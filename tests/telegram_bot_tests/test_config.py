"""Configuration for Telegram bot testing"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import random

load_dotenv()

# Telegram API credentials
API_ID = os.getenv('TELEGRAM_TEST_API_ID')
API_HASH = os.getenv('TELEGRAM_TEST_API_HASH')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TEST_PHONE = os.getenv('TELEGRAM_TEST_PHONE')

# Bot username to test against
BOT_USERNAME = os.getenv('TELEGRAM_BOT_USERNAME')

# Test data
TEST_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'INVALID_SYMBOL']
TEST_TIMEFRAMES = ['1Min', '5Min', '15Min', '1H', '4H', '1D', 'invalid_timeframe']
TEST_INDICES = ['SPY', 'QQQ', 'DIA', 'IWM', 'INVALID_INDEX']
MARKET_PHASES = ['accumulation', 'markup', 'distribution', 'markdown']

# Generate test dates
TODAY = datetime.now()
VALID_PAST_DATE = (TODAY - timedelta(days=7)).strftime('%Y-%m-%d')
OUTSIDE_WINDOW_DATE = (TODAY - timedelta(days=45)).strftime('%Y-%m-%d')
FUTURE_DATE = (TODAY + timedelta(days=1)).strftime('%Y-%m-%d')

# Random stock and date generator
def get_random_stock_and_date():
    stock = random.choice(TEST_SYMBOLS[:-1])  # Exclude invalid symbol
    days_ago = random.randint(1, 7)
    date = (TODAY - timedelta(days=days_ago)).strftime('%Y-%m-%d')
    return stock, date

# Test scenarios
TEST_SCENARIOS = [
    {
        'name': 'Help Command Test',
        'commands': ['/help', '/start'],
        'expected_responses': [
            'Available commands',
            'Welcome to Blackprint Trading Bot',
            '/analyze - Analyze a stock',
            '/historical - View historical data',
            '/setcandle - Set candle timeframe'
        ]
    },
    {
        'name': 'Index Change Tests',
        'commands': [
            '/setindex SPY',
            '/setindex QQQ',
            '/setindex INVALID_INDEX',
            '/getindex'
        ],
        'expected_responses': [
            'Index set to SPY',
            'Index set to QQQ',
            'Invalid index symbol',
            'Current index:'
        ]
    },
    {
        'name': 'Stock Analysis Tests',
        'commands': [
            '/analyze AAPL',
            '/analyze GOOGL',
            '/analyze INVALID_SYMBOL',
            '/analyze'  # Missing symbol
        ],
        'expected_responses': [
            'Analysis for AAPL',
            'Analysis for GOOGL',
            'Invalid symbol',
            'Please provide a valid stock symbol'
        ]
    },
    {
        'name': 'Market Phase Notification Tests',
        'commands': [
            '/subscribe AAPL accumulation',
            '/subscribe AAPL markup',
            '/subscribe AAPL distribution',
            '/subscribe AAPL markdown',
            '/subscribe INVALID_SYMBOL accumulation',
            '/subscribe AAPL invalid_phase'
        ],
        'expected_responses': [
            'Subscribed to accumulation phase alerts for AAPL',
            'Subscribed to markup phase alerts for AAPL',
            'Subscribed to distribution phase alerts for AAPL',
            'Subscribed to markdown phase alerts for AAPL',
            'Invalid symbol',
            'Invalid market phase'
        ]
    },
    {
        'name': 'Candle Timeframe Tests',
        'commands': [
            '/setcandle 1Min',
            '/setcandle 5Min',
            '/setcandle 1H',
            '/setcandle invalid',
            '/getcandle'
        ],
        'expected_responses': [
            'Candle timeframe set to 1 minute',
            'Candle timeframe set to 5 minutes',
            'Candle timeframe set to 1 hour',
            'Invalid timeframe',
            'Current candle timeframe:'
        ]
    },
    {
        'name': 'Notification Subscription Tests',
        'commands': [
            '/subscribe AAPL all',
            '/unsubscribe AAPL all',
            '/subscribe INVALID_SYMBOL all',
            '/subscribe',  # Missing parameters
            '/listsubscriptions'
        ],
        'expected_responses': [
            'Subscribed to all alerts for AAPL',
            'Unsubscribed from all alerts for AAPL',
            'Invalid symbol',
            'Please provide symbol and phase',
            'Your current subscriptions'
        ]
    },
    {
        'name': 'Historical Data Tests',
        'commands': [
            f'/historical AAPL {VALID_PAST_DATE}',
            f'/historical GOOGL {OUTSIDE_WINDOW_DATE}',
            f'/historical INVALID_SYMBOL {VALID_PAST_DATE}',
            f'/historical AAPL {FUTURE_DATE}',
            '/historical'  # Missing parameters
        ],
        'expected_responses': [
            'Historical data for AAPL',
            'Date outside allowed window',
            'Invalid symbol',
            'Cannot request future dates',
            'Please provide symbol and date'
        ]
    },
    {
        'name': 'Malformed Input Tests',
        'commands': [
            '/analyze @#$%',
            '/setcandle 2.5Min',
            '/subscribe @ #',
            '/historical AAPL not-a-date',
            '/setindex 123',
            '/analyze AAPL GOOGL',  # Too many parameters
            '/setcandle 1Min 5Min'  # Too many parameters
        ],
        'expected_responses': [
            'Invalid symbol format',
            'Invalid timeframe format',
            'Invalid subscription format',
            'Invalid date format',
            'Invalid index format',
            'Too many parameters',
            'Too many parameters'
        ]
    },
    {
        'name': 'Random Stock Historical Tests',
        'commands': [
            # Will be populated dynamically in test_runner.py
        ],
        'expected_responses': [
            # Will be populated dynamically in test_runner.py
        ]
    }
]

# Special test cases that need dynamic generation
DYNAMIC_TEST_CASES = {
    'random_historical': {
        'generate': get_random_stock_and_date,
        'validate': lambda response: 'Historical data' in response
    }
}
