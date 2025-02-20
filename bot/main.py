import os
import logging
from dotenv import load_dotenv
import asyncio
from bot.telegram_bot import BlackprintBot

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    # Load environment variables
    load_dotenv()
    
    # Get bot token from environment
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
    
    logger.info("Starting Blackprint Trading Bot...")
    bot = BlackprintBot(bot_token)
    await bot.run()

if __name__ == '__main__':
    asyncio.run(main())
