import pytest
from src.config import Config
from src.data_source import CSVDataSource, SnowflakeDataSource, DataSourceError

def test_csv_data_source():
    """Test CSV data source functionality"""
    # Create test configuration
    config = Config()
    config.csv_input_path = "sample_data/test_issues.csv"
    
    # Create sample CSV file for testing
    with open(config.csv_input_path, 'w') as f:
        f.write("issue_id,creator_user_id,assigned_group,creator_group\n")
        f.write("ISSUE-1,USER-1,GROUP-A,\n")  # Missing creator_group
        f.write("ISSUE-2,USER-2,GROUP-B,GROUP-C\n")  # Has creator_group
    
    # Initialize CSV data source
    csv_source = CSVDataSource(config)
    
    # Test connection
    assert csv_source.test_connection() is True
    
    # Test reading issues
    issues = csv_source.get_issues_missing_creator_group()
    assert len(issues) == 1  # Should only get the issue with missing creator_group
    assert issues[0].issue_id == "ISSUE-1"

def test_snowflake_data_source():
    """Test Snowflake data source functionality"""
    # Create test configuration
    config = Config()
    
    # Only run this test if Snowflake credentials are configured
    if not all([
        config.snowflake_account,
        config.snowflake_user,
        config.snowflake_password
    ]):
        pytest.skip("Snowflake credentials not configured")
    
    # Initialize Snowflake data source
    snowflake_source = SnowflakeDataSource(config)
    
    try:
        # Test connection
        assert snowflake_source.test_connection() is True
        
        # Test reading issues
        issues = snowflake_source.get_issues_missing_creator_group()
        assert isinstance(issues, list)
        
    except DataSourceError as e:
        pytest.fail(f"Snowflake test failed: {str(e)}")

if __name__ == "__main__":
    # Manual testing script
    from src.config import Config
    import logging
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize config
    config = Config()
    
    # Test CSV source
    print("\nTesting CSV Source:")
    csv_source = CSVDataSource(config)
    if csv_source.test_connection():
        print("CSV connection successful")
        issues = csv_source.get_issues_missing_creator_group()
        print(f"Found {len(issues)} issues with missing creator group in CSV")
    else:
        print("CSV connection failed")
    
    # Test Snowflake source if configured
    if config.snowflake_account:
        print("\nTesting Snowflake Source:")
        snowflake_source = SnowflakeDataSource(config)
        if snowflake_source.test_connection():
            print("Snowflake connection successful")
            issues = snowflake_source.get_issues_missing_creator_group()
            print(f"Found {len(issues)} issues with missing creator group in Snowflake")
        else:
            print("Snowflake connection failed")