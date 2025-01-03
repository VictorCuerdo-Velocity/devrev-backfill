import logging
import aiohttp
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from models import UserGroup
from config import Config
from core.logging import ContextLogger
from core.circuit_breaker import CircuitBreaker
from core.cache import Cache
from core.validation import DataValidator
from metrics.prometheus import PrometheusMetrics

class DevRevAPIError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)

class RateLimitError(DevRevAPIError):
    pass

class AuthenticationError(DevRevAPIError):
    pass

class DevRevClient:
    def __init__(self, config: Config, logger: Optional[ContextLogger] = None):
        self.config = config
        self.logger = logger or ContextLogger(__name__)
        self.cache = Cache(ttl=3600)
        self.validator = DataValidator()
        self.metrics = PrometheusMetrics()
        self.headers = {
            "Authorization": f"Bearer {config.devrev_api_token}",
            "Content-Type": "application/json"
        }

    @CircuitBreaker(failure_threshold=5, reset_timeout=60)
    async def get_groups(self) -> List[Dict[str, Any]]:
        try:
            with self.metrics.api_latency.labels(endpoint='groups.list').time():
                self.metrics.record_api_request('groups.list')
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.config.devrev_base_url.rstrip('/')}/groups.list",
                        headers=self.headers,
                        params={
                            'group_type': 'static',
                            'member_type': 'dev_user'
                        }
                    ) as response:
                        if response.status == 429:
                            raise RateLimitError("API rate limit exceeded")
                        elif response.status == 401:
                            raise AuthenticationError("Authentication failed")
                            
                        data = await response.json()
                        return data.get('groups', [])
        except Exception as e:
            self.logger.error(f"Failed to fetch groups: {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(RateLimitError)
    )
    async def get_user_groups(self, user_ids: List[str]) -> List[UserGroup]:
        cache_key = f"user_groups_{','.join(sorted(user_ids))}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            with self.metrics.api_latency.labels(endpoint='users.list').time():
                self.metrics.record_api_request('users.list')
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.config.devrev_base_url.rstrip('/')}/users.list",
                        headers=self.headers,
                        json={'ids': user_ids}
                    ) as response:
                        data = await response.json()
                        groups = [
                            UserGroup(
                                user_id=user['id'],
                                group_id=user['group_refs'][0] if user.get('group_refs') else None
                            ) 
                            for user in data.get('users', [])
                        ]
                        self.cache.set(cache_key, groups)
                        return groups
        except Exception as e:
            self.metrics.record_api_error('users.list', type(e).__name__)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(RateLimitError)
    )
    async def update_issue_creator_group(self, issue_id: str, group_id: str, dry_run: bool = False) -> bool:
        if dry_run:
            self.logger.info(f"DRY RUN: Would update issue {issue_id} with creator_group {group_id}")
            return True

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config.devrev_base_url.rstrip('/')}/works.update",
                    headers=self.headers,
                    json={
                        'id': issue_id,
                        'creator_group': {'id': group_id}
                    }
                ) as response:
                    if response.status == 200:
                        self.logger.info(f"Successfully updated creator group for issue {issue_id}")
                        return True
                    elif response.status == 404:
                        self.logger.error(f"Issue {issue_id} not found")
                    elif response.status == 403:
                        self.logger.error(f"Permission denied updating issue {issue_id}")
                    else:
                        self.logger.error(f"Error updating issue {issue_id}: {response.status}")
                    return False
        except Exception as e:
            self.logger.error(f"Error updating issue {issue_id}: {str(e)}")
            return False

    async def batch_update_issues(self, updates: List[Dict[str, str]], batch_size: int = 100) -> None:
        total_updates = len(updates)
        self.logger.info(f"Starting batch update of {total_updates} issues")
        
        for i in range(0, total_updates, batch_size):
            batch = updates[i:i + batch_size]
            self.logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} issues)")
            
            for update in batch:
                await self.update_issue_creator_group(update['issue_id'], update['group_id'])

    async def test_connection(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config.devrev_base_url.rstrip('/')}/users.self",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        self.logger.info("Successfully connected to DevRev API")
                        return True
                    elif response.status == 401:
                        self.logger.error("Authentication failed - please check your API token")
                    else:
                        self.logger.error(f"DevRev API connection test failed: {response.status}")
                    return False
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False