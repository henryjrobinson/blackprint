from typing import Optional, Dict, Any
import logging
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
    
    def __init__(self, token: str):
        """Initialize the bot with Alpaca integration"""
        self.token = token
        self.application = Application.builder().token(token).build()
        
        # Initialize managers
        self.data_manager = AlpacaDataManager()
        self.market_manager = MarketStateManager(self.data_manager)
        
        # Register for phase change notifications
        self.market_manager.register_phase_change_callback(self._handle_phase_change)
        
        # Setup command handlers
        self.setup_handlers()
        
        # Track subscribed users for notifications
        self.subscribed_users = set()
        
        # Common symbols for quick access
        self.quick_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
    
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
        
        # Callback query handler for inline buttons
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start_streaming(self):
        """Start the data streaming"""
        try:
            await self.data_manager.start_streaming()
            logger.info("Started data streaming")
        except Exception as e:
            logger.error(f"Error starting data streaming: {e}")
    
    async def run(self):
        """Start the bot and begin streaming market data"""
        try:
            # First, try to clean up any existing connections
            try:
                await self.application.bot.delete_webhook(drop_pending_updates=True)
                await asyncio.sleep(10)  # Wait for Telegram to clean up
            except Exception as e:
                logger.warning(f"Error cleaning up webhook: {e}")
            
            # Start the bot with polling
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(allowed_updates=['message', 'callback_query'])
            
            # Start streaming market data
            await self.start_streaming()
            
            # Keep the application running
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            raise
        finally:
            try:
                await self.application.stop()
            except Exception as e:
                logger.error(f"Error stopping application: {e}")
    
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
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message when the command /start is issued"""
        welcome_text = (
            "🤖 Welcome to the Blackprint Trading Bot!\n\n"
            "I can help you analyze market phases using the Blackprint strategy.\n\n"
            "Use the buttons below to navigate or type commands directly:\n"
            "/analyze - Get current market phase and indicators\n"
            "/historical - Analyze historical market state\n"
            "/subscribe - Get notifications for market phase changes\n"
            "/unsubscribe - Stop receiving notifications\n"
            "/setcandle - Set candle size (default: 15Min)\n"
            "/setindex - Set reference index (default: US30)\n"
            "/help - Show detailed help"
        )
        # Send message with main keyboard
        await update.message.reply_text(
            welcome_text, 
            reply_markup=self.get_main_keyboard(),
            parse_mode='Markdown'
        )
        
        # Send quick access symbols
        await update.message.reply_text(
            "📊 Quick Analysis - Select a symbol:",
            reply_markup=self.get_symbol_keyboard()
        )
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send detailed help"""
        help_text = (
            "📚 *Blackprint Trading Bot Help*\n\n"
            "*Market Analysis Commands:*\n"
            "/analyze <symbol> - Get current market analysis\n"
            "  Example: `/analyze AAPL`\n\n"
            "/historical <symbol> <datetime> - Get historical analysis\n"
            "  Example: `/historical AAPL 2025-02-18 14:30`\n\n"
            "*Notification Commands:*\n"
            "/subscribe - Get market phase change alerts\n"
            "/unsubscribe - Stop receiving alerts\n\n"
            "*Settings Commands:*\n"
            "/setcandle <timeframe> - Set analysis timeframe\n"
            f"  Valid options: {', '.join(VALID_TIMEFRAMES)}\n"
            "/setindex <index> - Set reference index\n"
            "  Valid options: US30, SPX, NDX, RUT\n\n"
            "*Tips:*\n"
            "• All times are in US/Eastern timezone\n"
            "• Historical data is limited to last 30 days\n"
            "• Default candle size is 15Min"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def analyze_stock(self, update: Update, context: CallbackContext) -> None:
        """Analyze a stock symbol"""
        try:
            # Get symbol from either command args or direct message
            if context.args:
                symbol = context.args[0].upper()
            elif update.message.text.startswith('/'):
                await update.message.reply_text(
                    "Please provide a stock symbol to analyze (e.g., /analyze AAPL)",
                    reply_markup=self.get_main_keyboard()
                )
                return
            else:
                symbol = update.message.text.strip().upper()

            # Remove the buttons and show analyzing message
            await update.message.reply_text(
                f"📊 Analyzing {symbol} with {self.data_manager.candle_length}-minute candles...",
                reply_markup=ReplyKeyboardRemove()
            )
            
            try:
                # Get the historical data
                df = await self.data_manager.get_bars(symbol)
                if df is None or df.empty:
                    await update.message.reply_text(
                        f"❌ No data found for {symbol}. Please check the symbol and try again.",
                        reply_markup=self.get_main_keyboard()
                    )
                    return
                
                # Get the analysis
                phase, metrics = self.market_manager.detect_phase(df)
                
                # Format the response
                response = (
                    f"Analysis for {symbol} ({self.data_manager.candle_length}min candles):\n\n"
                    f"🏷 Market Phase: {phase.value.upper()}\n"
                    f"📈 Current Price: ${metrics['close']:.2f}\n"
                    f"📊 EMAs:\n"
                    f"  • Fast: ${metrics['ema_fast']:.2f} ({'+' if metrics['fast_slope'] > 0 else ''}{metrics['fast_slope']:.4f})\n"
                    f"  • Medium: ${metrics['ema_medium']:.2f} ({'+' if metrics['medium_slope'] > 0 else ''}{metrics['medium_slope']:.4f})\n"
                    f"  • Slow: ${metrics['ema_slow']:.2f} ({'+' if metrics['slow_slope'] > 0 else ''}{metrics['slow_slope']:.4f})\n"
                    f"💫 Momentum: {'+' if metrics['price_momentum'] > 0 else ''}{metrics['price_momentum']:.4f}"
                )
                
                await update.message.reply_text(
                    response,
                    reply_markup=self.get_main_keyboard()
                )
                
            except ValueError as e:
                await update.message.reply_text(
                    f"❌ Error analyzing {symbol}: {str(e)}",
                    reply_markup=self.get_main_keyboard()
                )
                
        except Exception as e:
            logger.error(f"Error in analyze_stock: {e}")
            await update.message.reply_text(
                "❌ An error occurred while analyzing the stock. Please try again later.",
                reply_markup=self.get_main_keyboard()
            )
    
    async def historical_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get historical market phase analysis"""
        try:
            if not context.args or len(context.args) != 1:
                await update.message.reply_text(
                    "Please provide a stock symbol (e.g., /historical AAPL)",
                    reply_markup=self.get_main_keyboard()
                )
                return
            
            symbol = context.args[0].upper()
            await update.message.reply_text(
                f"📊 Analyzing historical data for {symbol} with {self.data_manager.candle_length}-minute candles...",
                reply_markup=ReplyKeyboardRemove()
            )
            
            try:
                # Get historical data
                df = await self.data_manager.get_bars(symbol, limit=200)  # Get more historical data
                if df is None or df.empty:
                    await update.message.reply_text(
                        f"❌ No historical data found for {symbol}. Please check the symbol and try again.",
                        reply_markup=self.get_main_keyboard()
                    )
                    return
                
                # Analyze phases over time
                phases = []
                for i in range(max(len(df)-10, 0), len(df)):  # Look at last 10 periods
                    subset = df.iloc[:i+1]
                    phase, _ = self.market_manager.detect_phase(subset)
                    phases.append(phase.value)
                
                # Count phase occurrences
                phase_counts = {}
                for phase in phases:
                    phase_counts[phase] = phase_counts.get(phase, 0) + 1
                
                # Format response
                current_phase, metrics = self.market_manager.detect_phase(df)
                response = (
                    f"Historical Analysis for {symbol} ({self.data_manager.candle_length}min candles):\n\n"
                    f"🏷 Current Phase: {current_phase.value.upper()}\n"
                    f"📈 Current Price: ${metrics['close']:.2f}\n\n"
                    f"📊 Recent Phase Distribution:\n"
                )
                
                for phase, count in phase_counts.items():
                    percentage = (count / len(phases)) * 100
                    response += f"  • {phase.upper()}: {'▓' * int(percentage/10)}{'░' * (10-int(percentage/10))} {percentage:.1f}%\n"
                
                response += f"\n💫 Current Momentum: {'+' if metrics['price_momentum'] > 0 else ''}{metrics['price_momentum']:.4f}"
                
                await update.message.reply_text(
                    response,
                    reply_markup=self.get_main_keyboard()
                )
                
            except ValueError as e:
                await update.message.reply_text(
                    f"❌ Error analyzing historical data for {symbol}: {str(e)}",
                    reply_markup=self.get_main_keyboard()
                )
                
        except Exception as e:
            logger.error(f"Error in historical_command: {e}")
            await update.message.reply_text(
                "❌ An error occurred while analyzing historical data. Please try again later.",
                reply_markup=self.get_main_keyboard()
            )
    
    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Subscribe to market phase change notifications"""
        user_id = update.effective_user.id
        self.subscribed_users.add(user_id)
        await update.message.reply_text(
            "✅ You are now subscribed to market phase change notifications.\n"
            "You will receive alerts when the market phase changes for any monitored symbol."
        )
    
    async def unsubscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unsubscribe from market phase change notifications"""
        user_id = update.effective_user.id
        self.subscribed_users.discard(user_id)
        await update.message.reply_text(
            "✅ You have been unsubscribed from market phase change notifications."
        )
    
    async def set_candle_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set the candle size for market analysis"""
        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "Select a timeframe:",
                reply_markup=self.get_timeframe_keyboard()
            )
            return
            
        timeframe = context.args[0]
        if timeframe not in VALID_TIMEFRAMES:
            await update.message.reply_text(
                f"❌ Invalid timeframe. Valid options are: {', '.join(VALID_TIMEFRAMES)}"
            )
            return
            
        config = PhaseDetectionConfig(candle_size=timeframe)
        self.market_manager.detector.config = config
        await update.message.reply_text(
            f"✅ Candle size updated to {timeframe}. Please confirm by typing '/confirm'"
        )
    
    async def handle_candle_length(self, update: Update, context: CallbackContext) -> None:
        """Handle candle length command"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "Please specify a candle length in minutes (e.g., /candle 5)",
                    reply_markup=self.get_main_keyboard()
                )
                return

            length = int(context.args[0])
            self.data_manager.set_candle_length(length)
            await update.message.reply_text(
                f"✅ Candle length updated to {length} minutes",
                reply_markup=self.get_main_keyboard()
            )
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid candle length. Please specify a number in minutes (e.g., /candle 5)",
                reply_markup=self.get_main_keyboard()
            )
    
    async def set_index_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set the reference index for market phase detection"""
        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "Select a reference index:",
                reply_markup=self.get_index_keyboard()
            )
            return
            
        index_name = context.args[0].upper()
        try:
            index = MarketIndex[index_name]
            self.market_manager.detector.set_index(index)
            await update.message.reply_text(
                f"✅ Reference index updated to {index.name}"
            )
        except KeyError:
            await update.message.reply_text(
                f"❌ Invalid index. Valid options are: US30, SPX, NDX, RUT"
            )
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Log errors caused by updates"""
        logger.error(f"Update {update} caused error {context.error}")
        if isinstance(update, Update) and update.message:
            await update.message.reply_text(
                "❌ Sorry, an error occurred while processing your request."
            )
    
    async def _handle_phase_change(self, symbol: str, state: Dict[str, Any]):
        """Handle market phase change notifications"""
        if not self.subscribed_users:
            return  # No subscribers
            
        # Format the notification message
        message = f"🔄 *Market Phase Change Alert*\n\n{self.market_manager.format_market_state(state)}"
        
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
