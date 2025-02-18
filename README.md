# Blackprint Trading Bot

A Telegram-based trading bot implementing Al Pickett's Blackprint trading strategy using the Alpaca API.

## Overview

The Blackprint Trading Bot provides automated market analysis and trading signals based on the Blackprint trading strategy. It monitors market conditions, identifies trading opportunities, and delivers clear, actionable insights via Telegram.

### Key Features

- Real-time market phase detection
- Technical indicator calculations (EMAs, PSAR, MACD)
- Options analysis and recommendations
- Telegram bot interface
- Optional automated trading via Alpaca API
- Docker containerization for easy deployment

## Quick Start

1. **Prerequisites**
   - Python 3.11+
   - Docker (optional)
   - Telegram Bot Token
   - Alpaca API credentials (optional)

2. **Installation**
   ```bash
   # Clone the repository
   git clone https://github.com/yourusername/blackprint.git
   cd blackprint

   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configuration**
   ```bash
   # Create .env file
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Running the Bot**
   ```bash
   # Direct execution
   python main.py

   # Or using Docker
   docker-compose up -d
   ```

## Documentation

- [Strategy Documentation](docs/strategy/)
  - [Trading Strategy Design](docs/strategy/trading-strategy-design.md)
  - [Alpaca Implementation Guide](docs/strategy/alpaca-implementation-guide.md)

- [Technical Documentation](docs/technical/)
  - [Architecture Overview](docs/technical/architecture.md)
  - [Bot Commands](docs/technical/bot-commands.md)
  - [Development Guide](docs/technical/development-guide.md)

- [Deployment Guide](docs/deployment/)
  - [Docker Setup](docs/deployment/docker-setup.md)
  - [Environment Configuration](docs/deployment/environment-config.md)

## Development

### Project Structure
```
blackprint/
├── config/             # Configuration files
├── data/              # Market data handling
├── strategy/          # Trading strategy implementation
├── risk/              # Risk management
├── utils/             # Utility functions
├── tests/             # Test suite
└── docs/              # Documentation
```

### Testing
```bash
# Run tests
pytest
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Al Pickett for the Blackprint trading strategy
- Alpaca for their trading API
- Python-Telegram-Bot team for their excellent library
