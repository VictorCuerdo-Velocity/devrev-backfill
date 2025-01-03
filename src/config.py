# src/config.py
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class Config:
    # DevRev API Configuration
    devrev_api_token: str = os.getenv('DEVREV_API_TOKEN', '')
    devrev_base_url: str = os.getenv('DEVREV_BASE_URL', 'https://app.devrev.ai/api/gateway/internal/')
    environment: str = os.getenv('ENVIRONMENT', 'production')
    
    # Snowflake Configuration (optional)
    snowflake_account: Optional[str] = os.getenv('SNOWFLAKE_ACCOUNT', '')
    snowflake_user: Optional[str] = os.getenv('SNOWFLAKE_USER', '')
    snowflake_password: Optional[str] = os.getenv('SNOWFLAKE_PASSWORD', '')
    snowflake_warehouse: Optional[str] = os.getenv('SNOWFLAKE_WAREHOUSE', '')
    snowflake_database: Optional[str] = os.getenv('SNOWFLAKE_DATABASE', '')
    snowflake_schema: Optional[str] = os.getenv('SNOWFLAKE_SCHEMA', '')
    
    # CSV Configuration
    csv_input_path: Optional[str] = os.getenv('CSV_INPUT_PATH', 'input_data.csv')
    
    # Processing Configuration
    batch_size: int = int(os.getenv('BATCH_SIZE', '100'))
    
    def validate(self) -> bool:
        """Validate required configuration"""
        if not self.devrev_api_token:
            raise ValueError("DevRev API token is required")
        if not self.devrev_base_url:
            raise ValueError("DevRev base URL is required")
        return True