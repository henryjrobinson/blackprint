# Blackprint Strategy - Alpaca Implementation Guide

## 1. Environment Setup

### 1.1 Project Structure
```
blackprint-trading/
├── config/
│   ├── __init__.py
│   └── settings.py        # API keys and configuration
├── data/
│   ├── __init__.py
│   └── market_data.py     # Data fetching and processing
├── strategy/
│   ├── __init__.py
│   ├── indicators.py      # Technical indicators
│   └── blackprint.py      # Main strategy logic
├── risk/
│   ├── __init__.py
│   └── management.py      # Position sizing and risk management
├── utils/
│   ├── __init__.py
│   └── helpers.py         # Utility functions
├── tests/
│   └── test_strategy.py   # Unit tests
├── main.py               # Strategy execution
├── requirements.txt      # Dependencies
└── README.md            # Documentation
```

### 1.2 Dependencies
```
# requirements.txt
alpaca-trade-api>=3.0.0
pandas>=1.5.0
numpy>=1.21.0
ta>=0.10.0  # Technical analysis library
python-dotenv>=0.19.0
pytest>=7.0.0
```

### 1.3 Environment Setup Steps
1. Create Virtual Environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Create .env file:
```env
ALPACA_API_KEY='your_api_key'
ALPACA_SECRET_KEY='your_secret_key'
ALPACA_BASE_URL='https://paper-api.alpaca.markets'  # Paper trading
```

## 2. Alpaca Account Setup

### 2.1 Account Creation
1. Go to https://app.alpaca.markets/signup
2. Create paper trading account
3. Get API keys from dashboard
4. Set up paper trading environment first

### 2.2 API Configuration
```python
# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

ALPACA_CONFIG = {
    'API_KEY': os.getenv('ALPACA_API_KEY'),
    'SECRET_KEY': os.getenv('ALPACA_SECRET_KEY'),
    'BASE_URL': os.getenv('ALPACA_BASE_URL'),
    'DATA_FEED': 'iex'  # or 'sip' for paid subscription
}

STRATEGY_CONFIG = {
    'TIMEFRAME': '15Min',
    'RISK_PER_TRADE': 0.02,  # 2% risk per trade
    'MAX_POSITIONS': 5,
    'UNIVERSE': ['SPY', 'QQQ', 'IWM']  # Initial trading universe
}
```

## 3. Implementation Components

### 3.1 Market Data Handler
```python
# data/market_data.py
from alpaca_trade_api.rest import REST
import pandas as pd

class MarketData:
    def __init__(self, api):
        self.api = api
    
    def get_bars(self, symbol, timeframe, limit=100):
        """Fetch historical bars for calculation"""
        pass
    
    def get_latest_trade(self, symbol):
        """Get latest trade for real-time updates"""
        pass
```

### 3.2 Technical Indicators
```python
# strategy/indicators.py
import pandas as pd
import numpy as np

class Indicators:
    @staticmethod
    def calculate_emas(data, periods=[5,7,9,11,13,34,89]):
        """Calculate multiple EMAs"""
        pass
    
    @staticmethod
    def calculate_psar(data, af=0.02, max_af=0.2):
        """Calculate Parabolic SAR"""
        pass
```

### 3.3 Strategy Implementation
```python
# strategy/blackprint.py
class BlackprintStrategy:
    def __init__(self, api, config):
        self.api = api
        self.config = config
        self.indicators = Indicators()
    
    def detect_market_phase(self, data):
        """Detect current market phase"""
        pass
    
    def generate_signals(self, data):
        """Generate trading signals"""
        pass
```

### 3.4 Risk Management
```python
# risk/management.py
class RiskManager:
    def __init__(self, config):
        self.config = config
    
    def calculate_position_size(self, price, stop_loss):
        """Calculate position size based on risk"""
        pass
    
    def set_stop_loss(self, timeframe, entry_price, direction):
        """Set stop loss based on timeframe"""
        pass
```

## 4. Main Strategy Execution

