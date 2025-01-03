# DevRev Creator Group Backfill

This project automates the process of backfilling missing creator group information in DevRev issues. It features robust error handling, monitoring, and supports multiple data sources.

## Features

- Multiple data source support (CSV, Snowflake)
- Batch processing with configurable sizes
- Robust error handling and retry mechanisms
- Real-time progress tracking and monitoring
- Dry run mode for testing
- Data validation and integrity checks
- Performance optimizations
- Health monitoring and metrics collection
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
│   │   └── health.py      # Health checks
│   ├── processing/        # Processing logic
│   │   ├── batch.py       # Batch processing
│   │   ├── progress.py    # Progress tracking
│   │   ├── integrity.py   # Data integrity
│   │   └── dry_run.py     # Dry run functionality
│   ├── monitoring/        # Monitoring components
│   │   ├── metrics.py     # Metrics collection
│   │   └── health_check.py# Health monitoring
│   ├── data_source.py     # Data source implementations
│   ├── devrev_client.py   # DevRev API client
│   └── main.py           # Main execution script
├── tests/                 # Test files
│   ├── test_core/        # Core functionality tests
│   ├── test_processing/  # Processing tests
│   └── test_monitoring/  # Monitoring tests
└── sample_data/          # Sample data files
```

## Prerequisites

- Python 3.9 or higher
- Virtual environment tool (venv)
- Access to DevRev API
- (Optional) Snowflake access

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd devrev-backfill
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Unix/macOS
# or
.\venv\Scripts\activate  # On Windows
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the root directory:
```env
# DevRev Configuration
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
```

## Usage

### Command Line Arguments

- `--source`: Choose data source ('csv' or 'snowflake', default: 'csv')
- `--batch-size`: Number of issues to process in each batch (default: 100)
- `--dry-run`: Run without making actual updates
- `--log-level`: Set logging level (DEBUG/INFO/WARNING/ERROR, default: INFO)

### Running the Script

1. Basic usage (CSV source):
```bash
python src/main.py
```

2. Using Snowflake as data source:
```bash
python src/main.py --source snowflake
```

3. Dry run mode with custom batch size:
```bash
python src/main.py --dry-run --batch-size 50
```

4. Debug level logging:
```bash
python src/main.py --log-level DEBUG
```

## Monitoring

### Metrics
The application collects various metrics:
- Processing progress and success rates
- API call statistics
- Processing duration
- Batch processing metrics

### Health Checks
Monitors the health of:
- DevRev API connection
- Data source connectivity
- Rate limits
- System resources

### Logging
- JSON-formatted structured logs
- Separate log files for different components
- Configurable log levels
- Context-aware logging with metadata

## Error Handling

The script handles various error scenarios:
- Network connectivity issues
- API rate limiting
- Authentication failures
- Data validation errors
- Processing failures
- Database connection issues

## Data Validation

Validates:
- Input data format and required fields
- User and group associations
- Update results integrity
- Data consistency

## Testing

1. Run all tests:
```bash
python -m pytest tests/
```

2. Run specific test suites:
```bash
python -m pytest tests/test_core/
python -m pytest tests/test_processing/
python -m pytest tests/test_monitoring/
```

## Development

To contribute:
1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Run the full test suite
5. Submit a pull request

## Best Practices

1. Always use `--dry-run` first
2. Start with small batch sizes
3. Monitor logs during execution
4. Backup data before updates
5. Use virtual environment
6. Regularly check health metrics

## Troubleshooting

1. Check logs for detailed error messages
2. Verify configuration in .env
3. Test connectivity to all services
4. Monitor system resources
5. Check rate limits

## Support

For issues or questions:
1. Check the logs
2. Review error messages
3. Verify configuration
4. Check system health
5. Open an issue in the repository