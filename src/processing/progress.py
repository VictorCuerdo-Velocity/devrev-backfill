from dataclasses import dataclass, field
from typing import Dict, Any
from datetime import datetime
from tqdm import tqdm

@dataclass
class ProcessingMetrics:
    total: int = 0
    processed: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    start_time: datetime = field(default_factory=datetime.utcnow)

    @property
    def success_rate(self) -> float:
        if self.processed == 0:
            return 0.0
        return (self.successful / self.processed) * 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "processed": self.processed,
            "successful": self.successful,
            "failed": self.failed,
            "skipped": self.skipped,
            "success_rate": f"{self.success_rate:.2f}%",
            "duration": str(datetime.utcnow() - self.start_time)
        }

class ProgressTracker:
    def __init__(self, total: int, desc: str = "Processing"):
        self.progress_bar = tqdm(total=total, desc=desc)
        self.metrics = ProcessingMetrics(total=total)

    def update(self, status: str) -> None:
        self.metrics.processed += 1
        
        if status == "success":
            self.metrics.successful += 1
        elif status == "failed":
            self.metrics.failed += 1
        elif status == "skipped":
            self.metrics.skipped += 1
            
        self.progress_bar.update(1)
        self.progress_bar.set_postfix(self.metrics.to_dict())

    def close(self) -> None:
        self.progress_bar.close()