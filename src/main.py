import argparse
import logging
from datetime import datetime
from typing import List, Dict, Optional

from config import Config
from models import Issue, ProcessingResult
from core.logging import ContextLogger
from core.validation import DataValidator
from processing.batch import BatchProcessor
from processing.progress import ProgressTracker
from processing.integrity import DataIntegrityChecker
from processing.dry_run import DryRunProcessor
from monitoring.metrics import MetricsCollector
from monitoring.health_check import ServiceHealth
from data_source import CSVDataSource, SnowflakeDataSource
from devrev_client import DevRevClient

class BackfillProcessor:
    def __init__(
        self,
        config: Config,
        dry_run: bool = False,
        logger: Optional[ContextLogger] = None
    ):
        self.config = config
        self.dry_run = dry_run
        self.logger = logger or ContextLogger(__name__)
        
        # Initialize components
        self.metrics = MetricsCollector()
        self.health_checker = ServiceHealth(config, self.logger)
        self.data_validator = DataValidator()
        self.integrity_checker = DataIntegrityChecker(self.logger)
        self.dry_run_processor = DryRunProcessor(self.logger)
        
        # Initialize clients
        self.devrev_client = DevRevClient(config)
        
        # Initialize processors
        self.batch_processor = BatchProcessor(
            batch_size=config.batch_size,
            max_consecutive_failures=config.max_batch_failures,
            logger=self.logger
        )

    def initialize(self) -> bool:
        """Initialize and check health of all components"""
        self.logger.info("Starting initialization and health checks")
        
        # Check system health
        health_status = self.health_checker.check_all()
        if not health_status["overall"]:
            self.logger.error("Health checks failed", status=health_status)
            return False
            
        self.logger.info("All systems healthy", status=health_status)
        return True

    def process_issues(self, issues: List[Issue]) -> ProcessingResult:
        """Main processing logic"""
        self.metrics.record_process_start(len(issues))
        progress = ProgressTracker(len(issues), "Processing issues")

        try:
            # Get user group mapping
            user_ids = list({issue.creator_user_id for issue in issues})
            user_groups = self.devrev_client.get_user_groups(user_ids)
            user_group_map = {ug.user_id: ug.group_id for ug in user_groups}

            # Process in batches
            for batch_result in self.batch_processor.process_batch(
                issues,
                lambda batch: self._process_batch(batch, user_group_map)
            ):
                for item in batch_result.input_items:
                    if batch_result.success:
                        progress.update("success")
                        self.metrics.record_issue_processed(True)
                    else:
                        progress.update("failed")
                        self.metrics.record_issue_processed(False)

            # Final integrity check
            if not self.dry_run:
                integrity_result = self.integrity_checker.verify_updates(
                    issues,
                    self._fetch_updated_issues(issues)
                )
                if not integrity_result.passed:
                    self.logger.warning(
                        "Integrity check failed",
                        mismatches=integrity_result.mismatches
                    )

            return ProcessingResult(
                total_processed=len(issues),
                successful_updates=self.metrics.successful_updates,
                failed_updates=self.metrics.failed_updates,
                skipped_updates=0
            )

        finally:
            progress.close()
            final_metrics = self.metrics.get_current_metrics()
            self.logger.info("Processing completed", metrics=final_metrics)

    def _process_batch(
        self,
        batch: List[Issue],
        user_group_map: Dict[str, str]
    ) -> List[Issue]:
        """Process a single batch of issues"""
        processed_issues = []
        
        for issue in batch:
            # Validate issue
            validation_result = self.data_validator.validate_issue(issue)
            if not validation_result.is_valid:
                self.logger.warning(
                    "Issue validation failed",
                    issue_id=issue.issue_id,
                    errors=validation_result.errors
                )
                continue

            # Get group ID
            group_id = user_group_map.get(issue.creator_user_id)
            if not group_id:
                self.logger.warning(
                    "No group found for user",
                    user_id=issue.creator_user_id
                )
                continue

            if self.dry_run:
                self.dry_run_processor.record_operation(
                    operation="update",
                    target=f"issue/{issue.issue_id}",
                    params={"creator_group": group_id}
                )
                processed_issues.append(issue)
            else:
                # Update issue
                try:
                    success = self.devrev_client.update_issue_creator_group(
                        issue.issue_id,
                        group_id
                    )
                    if success:
                        processed_issues.append(issue)
                        self.metrics.record_api_call()
                    else:
                        self.logger.error(
                            "Failed to update issue",
                            issue_id=issue.issue_id
                        )
                except Exception as e:
                    self.logger.error(
                        "Error updating issue",
                        issue_id=issue.issue_id,
                        error=str(e)
                    )

        return processed_issues

    def _fetch_updated_issues(self, original_issues: List[Issue]) -> List[Issue]:
        """Fetch the updated issues to verify changes"""
        # This would typically involve querying the DevRev API or database
        # to get the current state of the issues
        # For now, we'll just return the original issues
        return original_issues

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Backfill DevRev issue creator groups')
    parser.add_argument('--source', choices=['csv', 'snowflake'], default='csv',
                       help='Data source to use (default: csv)')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Number of issues to process in each batch (default: 100)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run without making any actual updates')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Set the logging level')
    args = parser.parse_args()

    try:
        # Load and validate configuration
        config = Config()
        config.batch_size = args.batch_size
        config.validate()

        # Setup logging
        logger = ContextLogger("backfill")
        logger.logger.setLevel(getattr(logging, args.log_level))

        # Initialize processor
        processor = BackfillProcessor(
            config=config,
            dry_run=args.dry_run,
            logger=logger
        )

        # Initialize system
        if not processor.initialize():
            logger.error("System initialization failed")
            return 1

        # Initialize data source
        if args.source == 'csv':
            data_source = CSVDataSource(config)
        else:
            data_source = SnowflakeDataSource(config)

        # Test data source connection
        if not data_source.test_connection():
            logger.error(f"Failed to connect to {args.source} data source")
            return 1

        # Get issues needing updates
        logger.info("Fetching issues with missing creator group...")
        issues = data_source.get_issues_missing_creator_group()
        logger.info(f"Found {len(issues)} issues to process")

        if not issues:
            logger.info("No issues found needing updates")
            return 0

        # Process issues
        if args.dry_run:
            logger.info("Running in DRY RUN mode - no actual updates will be made")

        result = processor.process_issues(issues)

        # Log final results
        logger.info("Processing completed!", result=str(result))
        
        if args.dry_run:
            dry_run_summary = processor.dry_run_processor.get_summary()
            logger.info("Dry run summary", summary=dry_run_summary)

        return 0 if result.failed_updates == 0 else 1

    except Exception as e:
        logger.error(f"Error in main process: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())