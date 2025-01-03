import pytest
from src.config import Config
from src.data_source import CSVDataSource, SnowflakeDataSource, DataSourceError

def test_csv_data_source():
    """Test CSV data source functionality"""

    config = Config()
    config.csv_input_path = "sample_data/test_issues.csv"
    

    with open(config.csv_input_path, 'w') as f:
        f.write("issue_id,creator_user_id,assigned_group,creator_group\n")
        f.write("ISSUE-1,USER-1,GROUP-A,\n")  # Missing creator_group
        f.write("ISSUE-2,USER-2,GROUP-B,GROUP-C\n")  # Has creator_group
    
    
    csv_source = CSVDataSource(config)
    

    assert csv_source.test_connection() is True
    
    
    issues = csv_source.get_issues_missing_creator_group()
    assert len(issues) == 1  # Should only get the issue with missing creator_group
    assert issues[0].issue_id == "ISSUE-1"

def test_snowflake_data_source():
    """Test Snowflake data source functionality"""
    
    config = Config()
    
    
    if not all([
        config.snowflake_account,
        config.snowflake_user,
        config.snowflake_password
    ]):
        pytest.skip("Snowflake credentials not configured")
    
    
    snowflake_source = SnowflakeDataSource(config)
    
    try:
    
        assert snowflake_source.test_connection() is True
        
    
        issues = snowflake_source.get_issues_missing_creator_group()
        assert isinstance(issues, list)
        
    except DataSourceError as e:
        pytest.fail(f"Snowflake test failed: {str(e)}")

if __name__ == "__main__":

    from src.config import Config
    import logging
    
    
    logging.basicConfig(level=logging.INFO)
    

    config = Config()
    

    print("\nTesting CSV Source:")
    csv_source = CSVDataSource(config)
    if csv_source.test_connection():
        print("CSV connection successful")
        issues = csv_source.get_issues_missing_creator_group()
        print(f"Found {len(issues)} issues with missing creator group in CSV")
    else:
        print("CSV connection failed")
    

    if config.snowflake_account:
        print("\nTesting Snowflake Source:")
        snowflake_source = SnowflakeDataSource(config)
        if snowflake_source.test_connection():
            print("Snowflake connection successful")
            issues = snowflake_source.get_issues_missing_creator_group()
            print(f"Found {len(issues)} issues with missing creator group in Snowflake")
        else:
            print("Snowflake connection failed")