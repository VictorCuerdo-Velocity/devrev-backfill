from dataclasses import dataclass
from typing import List, Optional
from models import Issue

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]

class DataValidator:
    def validate_issue(self, issue: Issue) -> ValidationResult:
        errors = []
        
        if not issue.issue_id:
            errors.append("Issue ID is required")
        elif not isinstance(issue.issue_id, str):
            errors.append("Issue ID must be a string")
            
        if not issue.creator_user_id:
            errors.append("Creator user ID is required")
        elif not isinstance(issue.creator_user_id, str):
            errors.append("Creator user ID must be a string")
            
        if not issue.assigned_group:
            errors.append("Assigned group is required")
        elif not isinstance(issue.assigned_group, str):
            errors.append("Assigned group must be a string")
            
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )