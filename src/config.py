import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    devrev_api_token: str = os.getenv('DEVREV_API_TOKEN', '')
    devrev_base_url: str = os.getenv('DEVREV_BASE_URL', 'https://api.devrev.ai/internal/')
    environment: str = os.getenv('ENVIRONMENT', 'production')
