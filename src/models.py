# src/models.py
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Issue:
    """Represents a DevRev issue/ticket with its properties"""
    issue_id: str
    creator_user_id: str
    assigned_group: str
    creator_group: Optional[str] = None

    def __str__(self) -> str:
        return f"Issue(id={self.issue_id}, creator={self.creator_user_id}, assigned_group={self.assigned_group})"

@dataclass
class UserGroup:
    """Represents a user-group association in DevRev"""
    user_id: str
    group_id: str
    group_name: Optional[str] = None

    def __str__(self) -> str:
        return f"UserGroup(user={self.user_id}, group={self.group_id})"

@dataclass
class ProcessingResult:
    """Tracks the results of batch processing operations"""
    total_processed: int = 0
    successful_updates: int = 0
    failed_updates: int = 0
    skipped_updates: int = 0
    
    def update_success(self) -> None:
        """Increment successful updates counter"""
        self.total_processed += 1
        self.successful_updates += 1
    
    def update_failure(self) -> None:
        """Increment failed updates counter"""
        self.total_processed += 1
        self.failed_updates += 1
    
    def update_skipped(self) -> None:
        """Increment skipped updates counter"""
        self.total_processed += 1
        self.skipped_updates += 1
    
    def __str__(self) -> str:
        return (
            f"Processing Results:\n"
            f"  Total Processed: {self.total_processed}\n"
            f"  Successful Updates: {self.successful_updates}\n"
            f"  Failed Updates: {self.failed_updates}\n"
            f"  Skipped Updates: {self.skipped_updates}\n"
            f"  Success Rate: {(self.successful_updates/self.total_processed)*100:.1f}% "
            f"(excluding skipped)" if self.total_processed > 0 else "No issues processed"
        )