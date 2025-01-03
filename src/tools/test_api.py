import asyncio
import os
import sys
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Direct imports from src
from core.logging import ContextLogger
from monitoring.health_check import HealthChecker
from devrev_client import DevRevClient
from metrics.prometheus import PrometheusMetrics
from config import Config

async def test_api_connectivity():
    config = Config()
    logger = ContextLogger("api-test")
    client = DevRevClient(config)
    health_checker = HealthChecker(config, logger)
    
    # Health check
    health = await health_checker.check_all()
    logger.info("Health check results:", status=health)
    
    # Test API
    try:
        await client.test_connection()
        groups = await client.get_groups()
        logger.info(f"Retrieved {len(groups)} groups")
    except Exception as e:
        logger.error(f"API test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_api_connectivity())