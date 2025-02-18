# Blackprint Trading Bot Commands

## Available Commands

### Basic Commands

#### `/start`
- Description: Initialize the bot and get started
- Usage: `/start`
- Response: Welcome message and basic setup instructions

#### `/help`
- Description: Display available commands and their usage
- Usage: `/help`
- Response: List of all commands with descriptions

#### `/status`
- Description: Check bot status and current positions
- Usage: `/status`
- Response: Current market phase, active positions, and account status

### Analysis Commands

#### `/analyze <symbol>`
- Description: Analyze a specific symbol using the Blackprint strategy
- Usage: `/analyze AAPL` or `/analyze SPY`
- Response: 
  - Current market phase
  - EMA relationships
  - RSI value
  - MACD status
  - Trading signals (if any)

#### `/positions`
- Description: View current positions and their status
- Usage: `/positions`
- Response:
  - List of open positions
  - Entry prices
  - Current P&L
  - Risk metrics

### Settings Commands

#### `/settings`
- Description: View and modify bot settings
- Usage: `/settings`
- Response: Current settings and options to modify them

Available settings:
- Risk per trade
- Maximum positions
- Account size
- Notification preferences

## Command Examples

### Analyzing a Stock
```
User: /analyze AAPL
Bot: 📊 Analysis for AAPL:
Market Phase: BULLISH
EMAs: Aligned (13 > 34 > 89)
RSI: 58 (Neutral)
MACD: Bullish Crossover
Signal: LONG Entry Valid
Risk: 2% ($2000)
```

### Checking Positions
```
User: /positions
Bot: 📈 Current Positions:
1. AAPL (LONG)
   Entry: $150.25
   Current: $155.50
   P&L: +3.5%
   Risk: $300 (1.5%)

Total Risk Exposure: 1.5%
Available Positions: 4
```

### Modifying Settings
```
User: /settings
Bot: ⚙️ Current Settings:
Risk Per Trade: 2%
Max Positions: 5
Account Size: $100,000
Notifications: All

To modify, use:
/settings risk <percentage>
/settings positions <number>
/settings account <amount>
```

## Error Handling

### Common Error Messages

1. Invalid Symbol
```
Error: Symbol 'INVALID' not found. Please check the symbol and try again.
```

2. Market Closed
```
Error: Market is currently closed. Analysis based on last available data.
```

3. Rate Limit
```
Error: Rate limit exceeded. Please wait 60 seconds before trying again.
```

## Future Commands

### Planned Additions

1. `/backtest <symbol>`
- Test strategy on historical data
- Generate performance metrics
- Show trade examples

2. `/alerts <on/off>`
- Configure automatic alerts
- Set custom conditions
- Manage notification preferences

3. `/portfolio`
- View portfolio analytics
- Risk exposure analysis
- Performance metrics

4. `/trade <symbol> <direction>`
- Execute trades directly
- Set position size
- Configure stop-loss
