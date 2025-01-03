# DevRev Creator Group Backfill

This project automates the process of backfilling missing creator group information in DevRev issues. It can read issue data from either CSV files or Snowflake database and update the issues via the DevRev API.

## Project Structure
```
devrev-backfill/
├── .env                 # Environment variables and configurations
├── .gitignore          # Git ignore file
├── src/                # Source code
│   ├── __init__.py
│   ├── config.py       # Configuration management
│   ├── models.py       # Data models
│   ├── data_source.py  # Data source implementations
│   ├── devrev_client.py# DevRev API client
│   └── main.py         # Main execution script
├── tests/              # Test files
│   ├── __init__.py
│   └── test_devrev_connection.py
└── sample_data/        # Sample data files
    └── issues.csv      # Sample CSV file
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
```

3. Install required packages:
```bash
pip3 install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the root directory with your credentials:
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
```

2. For CSV input, ensure your CSV file has the following columns:
- issue_id
- creator_user_id
- assigned_group
- creator_group (optional)

## Usage

### Running the Script

1. Basic usage (CSV source):
```bash
python3 src/main.py
```

2. Using Snowflake as data source:
```bash
python3 src/main.py --source snowflake
```

3. Customize batch size:
```bash
python3 src/main.py --batch-size 50
```

4. Dry run mode (test without making updates):
```bash
python3 src/main.py --dry-run
```

### Command Line Arguments

- `--source`: Choose data source ('csv' or 'snowflake', default: 'csv')
- `--batch-size`: Number of issues to process in each batch (default: 100)
- `--dry-run`: Run without making actual updates

## Testing

1. Test DevRev API connection:
```bash
python3 tests/test_devrev_connection.py
```

2. Run all tests:
```bash
python3 -m pytest tests/
```

## Logging

- Logs are created in the root directory with timestamp: `backfill_YYYYMMDD_HHMMSS.log`
- Includes both console output and file logging
- Log level is set to INFO by default

## Error Handling

The script handles various error scenarios:
- DevRev API connection issues
- Rate limiting
- Authentication failures
- Data source connection problems
- Invalid data formats
- Missing or malformed fields

## CSV File Format

Example CSV format:
```csv
issue_id,creator_user_id,assigned_group,creator_group
ISSUE-123,USER-456,GROUP-789,
ISSUE-124,USER-457,GROUP-790,
ISSUE-125,USER-458,GROUP-791,null
```

## Snowflake Setup

If using Snowflake, ensure:
1. You have the necessary permissions
2. The issues table exists with required columns
3. Your Snowflake credentials are correctly configured in .env

## Troubleshooting

1. If you get "command not found: python":
```bash
brew install python3  # On macOS
```

2. If virtual environment fails to activate:
```bash
# Make sure you're in the project root directory
pwd
# Should show: /path/to/devrev-backfill
```

3. For permission issues:
```bash
chmod +x src/main.py
```

4. For SSL certificate issues:
```bash
pip3 install certifi
```

## Development

To contribute:
1. Fork the repository
2. Create a new branch
3. Make your changes
4. Run tests
5. Submit a pull request

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Verify your configuration in .env
3. Ensure all prerequisites are installed
4. Open an issue in the repository

## Best Practices

1. Always use `--dry-run` first to verify changes
2. Start with a small batch size for testing
3. Monitor the logs during execution
4. Backup data before running updates
5. Use virtual environment to manage dependencies