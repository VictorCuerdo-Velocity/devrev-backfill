# src/devrev_client.py
import logging
import requests
from typing import List, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from models import UserGroup
from config import Config

class DevRevAPIError(Exception):
    """Base exception for DevRev API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)

class RateLimitError(DevRevAPIError):
    """Raised when hitting API rate limits"""
    pass

class AuthenticationError(DevRevAPIError):
    """Raised when authentication fails"""
    pass

class DevRevClient:
    """Client for interacting with the DevRev API"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {config.devrev_api_token}',
            'Content-Type': 'application/json'
        })

    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make a request to the DevRev API with error handling"""
        url = f"{self.config.devrev_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Handle specific error cases
            if response.status_code == 429:
                raise RateLimitError("API rate limit exceeded", response.status_code, response.text)
            elif response.status_code == 401:
                raise AuthenticationError("Authentication failed", response.status_code, response.text)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            self.logger.error(f"API request failed: {error_msg}")
            raise DevRevAPIError(error_msg, e.response.status_code, e.response.text)
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {str(e)}")
            raise DevRevAPIError(f"Request failed: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(RateLimitError)
    )
    def get_user_groups(self, user_ids: List[str]) -> List[UserGroup]:
        """Fetch group memberships for given users from DevRev API"""
        if not user_ids:
            return []
            
        self.logger.info(f"Fetching group information for {len(user_ids)} users")
        
        try:
            # DevRev API endpoint for fetching user information
            response = self._make_request(
                'POST',
                'users.list',
                json={'ids': user_ids}
            )
            
            user_groups = []
            for user in response.get('users', []):
                # Get the primary group for the user
                group_refs = user.get('group_refs', [])
                if group_refs:
                    user_groups.append(UserGroup(
                        user_id=user['id'],
                        group_id=group_refs[0],  # Using first group as primary
                        group_name=None  # Can be populated if needed
                    ))
                else:
                    self.logger.warning(f"No group found for user {user['id']}")
            
            self.logger.info(f"Successfully fetched groups for {len(user_groups)} users")
            return user_groups
            
        except DevRevAPIError as e:
            self.logger.error(f"Error fetching user groups: {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(RateLimitError)
    )
    def update_issue_creator_group(self, issue_id: str, group_id: str) -> bool:
        """Update an issue's creator group via DevRev API"""
        try:
            self._make_request(
                'POST',
                'works.update',
                json={
                    'id': issue_id,
                    'creator_group': {
                        'id': group_id
                    }
                }
            )
            self.logger.info(f"Successfully updated creator group for issue {issue_id}")
            return True
            
        except DevRevAPIError as e:
            if e.status_code == 404:
                self.logger.error(f"Issue {issue_id} not found")
            elif e.status_code == 403:
                self.logger.error(f"Permission denied updating issue {issue_id}")
            else:
                self.logger.error(f"Error updating issue {issue_id}: {str(e)}")
            return False

    def test_connection(self) -> bool:
        """Test the API connection and credentials"""
        try:
            # Test connection by getting current user info
            self._make_request('GET', 'users.self')
            self.logger.info("Successfully connected to DevRev API")
            return True
            
        except AuthenticationError:
            self.logger.error("Authentication failed - please check your API token")
            return False
        except DevRevAPIError as e:
            self.logger.error(f"DevRev API connection test failed: {str(e)}")
            return False

    def batch_update_issues(self, updates: List[Dict[str, str]], batch_size: int = 100) -> None:
        """Update issues in batches to avoid rate limiting"""
        total_updates = len(updates)
        self.logger.info(f"Starting batch update of {total_updates} issues")
        
        for i in range(0, total_updates, batch_size):
            batch = updates[i:i + batch_size]
            self.logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} issues)")
            
            for update in batch:
                self.update_issue_creator_group(update['issue_id'], update['group_id'])