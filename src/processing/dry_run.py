from typing import List, Optional, Any
from dataclasses import dataclass
from core.logging import ContextLogger

@dataclass
class DryRunResult:
    operation: str
    target: str
    params: dict
    would_execute: bool
    notes: Optional[str] = None

class DryRunProcessor:
    def __init__(self, logger: Optional[ContextLogger] = None):
        self.logger = logger or ContextLogger(__name__)
        self.operations: List[DryRunResult] = []

    def record_operation(
        self,
        operation: str,
        target: str,
        params: dict,
        would_execute: bool = True,
        notes: Optional[str] = None
    ) -> None:
        result = DryRunResult(
            operation=operation,
            target=target,
            params=params,
            would_execute=would_execute,
            notes=notes
        )
        self.operations.append(result)
        self.logger.info(
            f"DRY RUN: Would {operation} {target}",
            params=params,
            would_execute=would_execute,
            notes=notes
        )

    def get_summary(self) -> dict:
        return {
            "total_operations": len(self.operations),
            "operations_by_type": self._group_by_operation_type(),
            "would_execute": len([op for op in self.operations if op.would_execute]),
            "would_skip": len([op for op in self.operations if not op.would_execute])
        }

    def _group_by_operation_type(self) -> dict:
        result = {}
        for op in self.operations:
            if op.operation not in result:
                result[op.operation] = 0
            result[op.operation] += 1
        return result