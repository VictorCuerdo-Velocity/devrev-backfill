import asyncio
import argparse
from typing import Optional
import logging

from config import Config
from core.logging import ContextLogger
from devrev_client import DevRevClient
from processors.issue_processor import IssueProcessor
from data_loader import DataLoader
from monitoring.metrics import MetricsCollector
from monitoring.health_check import ServiceHealth

async def main():
    parser = argparse.ArgumentParser(description='Backfill DevRev issue creator groups')
    parser.add_argument('--csv', required=True, help='Path to input CSV file')
    parser.add_argument('--batch-size', type=int, default=100,
                    help='Number of issues to process in each batch')
    parser.add_argument('--dry-run', action='store_true',
                    help='Run without making actual updates')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                    default='INFO', help='Set the logging level')
    args = parser.parse_args()

    # Setup logging
    logger = ContextLogger("backfill")
    logger.logger.setLevel(getattr(logging, args.log_level))

    try:
        # Initialize components
        config = Config()
        metrics = MetricsCollector()
        health_checker = ServiceHealth(config)
        devrev_client = DevRevClient(config, logger)
        loader = DataLoader(logger)
        
        # Check service health
        health = await health_checker.check_all()
        if not health['overall']:
            logger.error("Service health check failed", status=health)
            return 1
            
        # Load and validate data
        logger.info(f"Loading issues from {args.csv}")
        issues = loader.load_from_csv(args.csv)
        if not issues:
            logger.info("No issues found needing updates")
            return 0
            
        # Initialize processor
        processor = IssueProcessor(
            devrev_client=devrev_client,
            logger=logger,
            metrics=metrics,
            batch_size=args.batch_size
        )
        
        # Process issues
        logger.info(f"Processing {len(issues)} issues (dry_run={args.dry_run})")
        result = await processor.process_issues(issues, dry_run=args.dry_run)
        
        # Log results
        logger.info(
            "Processing completed",
            total=result.total_processed,
            successful=result.successful_updates,
            failed=result.failed_updates,
            skipped=result.skipped_updates
        )
        
        return 0 if result.failed_updates == 0 else 1

    except Exception as e:
        logger.error(f"Error in main process: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    asyncio.run(main())