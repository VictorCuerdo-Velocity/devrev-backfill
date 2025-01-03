from dataclasses import dataclass
from typing import List, Optional
from models import Issue, UserGroup

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str] = None

class DataValidator:
    def validate_issue(self, issue: Issue) -> ValidationResult:
        errors = []
        warnings = []
        
        if not issue.issue_id:
            errors.append("Issue ID is required")
        elif not isinstance(issue.issue_id, str):
            errors.append("Issue ID must be a string")
        
        if not issue.creator_user_id:
            errors.append("Creator user ID is required")
        
        if not issue.assigned_group:
            warnings.append("Assigned group is missing")
            
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def validate_group(self, group: Dict[str, Any]) -> ValidationResult:
        errors = []
        
        required_fields = ['id', 'name', 'type']
        for field in required_fields:
            if field not in group:
                errors.append(f"Missing required field: {field}")
                
        if group.get('type') not in ['static', 'dynamic']:
            errors.append("Invalid group type")
            
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )