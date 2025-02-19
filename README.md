# Blackprint Trading Bot

A sophisticated market phase detection and analysis bot that operates through Telegram, providing real-time market insights and automated trading signals.

## Features

- Real-time market phase detection
- Interactive Telegram bot interface
- Multiple timeframe analysis
- Support for various market indices
- Customizable symbol tracking
- Automated notifications for phase changes

## Setup

1. Clone the repository:
```bash
git clone https://github.com/henryjrobinson/blackprint.git
cd blackprint
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp env.example .env
```
Edit `.env` with your:
- Telegram Bot Token
- Alpaca API Key and Secret
- Other configuration parameters

## Project Structure

```
blackprint/
├── bot/                    # Bot implementation
│   ├── __init__.py
│   ├── telegram_bot.py     # Main bot logic
│   ├── market_phases.py    # Market phase detection
│   └── main.py            # Entry point
├── tests/                  # Test suite
│   ├── conftest.py        # Test configuration
│   ├── test_telegram_bot.py
│   └── test_market_phases.py
├── requirements.txt        # Project dependencies
├── .env.example           # Environment template
└── README.md
```

## Testing

The project uses pytest for testing with async support. Run tests with:

```bash
pytest -v
```

### Test Coverage

- Unit tests for all bot components
- Integration tests for market phase detection
- Comprehensive button and command testing
- Mock implementations for external APIs

## Development

1. **Environment Setup**
   - Python 3.10+
   - Virtual environment recommended
   - Required packages in requirements.txt

2. **Running Tests**
   ```bash
   pytest tests/ -v
   ```

3. **Running the Bot**
   ```bash
   python -m bot.main
   ```

## Bot Commands

- `/start` - Initialize bot and show main keyboard
- `/analyze [symbol]` - Analyze market phase for a symbol
- `/historical [symbol]` - View historical phase changes
- `/setcandle [timeframe]` - Change analysis timeframe
- `/setindex [index]` - Change reference market index

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details
