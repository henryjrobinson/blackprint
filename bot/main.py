import os
import logging
import signal
import asyncio
from dotenv import load_dotenv
from bot.telegram_bot import BlackprintBot

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Global variables for cleanup
bot = None
main_task = None

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {sig}, initiating shutdown...")
    if main_task:
        main_task.cancel()

async def cleanup():
    """Cleanup resources"""
    try:
        if bot:
            logger.info("Stopping bot...")
            await bot.run()  # This will trigger the cleanup in finally block
    except Exception as e:
        logger.error(f"Error during cleanup: {e}", exc_info=True)

async def main():
    global bot
    try:
        # Load environment variables
        load_dotenv()
        logger.info("Environment variables loaded")
        
        # Get bot token from environment
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        logger.info("Bot token retrieved")
        
        logger.info("Starting Blackprint Trading Bot...")
        logger.info("Initializing bot...")
        bot = BlackprintBot()
        logger.info("Bot initialized, starting run sequence...")
        
        # Configure logging
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=os.getenv('LOG_LEVEL', 'INFO')
        )

        # Initialize and run the bot
        try:
            await bot.run()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Error running bot: {e}", exc_info=True)
        finally:
            # Ensure proper cleanup
            await bot.cleanup()
    except asyncio.CancelledError:
        logger.info("Main task cancelled")
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}", exc_info=True)
    finally:
        if bot:
            await bot.cleanup()
        logger.info("Shutdown complete")

if __name__ == '__main__':
    try:
        # Setup signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Create event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run main task
        logger.info("Starting main event loop...")
        main_task = loop.create_task(main())
        loop.run_until_complete(main_task)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt...")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    finally:
        try:
            # Cancel any pending tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            
            # Run cleanup
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
            logger.info("Shutdown complete")
        except Exception as e:
            logger.error(f"Error during final cleanup: {e}", exc_info=True)
