# The Blackprint Trading Strategy - Technical Design Document

## 1. Overview
This document outlines the technical implementation of Al Pickett's trading strategy from "The Blackprint" in TradingView's Pine Script. The strategy is a trend-following system based on multiple exponential moving averages (EMAs), Parabolic SAR, and MACD indicators.

## 2. Technical Components

### 2.1 Indicators
1. Exponential Moving Averages (EMAs):
   - Fast EMAs: 5, 7, 9, 11, 13 periods
   - Medium EMA: 34 periods
   - Slow EMA: 89 periods
   - Implementation: Using TradingView's built-in `ta.ema()` function

2. Parabolic SAR:
   - Settings: Acceleration = 0.05, Maximum = 0.2
   - Implementation: Using TradingView's built-in `ta.sar()` function

3. MACD:
   - Settings: Fast = 12, Slow = 26, Signal = 9
   - Implementation: Using TradingView's built-in `ta.macd()` function

### 2.2 Market Phase Detection
The strategy defines three distinct market phases:

1. Unordered Phase:
   ```
   13 EMA between 34 EMA and 89 EMA
   Condition: (ema13 < ema34 && ema13 > ema89) || (ema13 > ema34 && ema13 < ema89)
   ```

2. Emerging Phase:
   ```
   13 EMA above both 89 EMA and 34 EMA
   Condition: ema13 > ema89 && ema13 > ema34
   ```

3. Trending Phase:
   ```
   13 EMA above 34 EMA and 89 EMA (continuation of Emerging Phase)
   Condition: Same as Emerging Phase with additional trend confirmation
   ```

## 3. Entry and Exit Rules

### 3.1 Long Entry Conditions
All conditions must be true:
1. Not in Unordered Phase
2. Price pulled back to 13 EMA
3. Price closes above 5 EMA
4. Parabolic SAR below price
5. Optional: MACD showing bullish momentum

### 3.2 Short Entry Conditions
All conditions must be true:
1. Not in Unordered Phase
2. Price pulled back to 34 EMA
3. Price closes below 13 EMA
4. Parabolic SAR above price
5. Optional: MACD showing bearish momentum

### 3.3 Exit Rules
1. Stop Loss:
   - 5min timeframe: 15 pips
   - 15min timeframe: 20 pips
   - 1hr timeframe: 30 pips
   - 4hr timeframe: 50 pips

2. Take Profit:
   - Trailing stop using Parabolic SAR
   - Optional: Risk:Reward based exits

## 4. Risk Management Implementation

### 4.1 Position Sizing
- User-configurable risk per trade (1-5% of account)
- Position size calculation:
  ```
  position_size = (account_size * risk_percentage) / (stop_loss_pips * pip_value)
  ```

### 4.2 Risk Controls
1. Maximum open positions
2. Maximum daily loss
3. Maximum drawdown protection
4. Correlation protection for multiple positions

## 5. Pine Script Structure

### 5.1 Script Organization
```pine
//@version=5
strategy("The Blackprint Strategy", overlay=true)

// 1. Input Parameters
// 2. Indicator Calculations
// 3. Market Phase Detection
// 4. Entry/Exit Signal Generation
// 5. Risk Management
// 6. Strategy Execution
// 7. Plot Visualization
```

### 5.2 Key Functions
1. `detectMarketPhase()`
2. `calculatePullback()`
3. `checkEntryConditions()`
4. `calculatePositionSize()`
5. `manageRisk()`

## 6. Visualization

### 6.1 Chart Overlay
1. All EMAs with distinct colors
2. Parabolic SAR dots
3. Market phase labels
4. Entry/exit points

### 6.2 Separate Panes
1. MACD indicator
2. Market phase indicator
3. Risk exposure meter

## 7. Backtesting Configuration

### 7.1 Parameters to Test
1. EMA periods
2. Parabolic SAR settings
3. Risk percentages
4. Stop loss variations
5. Market phase definitions

### 7.2 Performance Metrics
1. Total return
2. Maximum drawdown
3. Sharpe ratio
4. Win rate
5. Average win/loss
6. Profit factor

## 8. Future Enhancements

### 8.1 Potential Improvements
1. Volume confirmation
2. Multiple timeframe analysis
3. Volatility adjustments
4. Additional filter conditions
5. Dynamic position sizing

### 8.2 Composer Integration Notes
1. Strategy adaptation requirements
2. Risk management modifications
3. Execution differences
4. Monitoring considerations

## 9. Implementation Schedule

### 9.1 Phase 1: Core Strategy
1. Basic indicator setup
2. Market phase detection
3. Entry/exit signals
4. Basic plotting

### 9.2 Phase 2: Risk Management
1. Position sizing
2. Stop loss implementation
3. Risk controls
4. Performance monitoring

### 9.3 Phase 3: Optimization
1. Backtesting
2. Parameter optimization
3. Performance improvements
4. Documentation

### 9.4 Phase 4: Composer Migration
1. Strategy adaptation
2. Testing
3. Monitoring setup
4. Production deployment

# Blackprint Trading Strategy Design

