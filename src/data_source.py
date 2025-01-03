import csv
import logging
from abc import ABC, abstractmethod
import snowflake.connector
from snowflake.connector.errors import ProgrammingError, DatabaseError
from typing import List, Optional
from models import Issue
from config import Config

class DataSourceError(Exception):
    """Base exception for data source errors"""
    pass

class ConnectionError(DataSourceError):
    """Raised when connection to data source fails"""
    pass

class QueryError(DataSourceError):
    """Raised when query execution fails"""
    pass

class DataSource(ABC):
    """Abstract base class for data sources"""
    
    @abstractmethod
    def get_issues_missing_creator_group(self) -> List[Issue]:
        """Retrieve issues that have missing creator group information"""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test the connection to the data source"""
        pass

class CSVDataSource(DataSource):
    """Handles reading issue data from CSV files"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def test_connection(self) -> bool:
        """Test if the CSV file is accessible and has the required format"""
        try:
            with open(self.config.csv_input_path, 'r') as f:
                reader = csv.DictReader(f)
                required_fields = {'issue_id', 'creator_user_id', 'assigned_group'}
                header_fields = set(reader.fieldnames or [])
                
                if not required_fields.issubset(header_fields):
                    missing_fields = required_fields - header_fields
                    self.logger.error(f"Missing required fields in CSV: {missing_fields}")
                    return False
                
                # Test read first row to verify data format
                try:
                    next(reader)
                except StopIteration:
                    self.logger.warning("CSV file is empty but format is valid")
                except csv.Error as e:
                    self.logger.error(f"CSV format error: {str(e)}")
                    return False
                    
                return True
                
        except FileNotFoundError:
            self.logger.error(f"CSV file not found: {self.config.csv_input_path}")
            return False
        except Exception as e:
            self.logger.error(f"Error testing CSV connection: {str(e)}")
            return False

    def get_issues_missing_creator_group(self) -> List[Issue]:
        """Read issues from CSV file where creator_group is missing"""
        try:
            issues = []
            with open(self.config.csv_input_path, 'r') as f:
                reader = csv.DictReader(f)
                row_num = 0
                
                for row in reader:
                    row_num += 1
                    try:
                        # Only include issues where creator_group is empty or null
                        creator_group = row.get('creator_group', '').strip()
                        if not creator_group or creator_group.lower() in ('null', 'none', ''):
                            issue = Issue(
                                issue_id=row['issue_id'].strip(),
                                creator_user_id=row['creator_user_id'].strip(),
                                assigned_group=row['assigned_group'].strip(),
                                creator_group=None
                            )
                            issues.append(issue)
                            
                    except KeyError as e:
                        self.logger.error(f"Missing required field in row {row_num}: {str(e)}")
                        continue
                    except Exception as e:
                        self.logger.error(f"Error processing row {row_num}: {str(e)}")
                        continue
            
            self.logger.info(f"Found {len(issues)} issues with missing creator group in CSV")
            return issues
            
        except Exception as e:
            raise DataSourceError(f"Error reading CSV file: {str(e)}")

class SnowflakeDataSource(DataSource):
    """Handles reading issue data from Snowflake"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._connection = None

    @property
    def connection(self):
        """Lazy connection to Snowflake"""
        if self._connection is None:
            try:
                self._connection = snowflake.connector.connect(
                    account=self.config.snowflake_account,
                    user=self.config.snowflake_user,
                    password=self.config.snowflake_password,
                    warehouse=self.config.snowflake_warehouse,
                    database=self.config.snowflake_database,
                    schema=self.config.snowflake_schema
                )
            except DatabaseError as e:
                raise ConnectionError(f"Failed to connect to Snowflake: {str(e)}")
        return self._connection

    def test_connection(self) -> bool:
        """Test Snowflake connection and required table access"""
        try:
            with self.connection.cursor() as cursor:
                # Test basic connection
                cursor.execute("SELECT CURRENT_VERSION()")
                version = cursor.fetchone()[0]
                self.logger.info(f"Connected to Snowflake version: {version}")
                
                # Test access to issues table
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM issues 
                    WHERE creator_group IS NULL 
                    LIMIT 1
                """)
                return True
                
        except Exception as e:
            self.logger.error(f"Snowflake connection test failed: {str(e)}")
            return False

    def get_issues_missing_creator_group(self) -> List[Issue]:
        """Query Snowflake for issues with missing creator group"""
        query = """
        SELECT 
            issue_id,
            creator_user_id,
            assigned_group,
            creator_group
        FROM issues 
        WHERE creator_group IS NULL
        ORDER BY issue_id
        """
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                
                issues = []
                for row in results:
                    try:
                        issue = Issue(
                            issue_id=str(row[0]),
                            creator_user_id=str(row[1]),
                            assigned_group=str(row[2]),
                            creator_group=row[3]
                        )
                        issues.append(issue)
                    except Exception as e:
                        self.logger.error(f"Error processing Snowflake row {row}: {str(e)}")
                        continue
                
                self.logger.info(f"Found {len(issues)} issues with missing creator group in Snowflake")
                return issues
                
        except ProgrammingError as e:
            raise QueryError(f"Snowflake query failed: {str(e)}")
        except Exception as e:
            raise DataSourceError(f"Error retrieving data from Snowflake: {str(e)}")

    def __del__(self):
        """Clean up Snowflake connection"""
        if self._connection:
            try:
                self._connection.close()
            except Exception as e:
                self.logger.error(f"Error closing Snowflake connection: {str(e)}")