### 4.1 Main Loop
```python
# main.py
class TradingApp:
    def __init__(self):
        self.api = self.setup_api()
        self.strategy = BlackprintStrategy(self.api, STRATEGY_CONFIG)
        self.risk_manager = RiskManager(STRATEGY_CONFIG)
    
    def run(self):
        """Main trading loop"""
        pass
```

## 5. Testing Framework

### 5.1 Paper Trading Testing
1. Start with small position sizes
2. Monitor execution quality
3. Track strategy performance
4. Validate risk management

### 5.2 Unit Tests
```python
# tests/test_strategy.py
def test_market_phase_detection():
    """Test market phase detection logic"""
    pass

def test_signal_generation():
    """Test trading signal generation"""
    pass
```

## 6. Monitoring and Logging

### 6.1 Logging Setup
```python
# utils/helpers.py
import logging

def setup_logging():
    """Configure logging for the application"""
    pass

def log_trade(trade_details):
    """Log trade information"""
    pass
```

### 6.2 Performance Monitoring
- Track key metrics:
  - Win rate
  - Profit factor
  - Maximum drawdown
  - Sharpe ratio
  - Trade duration

## 7. Deployment Steps

1. **Initial Testing**:
   - Run in paper trading mode
   - Validate all signals
   - Verify risk management

2. **Production Deployment**:
   - Switch to live API endpoints
   - Start with minimal capital
   - Monitor closely for first week

3. **Ongoing Maintenance**:
   - Daily performance review
   - Weekly strategy adjustment
   - Monthly performance analysis

## 8. Error Handling

### 8.1 Common Issues
1. API connection failures
2. Data quality issues
3. Order execution errors
4. Position tracking discrepancies

### 8.2 Error Recovery
```python
def handle_api_error(error):
    """Handle API-related errors"""
    pass

def handle_data_error(error):
    """Handle data-related errors"""
    pass
```

## 9. Next Steps

1. Implement basic data fetching
2. Build indicator calculations
3. Develop signal generation
4. Add risk management
5. Create main execution loop
6. Test paper trading
7. Add monitoring and logging
8. Deploy to production

Would you like to begin with implementing any specific component?

# Alpaca API Implementation Guide

## Overview

The Blackprint Trading Bot uses Alpaca's API for real-time market data and historical price information. This guide covers the implementation details and best practices.

## API Integration

### Data Manager Class

```python
class AlpacaDataManager:
    def __init__(self):
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.api_secret = os.getenv('ALPACA_API_SECRET')
        
        # Initialize clients
        self.hist_client = StockHistoricalDataClient(self.api_key, self.api_secret)
        self.stream_client = StockDataStream(self.api_key, self.api_secret)
        
        # Cache and state management
        self._latest_bars = {}
        self._callbacks = []
        self.subscribed_symbols = set()
```

### Timeframe Management

```python
self.timeframe_map = {
    "1Min": TimeFrame.Minute,
    "5Min": TimeFrame(5, TimeFrame.Minute),
    "15Min": TimeFrame(15, TimeFrame.Minute),
    "30Min": TimeFrame(30, TimeFrame.Minute),
    "1H": TimeFrame.Hour,
    "4H": TimeFrame(4, TimeFrame.Hour),
    "1D": TimeFrame.Day
}
```

## Data Streaming

### Connection Setup

```python
async def start_streaming(self):
    """Start the streaming connection"""
    try:
        # Connect to the streaming client
        await self.stream_client.connect()
        
        # Subscribe to existing symbols
        if self.subscribed_symbols:
            await self.subscribe_to_bars(list(self.subscribed_symbols))
        
        # Start processing messages
        await self.stream_client._run_forever()
    except Exception as e:
        logger.error(f"Error starting streaming: {e}")
        raise
```

### Bar Data Handling

