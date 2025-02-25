from typing import Optional, Dict, Any
import logging
import os
from datetime import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    CallbackContext
)
import pandas as pd
from .market_phases import MarketIndex, PhaseDetectionConfig
from .market_state import MarketStateManager
from .data_manager import AlpacaDataManager
import asyncio

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

VALID_TIMEFRAMES = ["1Min", "5Min", "15Min", "30Min", "1H", "4H", "1D"]

class BlackprintBot:
    """Telegram bot for Blackprint trading strategy"""
    
    def __init__(self):
        """Initialize the bot"""
        # Load environment variables
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.api_secret = os.getenv('ALPACA_API_SECRET')
        self.base_url = os.getenv('ALPACA_API_URL', 'https://paper-api.alpaca.markets')
        
        # Initialize components
        self.application = None
        self.data_manager = None
        self.streaming_task = None
        
        # Initialize message handlers
        self.message_handlers = {
            '/start': self.start_command,
            '/help': self.help_command,
            '/analyze': self.analyze_stock,
            '/historical': self.historical_command,
            '/subscribe': self.subscribe_command,
            '/unsubscribe': self.unsubscribe_command,
            '/setcandle': self.set_candle_command,
            '/setindex': self.set_index_command,
            '/candle': self.handle_candle_length
        }
        
        # Initialize managers
        self.market_manager = None
        
        # Register for phase change notifications
        self.subscribed_users = set()
        
        # Common symbols for quick access
        self.quick_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
    
    async def initialize(self):
        """Initialize the application"""
        logger.info("Initializing application...")
        
        # Create application instance
        self.application = Application.builder().token(self.token).build()
        await self.application.initialize()
        
        # Add handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        for command in self.message_handlers:
            self.application.add_handler(CommandHandler(command.lstrip('/'), self.message_handlers[command]))
        
        # Add callback query handler
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Add error handler
        self.application.add_error_handler(self.error_handler)
        
        # Initialize data manager
        self.data_manager = AlpacaDataManager(self.api_key, self.api_secret, self.base_url)
        
        # Initialize market manager
        self.market_manager = MarketStateManager(self.data_manager)
        
        # Register for phase change notifications
        self.market_manager.register_phase_change_callback(self._handle_phase_change)
        
        # Setup command handlers
        self.setup_handlers()
    
    async def run(self):
        """Run the bot"""
        try:
            if not self.token:
                logger.error("No bot token provided")
                return

            logger.info("Initializing application...")
            await self.initialize()
            
            if not self.application:
                logger.error("Failed to initialize application")
                return
                
            logger.info("Starting application...")
            await self.application.start()
            logger.info("Starting polling...")
            await self.application.updater.start_polling(drop_pending_updates=True)
            logger.info("Polling started successfully")
            
            # Start market data streaming
            logger.info("Starting market data streaming...")
            self.streaming_task = asyncio.create_task(self.data_manager.start_streaming())
            logger.info("Streaming task created")
            
            # Main loop
            logger.info("Entering main loop...")
            while True:
                if not self.application.running:
                    break
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in run loop: {e}", exc_info=True)
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Starting cleanup...")
        
        # Stop market data streaming
        await self.data_manager.stop_streaming()
        
        # Stop the application
        if self.application and self.application.running:
            logger.info("Stopping application...")
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Application stopped")
            
        # Cancel any remaining tasks
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                
    def setup_handlers(self):
        """Setup command and message handlers"""
        # Basic commands
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Market analysis commands
        self.application.add_handler(CommandHandler("analyze", self.analyze_stock))
        self.application.add_handler(CommandHandler("historical", self.historical_command))
        self.application.add_handler(CommandHandler("subscribe", self.subscribe_command))
        self.application.add_handler(CommandHandler("unsubscribe", self.unsubscribe_command))
        
        # Settings commands
        self.application.add_handler(CommandHandler("setcandle", self.set_candle_command))
        self.application.add_handler(CommandHandler("setindex", self.set_index_command))
        self.application.add_handler(CommandHandler("candle", self.handle_candle_length))
    
    def get_main_keyboard(self) -> ReplyKeyboardMarkup:
        """Create the main keyboard with common commands"""
        keyboard = [
            [KeyboardButton("/analyze"), KeyboardButton("/historical")],
            [KeyboardButton("/subscribe"), KeyboardButton("/unsubscribe")],
            [KeyboardButton("/setcandle"), KeyboardButton("/setindex")],
            [KeyboardButton("/help")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    def get_symbol_keyboard(self) -> InlineKeyboardMarkup:
        """Create inline keyboard with common symbols"""
        keyboard = []
        # Create rows of 3 symbols each
        for i in range(0, len(self.quick_symbols), 3):
            row = []
            for symbol in self.quick_symbols[i:i+3]:
                row.append(InlineKeyboardButton(
                    symbol, 
                    callback_data=f"analyze_{symbol}"
                ))
            keyboard.append(row)
        return InlineKeyboardMarkup(keyboard)
    
    def get_timeframe_keyboard(self) -> InlineKeyboardMarkup:
        """Create inline keyboard with timeframe options"""
        keyboard = []
        # Create rows of 3 timeframes each
        for i in range(0, len(VALID_TIMEFRAMES), 3):
            row = []
            for tf in VALID_TIMEFRAMES[i:i+3]:
                row.append(InlineKeyboardButton(
                    tf, 
                    callback_data=f"timeframe_{tf}"
                ))
            keyboard.append(row)
        return InlineKeyboardMarkup(keyboard)
    
    def get_index_keyboard(self) -> InlineKeyboardMarkup:
        """Create inline keyboard with index options"""
        keyboard = []
        indices = [index.name for index in MarketIndex]
        # Create rows of 2 indices each
        for i in range(0, len(indices), 2):
            row = []
            for idx in indices[i:i+2]:
                row.append(InlineKeyboardButton(
                    idx, 
                    callback_data=f"index_{idx}"
                ))
            keyboard.append(row)
        return InlineKeyboardMarkup(keyboard)

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()  # Acknowledge the button press
        
        data = query.data
        if data.startswith("analyze_"):
            symbol = data.split("_")[1]
            # Create new context args for the analyze command
            context.args = [symbol]
            await self.analyze_stock(update, context)
            
        elif data.startswith("timeframe_"):
            timeframe = data.split("_")[1]
            context.args = [timeframe]
            await self.set_candle_command(update, context)
            
        elif data.startswith("index_"):
            await self.handle_index_callback(update, context)
    
    async def handle_message(self, update: Update, context: CallbackContext) -> None:
        """Handle non-command messages"""
        try:
            message = update.message.text.upper()
            
            # Check if it's a stock symbol
            if message in self.quick_symbols:
                await self.analyze_stock(update, context)
            else:
                await update.message.reply_text(
                    "I don't understand that command. Try /help to see what I can do!"
                )
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await update.message.reply_text("Sorry, I couldn't process that message.")

    async def start_command(self, update: Update, context: CallbackContext) -> None:
        """Handle the /start command"""
        try:
            welcome_message = (
                "👋 Welcome to Blackprint Trading Bot!\n\n"
                "I can help you analyze stocks and manage your portfolio. Here are some things I can do:\n"
                "- /analyze <symbol> - Get real-time market analysis\n"
                "- /historical <symbol> - View historical data\n"
                "- /subscribe <symbol> - Get notifications for a stock\n"
                "- /unsubscribe <symbol> - Stop notifications\n"
                "- /help - See all available commands\n\n"
                "Try analyzing a stock like AAPL or GOOGL!"
            )
            await update.message.reply_text(welcome_message, reply_markup=self.get_main_keyboard())
        except Exception as e:
            logger.error(f"Error in start command: {e}", exc_info=True)
            await update.message.reply_text("Sorry, I couldn't process that command.")

    async def help_command(self, update: Update, context: CallbackContext) -> None:
        """Handle the /help command"""
        try:
            help_message = (
                "🤖 Blackprint Trading Bot Commands:\n\n"
                "Market Analysis:\n"
                "- /analyze <symbol> - Get real-time market analysis\n"
                "- /historical <symbol> - View historical data\n\n"
                "Notifications:\n"
                "- /subscribe <symbol> - Get notifications for a stock\n"
                "- /unsubscribe <symbol> - Stop notifications\n\n"
                "Settings:\n"
                "- /setcandle <1m|5m|15m|1h|1d> - Set candle timeframe\n"
                "- /setindex <SPY|QQQ|DIA> - Set market index\n\n"
                "Other:\n"
                "- /help - Show this help message\n"
                "- /start - Show welcome message\n\n"
                "You can also type any stock symbol directly!"
            )
            await update.message.reply_text(help_message, reply_markup=self.get_main_keyboard())
        except Exception as e:
            logger.error(f"Error in help command: {e}", exc_info=True)
            await update.message.reply_text("Sorry, I couldn't process that command.")

    async def analyze_stock(self, update: Update, context: CallbackContext) -> None:
        """Analyze a stock symbol"""
        try:
            # Get the symbol from the message
            if context.args:
                symbol = context.args[0].upper()
            else:
                symbol = update.message.text.upper()
            
            if symbol not in self.quick_symbols:
                await update.message.reply_text(
                    f"Sorry, I can only analyze these symbols for now: {', '.join(self.quick_symbols)}"
                )
                return
            
            # Send initial message
            message = await update.message.reply_text(f"Analyzing {symbol}...")
            
            # Get market data
            try:
                bars = await self.data_manager.get_historical_bars(symbol, "1Day", limit=5)
                if bars is None or bars.empty:
                    await message.edit_text(f"No data available for {symbol}")
                    return
                
                # Calculate basic metrics
                last_bar = bars.iloc[-1]
                prev_bar = bars.iloc[-2]
                price_change = ((last_bar['close'] - prev_bar['close']) / prev_bar['close']) * 100
                
                # Format the analysis message
                analysis = (
                    f"📊 {symbol} Analysis:\n\n"
                    f"Current Price: ${last_bar['close']:.2f}\n"
                    f"Daily Change: {price_change:.2f}%\n"
                    f"Volume: {last_bar['volume']:,}\n"
                    f"High: ${last_bar['high']:.2f}\n"
                    f"Low: ${last_bar['low']:.2f}\n\n"
                    f"Want real-time updates? Use /subscribe {symbol}"
                )
                
                # Update the message with the analysis
                await message.edit_text(analysis)
                
            except Exception as e:
                logger.error(f"Error getting market data: {e}", exc_info=True)
                await message.edit_text(f"Sorry, I couldn't analyze {symbol} right now.")
                
        except Exception as e:
            logger.error(f"Error in analyze command: {e}", exc_info=True)
            await update.message.reply_text("Sorry, I couldn't process that command.")

    async def subscribe_command(self, update: Update, context: CallbackContext) -> None:
        """Subscribe to updates for a symbol"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "Please provide a symbol to subscribe to. Example: /subscribe AAPL"
                )
                return
                
            symbol = context.args[0].upper()
            if symbol not in self.quick_symbols:
                await update.message.reply_text(
                    f"Sorry, I can only track these symbols for now: {', '.join(self.quick_symbols)}"
                )
                return
            
            # Add user to subscribed users set
            user_id = update.effective_user.id
            self.subscribed_users.add(user_id)
            
            await update.message.reply_text(
                f"✅ You are now subscribed to {symbol} updates!\n"
                f"You will receive notifications about significant price movements."
            )
            
        except Exception as e:
            logger.error(f"Error in subscribe command: {e}", exc_info=True)
            await update.message.reply_text("Sorry, I couldn't process that command.")

    async def unsubscribe_command(self, update: Update, context: CallbackContext) -> None:
        """Unsubscribe from updates"""
        try:
            user_id = update.effective_user.id
            self.subscribed_users.discard(user_id)
            
            await update.message.reply_text(
                "❌ You have been unsubscribed from all updates."
            )
            
        except Exception as e:
            logger.error(f"Error in unsubscribe command: {e}", exc_info=True)
            await update.message.reply_text("Sorry, I couldn't process that command.")

    async def notify_subscribers(self, message: str) -> None:
        """Send a notification to all subscribed users"""
        if not self.subscribed_users:
            return
            
        for user_id in self.subscribed_users:
            try:
                await self.application.bot.send_message(
                    chat_id=user_id,
                    text=message
                )
            except Exception as e:
                logger.error(f"Error sending notification to user {user_id}: {e}")

    async def error_handler(self, update: object, context: CallbackContext) -> None:
        """Handle errors in the telegram bot"""
        logger.error(f"Update {update} caused error: {context.error}")
        if update and isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "Sorry, something went wrong. Please try again later."
            )

    async def _handle_phase_change(self, symbol: str, state: Dict[str, Any]):
        """Handle market phase change notifications"""
        if not self.subscribed_users:
            return  # No subscribers
            
        # Format the notification message
        message = f"*Market Phase Change Alert*\n\n{self.market_manager.format_market_state(state)}"
        
        # Send notification to all subscribed users
        for user_id in self.subscribed_users:
            try:
                await self.application.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Error sending notification to user {user_id}: {e}")
                self.subscribed_users.discard(user_id)  # Remove user if we can't send messages

    async def handle_index_callback(self, update: Update, context: CallbackContext) -> None:
        """Handle index selection callback"""
        query = update.callback_query
        await query.answer()  # Acknowledge the button click
        
        try:
            # Extract the selected index from callback data
            selected_index = query.data.replace('index_', '')
            
            # Send a new message with the selection
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"You selected {selected_index}. Fetching market data..."
            )
            
            # Update the original message to show selection
            await query.edit_message_text(
                text=f"Selected index: {selected_index}"
            )
            
            # TODO: Fetch and display market data for the selected index
            
        except Exception as e:
            logger.error(f"Error handling index callback: {e}", exc_info=True)
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Sorry, there was an error processing your selection. Please try again."
            )

    async def historical_command(self, update: Update, context: CallbackContext) -> None:
        """Get historical data for a symbol"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "Please provide a symbol to analyze. Example: /historical AAPL"
                )
                return
                
            symbol = context.args[0].upper()
            if symbol not in self.quick_symbols:
                await update.message.reply_text(
                    f"Sorry, I can only analyze these symbols for now: {', '.join(self.quick_symbols)}"
                )
                return
            
            # Send initial message
            message = await update.message.reply_text(f"Getting historical data for {symbol}...")
            
            try:
                # Get historical data
                bars = await self.data_manager.get_historical_bars(symbol, "1Day", limit=30)
                if bars is None or bars.empty:
                    await message.edit_text(f"No historical data available for {symbol}")
                    return
                
                # Calculate basic metrics
                last_bar = bars.iloc[-1]
                first_bar = bars.iloc[0]
                total_change = ((last_bar['close'] - first_bar['close']) / first_bar['close']) * 100
                
                # Calculate average volume
                avg_volume = bars['volume'].mean()
                
                # Format the analysis message
                analysis = (
                    f"📈 {symbol} Historical Analysis (30 Days):\n\n"
                    f"Start Price: ${first_bar['close']:.2f}\n"
                    f"End Price: ${last_bar['close']:.2f}\n"
                    f"Total Change: {total_change:.2f}%\n"
                    f"Average Volume: {avg_volume:,.0f}\n"
                    f"Highest Price: ${bars['high'].max():.2f}\n"
                    f"Lowest Price: ${bars['low'].min():.2f}\n\n"
                    f"Want real-time updates? Use /subscribe {symbol}"
                )
                
                await message.edit_text(analysis)
                
            except Exception as e:
                logger.error(f"Error getting historical data: {e}", exc_info=True)
                await message.edit_text(f"Sorry, I couldn't get historical data for {symbol} right now.")
                
        except Exception as e:
            logger.error(f"Error in historical command: {e}", exc_info=True)
            await update.message.reply_text("Sorry, I couldn't process that command.")

    async def set_candle_command(self, update: Update, context: CallbackContext) -> None:
        """Set the candle timeframe"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "Please provide a timeframe. Example: /setcandle 1m\n"
                    "Valid timeframes: 1m, 5m, 15m, 1h, 1d"
                )
                return
            
            timeframe = context.args[0].lower()
            valid_timeframes = ['1m', '5m', '15m', '1h', '1d']
            
            if timeframe not in valid_timeframes:
                await update.message.reply_text(
                    f"Invalid timeframe. Please use one of: {', '.join(valid_timeframes)}"
                )
                return
            
            # Update the timeframe
            self.data_manager.set_timeframe(timeframe)
            
            await update.message.reply_text(
                f"✅ Candle timeframe set to {timeframe}"
            )
            
        except Exception as e:
            logger.error(f"Error in set_candle command: {e}", exc_info=True)
            await update.message.reply_text("Sorry, I couldn't process that command.")

    async def set_index_command(self, update: Update, context: CallbackContext) -> None:
        """Set the market index"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "Please provide an index symbol. Example: /setindex SPY\n"
                    "Valid indices: SPY, QQQ, DIA"
                )
                return
            
            index = context.args[0].upper()
            valid_indices = ['SPY', 'QQQ', 'DIA']
            
            if index not in valid_indices:
                await update.message.reply_text(
                    f"Invalid index. Please use one of: {', '.join(valid_indices)}"
                )
                return
            
            # Update the index
            self.data_manager.set_index(index)
            
            await update.message.reply_text(
                f"✅ Market index set to {index}"
            )
            
        except Exception as e:
            logger.error(f"Error in set_index command: {e}", exc_info=True)
            await update.message.reply_text("Sorry, I couldn't process that command.")

    async def handle_candle_length(self, update: Update, context: CallbackContext) -> None:
        """Handle the candle length command"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "Please provide a candle length in minutes. Example: /candle 5"
                )
                return
            
            try:
                length = int(context.args[0])
                if length <= 0:
                    raise ValueError("Length must be positive")
            except ValueError:
                await update.message.reply_text(
                    "Please provide a valid positive number for the candle length"
                )
                return
            
            # Update the candle length
            self.data_manager.set_candle_length(length)
            
            await update.message.reply_text(
                f"✅ Candle length set to {length} minutes"
            )
            
        except Exception as e:
            logger.error(f"Error in candle length command: {e}", exc_info=True)
            await update.message.reply_text("Sorry, I couldn't process that command.")
