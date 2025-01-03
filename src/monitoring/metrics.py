from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from prometheus_client import Counter, Gauge, Histogram
from core.logging import ContextLogger

@dataclass
class MetricsCollector:
    start_time: datetime = field(default_factory=datetime.utcnow)
    total_issues: int = 0
    processed_issues: int = 0
    successful_updates: int = 0
    failed_updates: int = 0
    processing_time: float = 0.0
    api_calls: int = 0
    
    # Prometheus metrics
    issues_processed = Counter('issues_processed_total', 'Total number of issues processed')
    updates_success = Counter('updates_success_total', 'Total number of successful updates')
    updates_failed = Counter('updates_failed_total', 'Total number of failed updates')
    processing_duration = Histogram('processing_duration_seconds', 'Time spent processing issues')
    api_calls_total = Counter('api_calls_total', 'Total number of API calls made')
    active_batches = Gauge('active_batches', 'Number of currently processing batches')

    def __post_init__(self):
        self.logger = ContextLogger(__name__)

    def record_process_start(self, total_issues: int) -> None:
        self.total_issues = total_issues
        self.start_time = datetime.utcnow()
        self.logger.info("Processing started", total_issues=total_issues)

    def record_issue_processed(self, success: bool) -> None:
        self.processed_issues += 1
        self.issues_processed.inc()
        
        if success:
            self.successful_updates += 1
            self.updates_success.inc()
        else:
            self.failed_updates += 1
            self.updates_failed.inc()

    def record_api_call(self) -> None:
        self.api_calls += 1
        self.api_calls_total.inc()

    def record_batch_start(self) -> None:
        self.active_batches.inc()

    def record_batch_complete(self) -> None:
        self.active_batches.dec()

    def get_current_metrics(self) -> Dict[str, Any]:
        current_time = datetime.utcnow()
        processing_time = (current_time - self.start_time).total_seconds()
        
        return {
            "timestamp": current_time.isoformat(),
            "total_issues": self.total_issues,
            "processed_issues": self.processed_issues,
            "successful_updates": self.successful_updates,
            "failed_updates": self.failed_updates,
            "success_rate": f"{(self.successful_updates/self.processed_issues)*100:.2f}%" if self.processed_issues > 0 else "0%",
            "processing_time": f"{processing_time:.2f}s",
            "api_calls": self.api_calls,
            "average_processing_time": f"{processing_time/self.processed_issues:.2f}s" if self.processed_issues > 0 else "0s"
        }