```python
async def _handle_bar(self, bar):
    """Handle incoming bar data"""
    try:
        symbol = bar.symbol
        
        # Convert bar to DataFrame row
        bar_data = {
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume,
            'timestamp': bar.timestamp
        }
        
        # Update cache and notify callbacks
        self._latest_bars[symbol] = pd.concat([
            self._latest_bars.get(symbol, pd.DataFrame()),
            pd.DataFrame([bar_data])
        ], ignore_index=True)
        
        for callback in self._callbacks:
            await callback(symbol, self._latest_bars[symbol])
            
    except Exception as e:
        logger.error(f"Error handling bar data: {e}")
```

## Historical Data

### Data Retrieval

```python
async def get_bars(self, symbol: str, timeframe: str = "1H", limit: int = 100):
    """Fetch historical bars for a symbol"""
    try:
        end = datetime.now(pytz.UTC)
        multiplier = 3 if timeframe in ["4H", "1D"] else 1
        start = end - timedelta(days=limit * multiplier)
        
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=self.timeframe_map[timeframe],
            start=start,
            end=end
        )
        
        bars = self.hist_client.get_stock_bars(request)
        
        if bars and hasattr(bars, 'df'):
            df = bars.df.reset_index(level=[0,1])
            df = df.dropna().sort_values('timestamp')
            return df
            
        raise ValueError(f"No data returned for {symbol}")
        
    except Exception as e:
        logger.error(f"Error fetching bars for {symbol}: {e}")
        raise
```

## Error Handling

### Common Issues

1. **Connection Errors**
   ```python
   try:
       await self.stream_client.connect()
   except Exception as e:
       logger.error(f"Connection error: {e}")
       await asyncio.sleep(5)  # Backoff
       await self.reconnect()
   ```

2. **Rate Limits**
   ```python
   if response.status_code == 429:
       wait_time = int(response.headers.get('Retry-After', 60))
       logger.warning(f"Rate limit hit, waiting {wait_time}s")
       await asyncio.sleep(wait_time)
   ```

3. **Data Validation**
   ```python
   def validate_data(self, df):
       if df is None or df.empty:
           raise ValueError("No data available")
       if not all(col in df.columns for col in ['open', 'high', 'low', 'close']):
           raise ValueError("Missing required columns")
   ```

## Best Practices

### 1. Connection Management
- Implement automatic reconnection
- Handle connection timeouts
- Monitor connection health
- Log connection events

### 2. Data Handling
- Cache frequently used data
- Implement data validation
- Handle missing data gracefully
- Maintain data consistency

### 3. Error Recovery
- Implement exponential backoff
- Log detailed error information
- Notify on critical failures
- Maintain operation state

### 4. Performance
- Optimize data structures
- Minimize API calls
- Use appropriate timeframes
- Implement efficient caching

## Configuration

### Environment Variables
```env
ALPACA_API_KEY=your_api_key
ALPACA_API_SECRET=your_api_secret
ALPACA_API_URL=https://paper-api.alpaca.markets
```

### Runtime Settings
```python
config = {
    'default_timeframe': '15Min',
    'cache_duration': 3600,  # 1 hour
    'reconnect_attempts': 3,
    'backoff_factor': 2,
}
```

## Monitoring

### 1. Connection Health
- Connection status
- Latency metrics
- Error rates
- Reconnection attempts

### 2. Data Quality
- Data freshness
- Missing data points
- Data consistency
- Update frequency

### 3. API Usage
- Rate limit status
- Request counts
- Response times
- Error distribution

## Testing

### 1. Unit Tests
```python
def test_data_validation():
    manager = AlpacaDataManager()
    with pytest.raises(ValueError):
        manager.validate_data(None)
    with pytest.raises(ValueError):
        manager.validate_data(pd.DataFrame())
```

### 2. Integration Tests
```python
async def test_historical_data():
    manager = AlpacaDataManager()
    data = await manager.get_bars("AAPL", "1H", 100)
    assert len(data) > 0
    assert all(col in data.columns for col in ['open', 'high', 'low', 'close'])
```

## Deployment Considerations

### 1. Production Setup
- Use paper trading initially
- Monitor API usage
- Implement proper logging
- Set up alerts

### 2. Scaling
- Optimize connection usage
- Manage memory efficiently
- Handle multiple symbols
- Consider rate limits