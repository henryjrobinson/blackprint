# Blackprint Trading Bot Deployment Guide

## Prerequisites

- Docker and Docker Compose
- Telegram Bot Token (from @BotFather)
- Alpaca API Key and Secret (from Alpaca dashboard)

## Environment Setup

1. Copy the example environment file:
   ```bash
   cp env.example .env
   ```

2. Update the following variables in `.env`:
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
   - `ALPACA_API_KEY`: Your Alpaca API key
   - `ALPACA_API_SECRET`: Your Alpaca API secret
   - `ALPACA_API_URL`: Use `https://paper-api.alpaca.markets` for paper trading

## Local Deployment

1. Build and start the container:
   ```bash
   docker-compose up --build -d
   ```

2. Check the logs:
   ```bash
   docker-compose logs -f
   ```

3. Stop the bot:
   ```bash
   docker-compose down
   ```

## Bot Commands

The bot supports the following commands:

- `/start` - Initialize the bot and get help
- `/help` - Display available commands
- `/analyze SYMBOL` - Analyze current market phase for any symbol
- `/historical SYMBOL` - Show historical phase distribution
- `/candle NUMBER` - Set candle length in minutes (e.g., `/candle 5`)
- `/subscribe SYMBOL` - Subscribe to real-time updates
- `/unsubscribe SYMBOL` - Unsubscribe from updates

You can also analyze any symbol by simply typing its ticker (e.g., "AAPL").

## Error Handling

The bot includes robust error handling for:
- Invalid symbols
- Missing market data
- Connection issues
- API rate limits

## Monitoring

Monitor the bot's health through:
1. Docker container logs
2. Application logs in the container
3. Telegram bot status updates

## Troubleshooting

If the bot becomes unresponsive:

1. Check container status:
   ```bash
   docker-compose ps
   ```

2. View recent logs:
   ```bash
   docker-compose logs --tail=100
   ```

3. Restart the bot:
   ```bash
   docker-compose restart
   ```

4. If issues persist, full reset:
   ```bash
   docker-compose down
   docker-compose up --build -d
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

## Updating the Bot

1. **Update Process**
   ```bash
   # Stop the bot (in Docker container)
   docker-compose down
   
   # Pull latest changes
   git pull origin main
   
   # Install any new dependencies
   docker-compose up --build -d
   
   # Restart the bot
   docker-compose restart
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
