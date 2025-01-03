from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from models import Issue
from core.logging import ContextLogger

@dataclass
class IntegrityCheckResult:
    passed: bool
    mismatches: List[str]
    details: Dict[str, Any]

class DataIntegrityChecker:
    def __init__(self, logger: Optional[ContextLogger] = None):
        self.logger = logger or ContextLogger(__name__)

    def verify_updates(
        self,
        original_issues: List[Issue],
        updated_issues: List[Issue]
    ) -> IntegrityCheckResult:
        mismatches = []
        details = {
            "total_checked": len(original_issues),
            "matched": 0,
            "mismatched": 0
        }

        if len(original_issues) != len(updated_issues):
            mismatches.append(
                f"Count mismatch: {len(original_issues)} vs {len(updated_issues)}"
            )

        for orig, updated in zip(original_issues, updated_issues):
            if orig.issue_id != updated.issue_id:
                mismatches.append(
                    f"ID mismatch: {orig.issue_id} vs {updated.issue_id}"
                )
                details["mismatched"] += 1
            else:
                details["matched"] += 1

        passed = len(mismatches) == 0

        return IntegrityCheckResult(
            passed=passed,
            mismatches=mismatches,
            details=details
        )

    def verify_field_updates(
        self,
        original_issues: List[Issue],
        updated_issues: List[Issue],
        field_name: str
    ) -> IntegrityCheckResult:
        mismatches = []
        details = {
            "total_checked": len(original_issues),
            "field": field_name,
            "updates_verified": 0,
            "updates_failed": 0
        }

        for orig, updated in zip(original_issues, updated_issues):
            if getattr(orig, field_name) != getattr(updated, field_name):
                mismatches.append(
                    f"Field {field_name} mismatch for issue {orig.issue_id}: "
                    f"{getattr(orig, field_name)} vs {getattr(updated, field_name)}"
                )
                details["updates_failed"] += 1
            else:
                details["updates_verified"] += 1

        return IntegrityCheckResult(
            passed=len(mismatches) == 0,
            mismatches=mismatches,
            details=details
        )