import sys
import os
# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import Config
from devrev_client import DevRevClient
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize config and client
config = Config()
client = DevRevClient(config)

# Test connection
if client.test_connection():
    print("Successfully connected to DevRev API")
else:
    print("Failed to connect to DevRev API")