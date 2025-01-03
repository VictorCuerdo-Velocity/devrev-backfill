# DevRev Creator Group Backfill

This project automates the process of backfilling missing creator group information in DevRev issues, featuring robust error handling, monitoring, and multiple data sources support.

## Features

- Multiple data source support (CSV, Snowflake)
- Batch processing with configurable sizes
- Comprehensive error handling and retry mechanisms
- Real-time progress tracking and monitoring
- Dry run mode for testing
- Data validation and integrity checks
- Health monitoring and metrics collection
- AsyncIO for improved performance
- Checkpoint system for resumable operations
- Automatic rate limiting and circuit breakers
- Alerting system (Email/Slack)
- System diagnostics and profiling
- Structured JSON logging
- Prometheus metrics integration

## Project Structure
```
devrev-backfill/
├── .env                    # Environment variables and configurations
├── .gitignore             # Git ignore file
├── src/                   # Source code
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── models.py          # Data models
│   ├── core/              # Core functionality
│   │   ├── logging.py     # Custom logging
│   │   ├── validation.py  # Data validation
│   │   ├── caching.py     # Caching mechanisms
│   │   ├── retry.py       # Retry logic
│   │   ├── circuit_breaker.py # Circuit breaker implementation
│   │   ├── rate_limiter.py    # Rate limiting logic
│   │   ├── bulk_processor.py  # Bulk processing with backpressure
│   │   └── checkpoint.py      # Checkpointing system
│   ├── processing/        # Processing logic
│   │   ├── batch.py       # Batch processing
│   │   ├── progress.py    # Progress tracking
│   │   ├── integrity.py   # Data integrity
│   │   └── dry_run.py     # Dry run functionality
│   ├── monitoring/        # Monitoring components
│   │   ├── metrics.py     # Metrics collection
│   │   ├── alerting.py    # Alert system
│   │   └── health_check.py# Health monitoring
│   ├── utils/             # Utility functions
│   │   ├── profiler.py    # Performance profiling
│   │   └── diagnostics.py # System diagnostics
│   ├── data_source.py     # Data source implementations
│   ├── devrev_client.py   # DevRev API client
│   └── main.py           # Main execution script
├── tests/                 # Test files
│   ├── test_core/        # Core functionality tests
│   ├── test_processing/  # Processing tests
│   └── test_monitoring/  # Monitoring tests
├── logs/                 # Log files directory
├── checkpoints/          # Checkpoint files
└── test_data/           # Test and sample data
```

## Prerequisites

- Python 3.9+
- Virtual environment tool (venv)
- DevRev API access
- (Optional) Snowflake access

## Quick Start

1. Clone and setup:
```bash
git clone <repository-url>
cd devrev-backfill
python3 -m venv venv
source venv/bin/activate  # Unix/macOS
# or .\venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. Configure environment:
```bash
# Copy sample .env
cp .env.sample .env
# Edit with your values
nano .env
```

3. Test your CSV:
```bash
# Create test directory
mkdir -p test_data
# Copy your CSV
cp your_file.csv test_data/input.csv
# Validate format
python src/tools/validate_csv.py test_data/input.csv
```

4. Safe testing process:
```bash
# Full dry run first
python src/main.py --csv test_data/input.csv --dry-run --log-level DEBUG

# Test small batch
python src/main.py --csv test_data/input.csv --batch-size 5 --dry-run

# Process sample in production
head -n 10 test_data/input.csv > test_data/sample.csv
python src/main.py --csv test_data/sample.csv --batch-size 5
```

## Configuration

`.env` file structure:
```env
# Required DevRev Configuration
ENVIRONMENT=production
DEVREV_API_TOKEN=your_token_here
DEVREV_BASE_URL=https://app.devrev.ai/api/gateway/internal/

# Optional: Snowflake Configuration
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema

# Processing Configuration
BATCH_SIZE=100
MAX_RETRIES=3
RETRY_BACKOFF=2
MAX_BATCH_FAILURES=5
CACHE_TTL=3600
RATE_LIMIT_CALLS=50
RATE_LIMIT_PERIOD=10

# Alerting Configuration
ALERT_EMAIL=your_email
SMTP_HOST=smtp.your-company.com
SLACK_WEBHOOK=your_webhook_url
```

## Command Line Options

```bash
python src/main.py [OPTIONS]

Options:
  --csv PATH               Path to input CSV file
  --source TEXT           Data source (csv/snowflake) [default: csv]
  --batch-size INTEGER    Batch size [default: 100]
  --dry-run              Run without making changes
  --resume               Resume from last checkpoint
  --log-level TEXT       Logging level [default: INFO]
  --validate-only        Only validate input data
  --profile              Enable performance profiling
  --monitor              Enable system monitoring
  --help                 Show this message and exit
```

## CSV Format Requirements

Required format:
```csv
issue_id,creator_user_id,assigned_group,creator_group
ISSUE-1,USER-1,GROUP-A,
ISSUE-2,USER-2,GROUP-B,
```

Validation rules:
- issue_id: Required, string
- creator_user_id: Required, string
- assigned_group: Required, string
- creator_group: Optional, string (empty for updates)

## Monitoring & Alerts

1. Real-time metrics:
```bash
# View current metrics
python src/tools/metrics.py

# Watch processing
python src/tools/monitor.py
```

2. Available metrics:
- Processing progress/rates
- API usage and limits
- Error rates and types
- System resource usage
- Processing durations

3. Health checks:
```bash
# Check system health
python src/tools/health_check.py

# Test API connection
python src/tools/test_connection.py
```

4. Alerts configuration:
```python
# config.py
ALERT_THRESHOLDS = {
    'error_rate': 0.1,     # Alert if >10% errors
    'processing_time': 60,  # Alert if batch takes >60s
    'api_errors': 5        # Alert after 5 API errors
}
```

## Error Recovery

If processing fails:

1. Check logs:
```bash
tail -f logs/processing.log
```

2. Review checkpoint:
```bash
python src/tools/show_checkpoint.py
```

3. Resume processing:
```bash
python src/main.py --csv input.csv --resume
```

## Troubleshooting

Common issues and solutions:

1. API Rate Limits:
- Reduce batch size
- Increase rate limit period
- Check current limits:
```bash
python src/tools/check_limits.py
```

2. Data Validation:
- Validate CSV format
- Check group mappings:
```bash
python src/tools/validate_groups.py
```

3. Performance Issues:
- Run profiler:
```bash
python src/main.py --profile
```
- Check system resources:
```bash
python src/tools/diagnostics.py
```

## Best Practices

1. Testing:
- Always run with --dry-run first
- Test with small batches initially
- Validate data before processing
- Monitor logs during execution

2. Production:
- Use checkpoints for large datasets
- Monitor system resources
- Keep data backups
- Set up alerts

3. Recovery:
- Use --resume for interruptions
- Check logs for errors
- Validate results after completion

## Support

For issues:
1. Check logs in `logs/`
2. Run health checks
3. Review error messages
4. Open GitHub issue with:
   - Error logs
   - Configuration (sanitized)
   - Steps to reproduce