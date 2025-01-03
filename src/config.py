import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

@dataclass
class Config:
    devrev_api_token: str = os.getenv('DEVREV_API_TOKEN', '')
    devrev_base_url: str = os.getenv('DEVREV_BASE_URL', 'https://api.devrev.ai/internal/')
    environment: str = os.getenv('ENVIRONMENT', 'production')
    batch_size: int = int(os.getenv('BATCH_SIZE', '100'))
    max_retries: int = int(os.getenv('MAX_RETRIES', '3'))
    retry_delay: int = int(os.getenv('RETRY_DELAY', '5'))
    timeout: int = int(os.getenv('TIMEOUT', '30'))
    cache_ttl: int = int(os.getenv('CACHE_TTL', '3600'))
    
    # Snowflake Configuration
    # snowflake_account: Optional[str] = os.getenv('SNOWFLAKE_ACCOUNT', '')
    # snowflake_user: Optional[str] = os.getenv('SNOWFLAKE_USER', '')
    # snowflake_password: Optional[str] = os.getenv('SNOWFLAKE_PASSWORD', '')
    # snowflake_warehouse: Optional[str] = os.getenv('SNOWFLAKE_WAREHOUSE', '')
    # snowflake_database: Optional[str] = os.getenv('SNOWFLAKE_DATABASE', '')
    # snowflake_schema: Optional[str] = os.getenv('SNOWFLAKE_SCHEMA', '')
    
    def validate(self) -> bool:
        if not self.devrev_api_token:
            raise ValueError("DevRev API token is required")
        if not self.devrev_base_url:
            raise ValueError("DevRev base URL is required")
        return True