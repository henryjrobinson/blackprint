from typing import Optional, Dict, Any
import logging
from datetime import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
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
        self.application.add_handler(CommandHandler("analyze", self.analyze_command))
        self.application.add_handler(CommandHandler("historical", self.historical_command))
        self.application.add_handler(CommandHandler("subscribe", self.subscribe_command))
        self.application.add_handler(CommandHandler("unsubscribe", self.unsubscribe_command))
        
        # Settings commands
        self.application.add_handler(CommandHandler("setcandle", self.set_candle_command))
        self.application.add_handler(CommandHandler("setindex", self.set_index_command))
        
        # Callback query handler for inline buttons
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
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
            await self.analyze_command(update, context)
            
        elif data.startswith("timeframe_"):
            timeframe = data.split("_")[1]
            context.args = [timeframe]
            await self.set_candle_command(update, context)
            
        elif data.startswith("index_"):
            index = data.split("_")[1]
            context.args = [index]
            await self.set_index_command(update, context)
    
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
    
    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get current market phase analysis"""
        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "Select a symbol to analyze:",
                reply_markup=self.get_symbol_keyboard()
            )
            return
        
        symbol = context.args[0].upper()
        try:
            # Get current market state
            state = self.market_manager.get_current_state(symbol)
            if not state:
                await update.message.reply_text(
                    f"⏳ Gathering data for {symbol}... Please try again in a few minutes."
                )
                return
            
            # Format response
            response = self.market_manager.format_market_state(state)
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            await update.message.reply_text(
                f"❌ Error analyzing {symbol}. Please try again later."
            )
    
    async def historical_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get historical market phase analysis"""
        if not context.args or len(context.args) < 3:
            await update.message.reply_text(
                "❌ Please specify symbol and datetime.\n"
                "Example: `/historical AAPL 2025-02-18 14:30`",
                parse_mode='Markdown'
            )
            return
        
        symbol = context.args[0].upper()
        try:
            # Parse datetime (assumed to be in US/Eastern)
            date_str = f"{context.args[1]} {context.args[2]}"
            eastern = pytz.timezone('US/Eastern')
            timestamp = eastern.localize(datetime.strptime(date_str, "%Y-%m-%d %H:%M"))
            
            # Get historical state
            state = await self.market_manager.get_historical_state(symbol, timestamp)
            if not state:
                await update.message.reply_text(
                    f"❌ No data found for {symbol} at {date_str} ET"
                )
                return
            
            # Format response
            response = self.market_manager.format_market_state(state, is_historical=True)
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid datetime format. Use: YYYY-MM-DD HH:MM"
            )
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            await update.message.reply_text(
                f"❌ Error retrieving historical data. Please try again later."
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
            f"✅ Candle size updated to {timeframe}"
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

    def run(self):
        """Run the bot"""
        self.application.run_polling()