## Overview
The Blackprint trading strategy is based on Al Pickett's methodology, combining technical analysis with risk management to identify and execute high-probability trades.

## Core Components

### 1. Technical Analysis
```python
# Key indicators used in strategy/indicators.py
- RSI (Relative Strength Index)
- Moving Averages (EMA, SMA)
- Volume Analysis
- Price Action Patterns
```

### 2. Entry Conditions
1. Primary Trend Alignment
   - Identify trend using multiple timeframes
   - Confirm trend strength with volume
   - Validate momentum indicators

2. Entry Triggers
   - Price action confirmation
   - Volume confirmation
   - Indicator convergence

### 3. Risk Management
```python
# Implementation in strategy/risk_manager.py
- Position Sizing: 2% risk per trade
- Maximum Positions: 5 concurrent trades
- Stop Loss: Technical or % based
- Take Profit: R-multiple based
```

### 4. Position Management
1. Entry Management
   - Partial position entries
   - Scaling in opportunities
   - Entry price optimization

2. Exit Management
   - Trailing stops
   - Partial profit taking
   - Break-even adjustments

## Strategy Parameters

### 1. Time Frames
- Primary: 1 Hour
- Secondary: 4 Hour
- Trend: Daily

### 2. Technical Parameters
```python
# Default values in config/strategy.py
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
EMA_FAST = 12
EMA_SLOW = 26
VOLUME_MA = 20
```

### 3. Risk Parameters
```python
# Default values in config/risk.py
RISK_PER_TRADE = 0.02  # 2%
MAX_POSITIONS = 5
STOP_LOSS_ATR = 2
TAKE_PROFIT_RR = 2  # Risk:Reward ratio
```

## Signal Generation

### 1. Entry Signals
```python
class SignalGenerator:
    def generate_entry_signal(self, data):
        # 1. Trend Analysis
        trend = self.analyze_trend(data)
        
        # 2. Volume Confirmation
        volume_valid = self.check_volume(data)
        
        # 3. Technical Confirmation
        technicals_valid = self.check_technicals(data)
        
        # 4. Generate Signal
        if all([trend, volume_valid, technicals_valid]):
            return self.create_signal('ENTRY')
```

### 2. Exit Signals
```python
class SignalGenerator:
    def generate_exit_signal(self, position):
        # 1. Stop Loss Check
        if self.check_stop_loss(position):
            return self.create_signal('EXIT')
        
        # 2. Take Profit Check
        if self.check_take_profit(position):
            return self.create_signal('EXIT')
        
        # 3. Technical Exit
        if self.check_technical_exit(position):
            return self.create_signal('EXIT')
```

## Backtesting Framework

### 1. Data Requirements
- Historical price data (OHLCV)
- Volume data
- Market condition data

### 2. Performance Metrics
```python
# Implementation in analysis/performance.py
- Sharpe Ratio
- Maximum Drawdown
- Win Rate
- Average R-Multiple
- Profit Factor
```

### 3. Optimization Parameters
- Entry timing
- Position sizing
- Stop loss placement
- Take profit levels

## Real-Time Execution

### 1. Market Data Processing
```python
class MarketDataProcessor:
    def process_data(self, data):
        # 1. Clean Data
        cleaned_data = self.clean_data(data)
        
        # 2. Calculate Indicators
        indicators = self.calculate_indicators(cleaned_data)
        
        # 3. Generate Signals
        signals = self.generate_signals(indicators)
        
        return signals
```

### 2. Order Execution
```python
class OrderExecutor:
    def execute_signal(self, signal):
        # 1. Validate Signal
        if not self.validate_signal(signal):
            return
        
        # 2. Calculate Position Size
        size = self.calculate_position_size(signal)
        
        # 3. Submit Order
        order = self.submit_order(signal, size)
        
        # 4. Track Order
        self.track_order(order)
```

## Risk Controls

### 1. Pre-Trade Checks
- Account balance verification
- Position limit check
- Risk per trade validation
- Market condition assessment

### 2. Post-Trade Monitoring
- Position tracking
- P&L monitoring
- Stop loss verification
- Technical indicator monitoring

### 3. System Safeguards
- Circuit breakers
- Error handling
- Connection monitoring
- Data validation

## Performance Analysis

### 1. Trade Metrics
- Win/Loss ratio
- Average trade duration
- Risk/Reward achieved
- Maximum adverse excursion

### 2. Portfolio Metrics
- Overall return
- Risk-adjusted return
- Drawdown analysis
- Correlation analysis

### 3. Strategy Metrics
- Signal quality
- Entry/exit efficiency
- Technical indicator effectiveness
- Market condition performance

## Implementation Roadmap

### Phase 1: Core Strategy
1. Basic indicator calculation
2. Signal generation
3. Risk management
4. Order execution

### Phase 2: Enhancement
1. Advanced position management
2. Dynamic parameter adjustment
3. Market condition analysis
4. Performance optimization

### Phase 3: Refinement
1. Machine learning integration
2. Alternative data sources
3. Advanced risk models
4. Portfolio optimization