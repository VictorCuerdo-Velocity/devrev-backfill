from prometheus_client import Counter, Gauge, Histogram
import time

class PrometheusMetrics:
    def __init__(self):
        # API metrics
        self.api_requests = Counter(
            'devrev_api_requests_total',
            'Total number of DevRev API requests',
            ['endpoint']
        )
        self.api_errors = Counter(
            'devrev_api_errors_total', 
            'Total number of DevRev API errors',
            ['endpoint', 'error_type']
        )
        
        # Processing metrics
        self.issues_processed = Counter(
            'issues_processed_total',
            'Total number of issues processed'
        )
        self.issues_updated = Counter(
            'issues_updated_total',
            'Total number of issues successfully updated'
        )
        self.issues_failed = Counter(
            'issues_failed_total',
            'Total number of issues that failed to update'
        )
        
        # Performance metrics  
        self.processing_duration = Histogram(
            'issue_processing_duration_seconds',
            'Time spent processing issues',
            buckets=[1, 5, 10, 30, 60, 120, 300, 600]
        )
        self.batch_size = Gauge(
            'current_batch_size',
            'Current processing batch size'
        )

    def record_api_request(self, endpoint: str) -> None:
        self.api_requests.labels(endpoint=endpoint).inc()

    def record_api_error(self, endpoint: str, error_type: str) -> None:
        self.api_errors.labels(
            endpoint=endpoint,
            error_type=error_type
        ).inc()

    def record_success(self) -> None:
        self.issues_processed.inc()
        self.issues_updated.inc()

    def record_failure(self) -> None:
        self.issues_processed.inc()
        self.issues_failed.inc()

    def record_batch_size(self, size: int) -> None:
        self.batch_size.set(size)

    def time_processing(self, start_time: float) -> None:
        duration = time.time() - start_time
        self.processing_duration.observe(duration)