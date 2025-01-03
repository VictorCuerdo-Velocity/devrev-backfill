# src/main.py
import logging
import argparse
from typing import List, Dict
from datetime import datetime
from config import Config
from models import Issue, ProcessingResult
from data_source import CSVDataSource, SnowflakeDataSource, DataSourceError
from devrev_client import DevRevClient, DevRevAPIError

def setup_logging(config: Config) -> None:
    """Configure logging for the application"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"backfill_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )

def create_user_group_mapping(devrev_client: DevRevClient, issues: List[Issue]) -> Dict[str, str]:
    """Create a mapping of user IDs to their primary group IDs"""
    # Get unique user IDs
    user_ids = list({issue.creator_user_id for issue in issues})
    logging.info(f"Fetching group information for {len(user_ids)} unique users")
    
    # Get user-group associations from DevRev
    user_groups = devrev_client.get_user_groups(user_ids)
    
    # Create mapping
    return {ug.user_id: ug.group_id for ug in user_groups}

def process_issues(issues: List[Issue], 
                  user_group_map: Dict[str, str], 
                  devrev_client: DevRevClient, 
                  batch_size: int) -> ProcessingResult:
    """Process issues in batches and update their creator groups"""
    result = ProcessingResult()
    total = len(issues)
    
    for i in range(0, total, batch_size):
        batch = issues[i:i + batch_size]
        logging.info(f"Processing batch {i//batch_size + 1} of {(total + batch_size - 1)//batch_size}")
        
        for issue in batch:
            try:
                group_id = user_group_map.get(issue.creator_user_id)
                if not group_id:
                    logging.warning(f"No group found for user {issue.creator_user_id}")
                    result.update_skipped()
                    continue
                
                if devrev_client.update_issue_creator_group(issue.issue_id, group_id):
                    result.update_success()
                else:
                    result.update_failure()
                    
            except Exception as e:
                logging.error(f"Error processing issue {issue.issue_id}: {str(e)}")
                result.update_failure()
        
        logging.info(f"Batch progress: {result}")
    
    return result

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Backfill DevRev issue creator groups')
    parser.add_argument('--source', choices=['csv', 'snowflake'], default='csv',
                       help='Data source to use (default: csv)')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Number of issues to process in each batch (default: 100)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run without making any actual updates')
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = Config()
        
        # Setup logging
        setup_logging(config)
        logging.info(f"Starting backfill process with source: {args.source}")
        
        if args.dry_run:
            logging.info("DRY RUN MODE - No updates will be made")
        
        # Initialize DevRev client
        devrev_client = DevRevClient(config)
        
        # Test DevRev connection
        if not devrev_client.test_connection():
            raise Exception("Failed to connect to DevRev API")
        
        # Initialize data source
        if args.source == 'csv':
            data_source = CSVDataSource(config)
        else:
            data_source = SnowflakeDataSource(config)
        
        # Test data source connection
        if not data_source.test_connection():
            raise Exception(f"Failed to connect to {args.source} data source")
        
        # Get issues needing updates
        logging.info("Fetching issues with missing creator group...")
        issues = data_source.get_issues_missing_creator_group()
        logging.info(f"Found {len(issues)} issues to process")
        
        if not issues:
            logging.info("No issues found needing updates")
            return
        
        # Create user-group mapping
        user_group_map = create_user_group_mapping(devrev_client, issues)
        
        if args.dry_run:
            # In dry run mode, just log what would be updated
            for issue in issues:
                group_id = user_group_map.get(issue.creator_user_id)
                if group_id:
                    logging.info(f"Would update issue {issue.issue_id} with creator group {group_id}")
                else:
                    logging.warning(f"No group found for user {issue.creator_user_id}")
            return
        
        # Process issues
        result = process_issues(issues, user_group_map, devrev_client, args.batch_size)
        
        # Log final results
        logging.info("Processing completed!")
        logging.info(str(result))
        
    except Exception as e:
        logging.error(f"Error in main process: {str(e)}")
        raise

if __name__ == "__main__":
    main()