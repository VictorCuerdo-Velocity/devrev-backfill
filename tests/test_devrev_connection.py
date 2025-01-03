#!/usr/bin/env python3

import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
import requests

# Add the src directory to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def decode_jwt(token):
    """Basic JWT decoder to show token information"""
    try:
        payload = token.split('.')[1]
        payload += '=' * (-len(payload) % 4)
        import base64
        decoded = base64.b64decode(payload).decode('utf-8')
        return json.loads(decoded)
    except Exception as e:
        logger.error(f"Error decoding JWT: {str(e)}")
        return None

def test_endpoint(url: str, method: str, headers: dict, json_data: dict = None) -> tuple:
    """Generic endpoint test function"""
    try:
        start_time = datetime.now()
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        else:  # POST
            response = requests.post(url, headers=headers, json=json_data, timeout=10)
        
        response.raise_for_status()
        
        # Calculate request duration
        duration = (datetime.now() - start_time).total_seconds()
        
        # Extract rate limits
        rate_limits = {
            'limit': response.headers.get('x-ratelimit-limit'),
            'remaining': response.headers.get('x-ratelimit-remaining'),
            'reset': response.headers.get('x-ratelimit-reset')
        }
        
        return True, response.json(), rate_limits, duration
    except requests.exceptions.RequestException as e:
        error_msg = f"Error testing {url}: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f"\nStatus code: {e.response.status_code}"
            error_msg += f"\nResponse: {e.response.text}"
        logger.error(error_msg)
        return False, None, None, 0

def test_devrev_connection():
    """Test connection to DevRev API with detailed output"""
    
    # Load environment variables
    load_dotenv()
    
    api_token = os.getenv('DEVREV_API_TOKEN')
    base_url = os.getenv('DEVREV_BASE_URL', 'https://api.devrev.ai/internal/')
    environment = os.getenv('ENVIRONMENT', 'production')

    if not api_token:
        logger.error("❌ DEVREV_API_TOKEN not found in environment variables")
        return False

    # Analyze token
    logger.info("\n=== Token Analysis ===")
    token_info = decode_jwt(api_token)
    if token_info:
        exp_timestamp = token_info.get('exp', 0)
        exp_date = datetime.fromtimestamp(exp_timestamp)
        now = datetime.now()
        
        logger.info(f"Token issued for: {token_info.get('http://devrev.ai/fullname', 'Unknown')}")
        logger.info(f"Email: {token_info.get('http://devrev.ai/email', 'Unknown')}")
        logger.info(f"Organization ID: {token_info.get('org_id', 'Unknown')}")
        logger.info(f"Environment: {environment}")
        logger.info(f"Token expires: {exp_date}")
        
        if exp_date < now:
            logger.error("❌ Token has expired!")
            return False
        else:
            logger.info(f"✅ Token is valid for {(exp_date - now).days} more days")

    # Common headers
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    start_time = datetime.now()
    total_duration = 0
    logger.info("\n=== Initial Setup ===")
    
    # Get first work item ID for timeline testing
    works_url = f"{base_url}works.list"
    logger.info(f"Fetching work item for timeline testing: {works_url}")
    success, response, limits, duration = test_endpoint(
        works_url, 
        'POST', 
        headers,
        {"limit": 1, "type": ["issue"]}
    )
    total_duration += duration
    
    work_id = None
    if success and response.get('works'):
        work_id = response['works'][0]['id']
        logger.info(f"✅ Successfully retrieved work ID: {work_id}")
        logger.info(f"   Request took: {duration:.2f}s")
    else:
        logger.error("❌ Could not get work ID for timeline testing")
        return False

    # Test suite
    logger.info("\n=== Testing API Endpoints ===")

    test_endpoints = [
        {
            'name': 'Works List',
            'url': f"{base_url}works.list",
            'method': 'POST',
            'data': {
                "limit": 1,
                "type": ["issue"]
            }
        },
        {
            'name': 'Works Count',
            'url': f"{base_url}works.count",
            'method': 'POST',
            'data': {
                "type": ["issue"],
                "created_date": {
                    "preset_type": "last_n_days",
                    "type": "preset",
                    "days": 90
                }
            }
        },
        {
            'name': 'Timeline Entries List',
            'url': f"{base_url}timeline-entries.list",
            'method': 'POST',
            'data': {
                "limit": 1,
                "object": work_id  # Required parameter
            }
        },
        {
            'name': 'Dev Users List',
            'url': f"{base_url}dev-users.list",
            'method': 'POST',
            'data': {
                "limit": 1
            }
        },
        {
            'name': 'Tags List',
            'url': f"{base_url}tags.list",
            'method': 'POST',
            'data': {
                "limit": 10
            }
        }
    ]

    logger.info("\n=== Testing API Endpoints ===")
    all_tests_passed = True
    rate_limits = {'limit': None, 'remaining': None, 'reset': None}

    test_results = []
    
    for test in test_endpoints:
        logger.info(f"\nTesting {test['name']} endpoint: {test['url']}")
        success, response, current_limits, duration = test_endpoint(
            test['url'], test['method'], headers, test['data']
        )
        total_duration += duration
        
        test_results.append({
            'name': test['name'],
            'success': success,
            'duration': duration
        })
        
        if success:
            logger.info(f"✅ {test['name']} endpoint verified")
            logger.info(f"   Request took: {duration:.2f}s")
            if current_limits and current_limits['limit']:
                rate_limits = current_limits
        else:
            logger.error(f"❌ {test['name']} endpoint failed")
        
    # Summary
    logger.info("\n=== Connection Summary ===")
    logger.info(f"✅ Environment: {environment}")
    logger.info(f"✅ Base URL: {base_url}")
    
    all_tests_passed = all(result['success'] for result in test_results)
    if all_tests_passed:
        logger.info("✅ All API endpoints tested successfully")
    else:
        logger.error("❌ Some API endpoints failed")

    # Performance Summary
    logger.info("\n=== Performance Summary ===")
    logger.info(f"Total test duration: {total_duration:.2f}s")
    logger.info("Individual endpoint performance:")
    for result in test_results:
        logger.info(f"  • {result['name']}: {result['duration']:.2f}s")
    
    # Rate Limits
    logger.info("\n=== Rate Limits ===")
    logger.info(f"Rate Limit: {rate_limits['limit']}")
    logger.info(f"Remaining: {rate_limits['remaining']}")
    logger.info(f"Reset: {rate_limits['reset']}")
        
    return all_tests_passed

if __name__ == "__main__":
    print("\n🔍 Starting DevRev API Connection Test...\n")
    success = test_devrev_connection()
    print("\n" + "="*50 + "\n")
    if success:
        print("✅ Overall Result: Connection test PASSED")
        exit(0)
    else:
        print("❌ Overall Result: Connection test FAILED")
        exit(1)