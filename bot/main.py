import os
from dotenv import load_dotenv
from bot.telegram_bot import BlackprintBot

def main():
    # Load environment variables
    load_dotenv()
    
    # Get bot token from environment
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
    
    # Initialize and run bot
    bot = BlackprintBot(bot_token)
    print("🤖 Starting Blackprint Trading Bot...")
    bot.run()

if __name__ == "__main__":
    main()
