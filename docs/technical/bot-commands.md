# Telegram Bot Commands Guide

## Basic Commands

### /start
Initiates interaction with the bot and provides basic setup instructions.
```
Usage: /start
Response: Welcome message and setup guide
```

### /watch
Start monitoring a specific ticker.
```
Usage: /watch TICKER
Example: /watch AAPL
Response: Confirmation and initial market analysis
```

### /unwatch
Stop monitoring a ticker.
```
Usage: /unwatch TICKER
Example: /unwatch AAPL
Response: Confirmation of removal
```

### /status
View current watchlist and positions.
```
Usage: /status
Response: List of watched tickers and positions
```

## Trading Commands

### /setkey
Configure Alpaca API credentials (send in private message only).
```
Usage: /setkey YOUR_API_KEY YOUR_SECRET_KEY
Response: Confirmation of API key storage
```

### /buy
Execute a buy order (requires API key setup).
```
Usage: /buy TICKER [QUANTITY] [TYPE]
Examples:
- /buy AAPL 100 shares
- /buy AAPL 5 185c_30d
Response: Order confirmation or error message
```

### /sell
Execute a sell order (requires API key setup).
```
Usage: /sell TICKER [QUANTITY] [TYPE]
Examples:
- /sell AAPL 100 shares
- /sell AAPL 5 185c_30d
Response: Order confirmation or error message
```

## Information Commands

### /analysis
Request detailed analysis for a ticker.
```
Usage: /analysis TICKER
Example: /analysis AAPL
Response: Comprehensive market analysis
```

### /help
Display command help.
```
Usage: /help
Response: List of available commands and usage
```

## Notification Format

### Market Updates
```
🔄 Market Update: [TICKER]
📊 Market Phase: [Phase]
➡️ EMAs:
   - 13 EMA: $[Price]
   - 34 EMA: $[Price]
   - 89 EMA: $[Price]
```

### Entry Signals
```
✅ Entry Signal: [TICKER]
📈 Type: [Long/Short]
💰 Price: $[Price]
🎯 Targets:
   1. $[Price] (Risk:Reward 1:1)
   2. $[Price] (Risk:Reward 1:2)
⛔️ Stop Loss: $[Price]
```

### Options Recommendations
```
🔄 Options Play: [TICKER]
📅 Expiry: [Date]
⚡️ Strike: $[Strike]
💰 Entry: $[Price]
⛔️ Stop: $[Price]
```

## Error Messages

### API Errors
```
❌ Error: [Message]
📝 Details: [Technical details]
```

### Validation Errors
```
⚠️ Warning: [Message]
💡 Correct usage: [Example]
```

## Rate Limiting

- Maximum 5 commands per minute per user
- Watch list limited to 10 tickers per user
- Trade commands require 5-second cooldown
