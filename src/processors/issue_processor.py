from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
import pandas as pd

from core.logging import ContextLogger
from core.cache import Cache
from core.circuit_breaker import CircuitBreaker
from core.validation import DataValidator
from models import Issue, UserGroup, ProcessingResult
from devrev_client import DevRevClient
from monitoring.metrics import MetricsCollector

@dataclass
class ProcessingStats:
    total_processed: int = 0
    successful_updates: int = 0
    failed_updates: int = 0
    skipped_updates: int = 0
    start_time: datetime = None
    end_time: datetime = None

    @property
    def duration_seconds(self) -> float:
        if not (self.start_time and self.end_time):
            return 0
        return (self.end_time - self.start_time).total_seconds()

class IssueProcessor:
    def __init__(
        self,
        devrev_client: DevRevClient,
        cache: Optional[Cache] = None,
        logger: Optional[ContextLogger] = None,
        metrics: Optional[MetricsCollector] = None,
        batch_size: int = 100
    ):
        self.client = devrev_client
        self.cache = cache or Cache()
        self.logger = logger or ContextLogger(__name__)
        self.metrics = metrics or MetricsCollector()
        self.validator = DataValidator()
        self.batch_size = batch_size
        self.stats = ProcessingStats()

    async def process_issues(
        self,
        issues: List[Issue],
        dry_run: bool = False
    ) -> ProcessingResult:
        """Process issues in batches with automatic retries and error handling"""
        self.stats.start_time = datetime.now()
        
        # First fetch all groups to build mapping
        groups = await self._fetch_groups()
        group_map = {g['id']: g for g in groups}
        
        # Process in batches
        for i in range(0, len(issues), self.batch_size):
            batch = issues[i:i + self.batch_size]
            await self._process_batch(batch, group_map, dry_run)
            
        self.stats.end_time = datetime.now()
        return self._build_result()

    @CircuitBreaker(failure_threshold=5)
    async def _fetch_groups(self) -> List[Dict]:
        """Fetch all groups with caching"""
        cached = self.cache.get('groups')
        if cached:
            return cached
            
        groups = await self.client.get_groups()
        self.cache.set('groups', groups)
        return groups

    async def _process_batch(
        self,
        batch: List[Issue],
        group_map: Dict,
        dry_run: bool
    ) -> None:
        """Process a batch of issues"""
        tasks = []
        for issue in batch:
            tasks.append(
                self._process_single_issue(issue, group_map, dry_run)
            )
            
        # Process concurrently but with rate limiting
        semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests
        async with semaphore:
            await asyncio.gather(*tasks)

    async def _process_single_issue(
        self,
        issue: Issue,
        group_map: Dict,
        dry_run: bool
    ) -> None:
        """Process a single issue with validation and error handling"""
        self.stats.total_processed += 1
        
        # Validate issue
        validation = self.validator.validate_issue(issue)
        if not validation.is_valid:
            self.logger.warning(
                f"Invalid issue: {validation.errors}",
                issue_id=issue.issue_id
            )
            self.stats.failed_updates += 1
            return

        try:
            # Get target group
            group = group_map.get(issue.creator_group)
            if not group:
                self.logger.warning(
                    "Group not found",
                    issue_id=issue.issue_id,
                    group_id=issue.creator_group
                )
                self.stats.failed_updates += 1
                return

            # Update the issue
            success = await self.client.update_issue_creator_group(
                issue.issue_id,
                group['id'],
                dry_run=dry_run
            )
            
            if success:
                self.stats.successful_updates += 1
                self.metrics.record_success()
            else:
                self.stats.failed_updates += 1
                self.metrics.record_failure()

        except Exception as e:
            self.logger.error(
                f"Error processing issue: {str(e)}",
                issue_id=issue.issue_id,
                exc_info=True
            )
            self.stats.failed_updates += 1
            self.metrics.record_failure()

    def _build_result(self) -> ProcessingResult:
        return ProcessingResult(
            total_processed=self.stats.total_processed,
            successful_updates=self.stats.successful_updates,
            failed_updates=self.stats.failed_updates,
            skipped_updates=self.stats.skipped_updates
        )