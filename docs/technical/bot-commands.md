# Blackprint Trading Bot Commands

## Core Commands

### Analysis Commands

- `/analyze SYMBOL` - Analyze current market phase for any symbol
  - Example: `/analyze AAPL`
  - Also supports direct symbol input (just type "AAPL")
  - Shows current phase, EMAs, and momentum indicators
  - Displays current candle length in output

- `/historical SYMBOL` - Show historical phase distribution
  - Example: `/historical MSFT`
  - Shows phase distribution over last 10 periods
  - Visual representation of phase percentages
  - Includes current momentum and price

### Configuration Commands

- `/candle NUMBER` - Set candle length in minutes
  - Example: `/candle 5` for 5-minute candles
  - Provides confirmation message
  - Affects all subsequent analysis

- `/setindex INDEX` - Set reference index for market phase detection
  - Supported indices: US30, SPX, NDX, RUT, VIX, FTSE, DAX, NIKKEI
  - Example: `/setindex SPX`

### Streaming Commands

- `/subscribe SYMBOL` - Subscribe to real-time updates
  - Example: `/subscribe AAPL`
  - Receive notifications on phase changes
  - Includes price and momentum updates

- `/unsubscribe SYMBOL` - Unsubscribe from updates
  - Example: `/unsubscribe AAPL`
  - Stops real-time notifications

### System Commands

- `/start` - Initialize the bot
  - Displays welcome message
  - Shows available commands
  - Sets up user session

- `/help` - Display command help
  - Lists all available commands
  - Shows usage examples
  - Provides quick start guide

## Usage Tips

1. Direct Symbol Analysis
   - Type any symbol directly to analyze it
   - No need for /analyze command
   - Example: Just type "AAPL" or "MSFT"

2. Candle Length
   - Default is 15 minutes
   - Can be changed with `/candle` command
   - Current length shown in all analysis

3. Error Handling
   - Invalid symbols: Clear error message
   - No data: Suggests checking symbol
   - Connection issues: Automatic retry

4. Real-time Updates
   - Phase changes
   - Significant price movements
   - Momentum shifts

## Response Format

Analysis responses include:
- Market Phase (TRENDING, EMERGING, PULLBACK, UNORDERED)
- Current Price
- EMA Values and Slopes
- Momentum Indicators
- Candle Length Used

Historical analysis includes:
- Phase Distribution Chart
- Recent Phase Changes
- Current Phase and Price
- Momentum Information

## Examples

1. Basic Analysis:
   ```
   /analyze AAPL
   
   Analysis for AAPL (15min candles):
   🏷 Market Phase: TRENDING
   📈 Current Price: $182.50
   📊 EMAs:
     • Fast: $181.20 (+0.0023)
     • Medium: $180.80 (+0.0015)
     • Slow: $180.10 (+0.0008)
   💫 Momentum: +0.0045
   ```

2. Historical Analysis:
   ```
   /historical MSFT
   
   Historical Analysis for MSFT (15min candles):
   🏷 Current Phase: EMERGING
   📈 Current Price: $402.75
   
   📊 Recent Phase Distribution:
     • TRENDING: ▓▓▓▓▓░░░░░ 50.0%
     • EMERGING: ▓▓░░░░░░░░ 20.0%
     • PULLBACK: ▓▓▓░░░░░░░ 30.0%
   
   💫 Current Momentum: +0.0067
   ```
