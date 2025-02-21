# Telegram Bot Automated Testing

This directory contains automated testing tools for the Blackprint Telegram bot. The tests simulate user interactions and verify bot responses.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with the following variables:
```env
TELEGRAM_TEST_API_ID=your_api_id
TELEGRAM_TEST_API_HASH=your_api_hash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_TEST_PHONE=your_phone_number
TELEGRAM_BOT_USERNAME=@your_bot_username
```

To get the API ID and Hash:
1. Go to https://my.telegram.org
2. Log in with your phone number
3. Go to 'API Development Tools'
4. Create a new application

## Running Tests

Run all tests:
```bash
python test_runner.py
```

## Test Output

The test runner generates two types of output:

1. Real-time console logging:
   - Test progress
   - Passed/Failed status
   - Error messages

2. Test report file:
   - Generated after each test run
   - Named `test_report_TIMESTAMP.txt`
   - Contains detailed test results
   - Lists failed tests with expected vs actual responses

## Log Files

- `telegram_bot_tests.log`: Contains detailed logging information
- `test_report_*.txt`: Contains test results and error details

## Test Scenarios

The test suite includes scenarios for:
- Basic command responses
- Symbol analysis
- Historical data retrieval
- Timeframe settings
- Error handling
- Invalid inputs

## Adding New Tests

Add new test scenarios in `test_config.py`:

```python
TEST_SCENARIOS = [
    {
        'name': 'Your Test Name',
        'commands': ['command1', 'command2'],
        'expected_responses': ['expected1', 'expected2']
    }
]
```
