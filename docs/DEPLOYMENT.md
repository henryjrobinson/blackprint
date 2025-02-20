# Blackprint Trading Bot Deployment Guide

## Prerequisites

1. **API Keys and Tokens**
   - Telegram Bot Token (from @BotFather)
   - Alpaca API Key and Secret (from Alpaca dashboard)
   - Paper trading account recommended for initial testing

2. **System Requirements**
   - Python 3.10+
   - pip package manager
   - Git
   - Screen or tmux (for production deployment)

## Local Deployment

1. **Environment Setup**
   ```bash
   # Clone repository
   git clone https://github.com/henryjrobinson/blackprint.git
   cd blackprint

   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configuration**
   ```bash
   # Copy example environment file
   cp env.example .env

   # Edit .env with your credentials
   TELEGRAM_BOT_TOKEN=your_bot_token
   ALPACA_API_KEY=your_alpaca_key
   ALPACA_SECRET_KEY=your_alpaca_secret
   ```

3. **Running Locally**
   ```bash
   # Start the bot
   python -m bot.main
   ```

## Production Deployment

1. **Server Setup** (Example using Ubuntu)
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y

   # Install Python and dependencies
   sudo apt install python3.10 python3.10-venv git screen -y
   ```

2. **Application Setup**
   ```bash
   # Clone and setup
   git clone https://github.com/henryjrobinson/blackprint.git
   cd blackprint
   python3.10 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   ```bash
   # Setup environment variables
   cp env.example .env
   nano .env  # Edit with your production credentials
   ```

4. **Running in Production**
   ```bash
   # Using screen for persistent running
   screen -S blackprint
   source venv/bin/activate
   python -m bot.main
   
   # Detach from screen: Ctrl+A, then D
   # Reattach to screen: screen -r blackprint
   ```

5. **Monitoring and Maintenance**
   ```bash
   # Check bot status
   screen -ls  # List running screens
   
   # View logs
   tail -f logs/bot.log
   ```

## Security Considerations

1. **API Keys**
   - Never commit API keys to version control
   - Use environment variables for sensitive data
   - Rotate API keys periodically

2. **Access Control**
   - Implement user whitelisting in production
   - Monitor for suspicious activity
   - Rate limit API requests

3. **Data Protection**
   - Backup configuration regularly
   - Encrypt sensitive data
   - Monitor disk usage

## Troubleshooting

1. **Common Issues**
   - Bot not responding: Check internet connection and API keys
   - Data delays: Verify Alpaca API status
   - Memory issues: Monitor system resources

2. **Debugging**
   ```bash
   # Check logs
   tail -f logs/bot.log
   
   # Test API connections
   python -m bot.test_connection
   ```

## Updating the Bot

1. **Update Process**
   ```bash
   # Stop the bot (in screen session)
   Ctrl+C
   
   # Pull latest changes
   git pull origin main
   
   # Install any new dependencies
   pip install -r requirements.txt
   
   # Restart the bot
   python -m bot.main
   ```

## Backup and Recovery

1. **Regular Backups**
   - Backup .env file
   - Backup user preferences
   - Backup custom configurations

2. **Recovery Process**
   ```bash
   # Restore from backup
   cp backup/.env .env
   cp -r backup/config/* config/
   ```

## Health Checks

1. **Automated Monitoring**
   - Set up periodic health checks
   - Monitor memory usage
   - Check API rate limits

2. **Alert System**
   - Configure error notifications
   - Set up status alerts
   - Monitor system resources
