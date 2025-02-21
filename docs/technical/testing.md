# Blackprint Trading Bot Testing Guide

## Overview
This document outlines the testing strategy and procedures for the Blackprint Trading Bot. The testing framework is designed to ensure reliability, functionality, and proper error handling of the bot's features.

## Test Framework

### Location
```
/tests/telegram_bot_tests/
├── test_runner.py      # Main test execution script
├── test_config.py      # Test configuration and scenarios
├── requirements.txt    # Test dependencies
└── README.md          # Testing documentation
```

### Setup Requirements
1. Python 3.8+
2. Telegram API credentials
3. Bot token and username
4. Test user account

### Environment Setup
1. Install dependencies:
```bash
cd tests/telegram_bot_tests
pip install -r requirements.txt
```

2. Create `.env` file with credentials:
```env
TELEGRAM_TEST_API_ID=your_api_id
TELEGRAM_TEST_API_HASH=your_api_hash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_TEST_PHONE=your_phone_number
TELEGRAM_BOT_USERNAME=@your_bot_username
```

## Test Coverage

### 1. Command Testing
- Basic commands (/start, /help)
- Analysis commands (/analyze)
- Historical data retrieval
- Candle timeframe settings
- Index management
- Subscription handling

### 2. Error Handling
- Invalid symbols
- Malformed input
- Missing parameters
- Rate limiting
- Connection issues

### 3. Market Phase Testing
- Phase detection
- Notification system
- Subscription management
- Phase transitions

### 4. Data Validation
- Symbol validation
- Date range checks
- Timeframe validation
- Parameter formatting

## Running Tests

### Full Test Suite
```bash
python test_runner.py
```

### Test Output
1. Console Output
   - Real-time test progress
   - Pass/Fail indicators
   - Error messages

2. Log File (`telegram_bot_tests.log`)
   - Detailed execution log
   - Error tracing
   - Debug information

3. Test Reports
   - JSON report (`test_report_TIMESTAMP.json`)
   - Human-readable summary (`test_summary_TIMESTAMP.txt`)

## Test Reports

### JSON Report Structure
```json
{
    "summary": {
        "timestamp": "ISO-8601 timestamp",
        "total_tests": "number of tests",
        "passed_tests": "number of passed tests",
        "failed_tests": "number of failed tests",
        "success_rate": "percentage"
    },
    "results": [
        {
            "scenario": "test scenario name",
            "command": "executed command",
            "response": "bot response",
            "expected": "expected response",
            "passed": true/false,
            "timestamp": "ISO-8601 timestamp"
        }
    ],
    "errors": [
        {
            "command": "failed command",
            "error": "error message",
            "timestamp": "ISO-8601 timestamp"
        }
    ]
}
```

### Summary Report Content
- Test execution timestamp
- Overall statistics
- Scenario-based results
- Detailed error logs
- Response validation

## Adding New Tests

### Test Scenario Structure
```python
{
    'name': 'Test Scenario Name',
    'commands': [
        '/command1 param1',
        '/command2 param2'
    ],
    'expected_responses': [
        'expected response 1',
        'expected response 2'
    ]
}
```

### Steps to Add Tests
1. Add scenario to `test_config.py`
2. Define commands and expected responses
3. Add any necessary validation logic
4. Update documentation

## Best Practices

### 1. Test Independence
- Each test should be self-contained
- Clean up after tests
- Don't rely on previous test state

### 2. Error Handling
- Test both success and failure cases
- Validate error messages
- Check edge cases

### 3. Response Validation
- Use precise expected responses
- Handle variable content
- Check response timing

### 4. Documentation
- Document new test scenarios
- Update test coverage
- Note any special requirements

## Troubleshooting

### Common Issues
1. Connection Problems
   - Check API credentials
   - Verify network connection
   - Check bot status

2. Authentication Errors
   - Verify API ID and Hash
   - Check bot token
   - Confirm user permissions

3. Rate Limiting
   - Add delays between tests
   - Handle rate limit responses
   - Implement backoff strategy

### Debug Mode
Enable detailed logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Future Improvements

### Planned Enhancements
1. Continuous Integration
   - GitHub Actions integration
   - Automated test runs
   - Pull request validation

2. Performance Testing
   - Response time metrics
   - Load testing
   - Stress testing

3. Coverage Expansion
   - Additional edge cases
   - New feature testing
   - Integration testing
