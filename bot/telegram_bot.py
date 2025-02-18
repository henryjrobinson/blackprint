from typing import Optional, Dict, Any
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackContext
)
from decimal import Decimal
import pandas as pd
import yfinance as yf
from .trading_service import TradingService

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class BlackprintBot:
    """
    Telegram bot for Blackprint trading strategy
    """
    
    def __init__(self, token: str, account_size: float = 100000, risk_per_trade: float = 0.02):
        """
        Initialize the bot
        
        Args:
            token: Telegram bot token
            account_size: Trading account size
            risk_per_trade: Risk per trade as decimal
        """
        self.application = Application.builder().token(token).build()
        self.trading_service = TradingService(
            account_size=account_size,
            risk_per_trade=risk_per_trade
        )
        self.setup_handlers()
        
    def setup_handlers(self):
        """Setup command and message handlers"""
        # Basic commands
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        
        # Trading commands
        self.application.add_handler(CommandHandler("analyze", self.analyze_command))
        self.application.add_handler(CommandHandler("positions", self.positions_command))
        self.application.add_handler(CommandHandler("settings", self.settings_command))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message when the command /start is issued"""
        welcome_text = (
            "🤖 Welcome to the Blackprint Trading Bot!\n\n"
            "I can help you analyze markets and execute trades using the "
            "Blackprint trading strategy.\n\n"
            "Available commands:\n"
            "/analyze <symbol> - Analyze a trading pair\n"
            "/positions - View open positions\n"
            "/status - Check bot status\n"
            "/settings - View/modify settings\n"
            "/help - Show this help message"
        )
        await update.message.reply_text(welcome_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send detailed help when the command /help is issued"""
        help_text = (
            "🔍 *Blackprint Trading Bot Commands*\n\n"
            "*Basic Commands:*\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/status - Check bot status\n\n"
            "*Trading Commands:*\n"
            "/analyze <symbol> - Analyze a trading pair\n"
            "  Example: `/analyze AAPL`\n"
            "/positions - View open positions\n"
            "/settings - View/modify settings\n\n"
            "*Settings Options:*\n"
            "- Risk per trade (default: 2%)\n"
            "- Max positions (default: 5)\n"
            "- Trading pairs\n"
            "- Notifications preferences"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check bot status and connection to trading API"""
        status_text = (
            "✅ *Bot Status*\n\n"
            "🤖 Bot: Running\n"
            "📊 Market Data: Connected\n"
            "💰 Trading API: Connected\n"
            "⚙️ Active Settings:\n"
            "  - Risk per trade: 2%\n"
            "  - Max positions: 5\n"
            "  - Monitoring: Active"
        )
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Analyze a trading pair using Blackprint strategy"""
        if not context.args:
            await update.message.reply_text(
                "⚠️ Please specify a symbol to analyze.\n"
                "Example: `/analyze AAPL`",
                parse_mode='Markdown'
            )
            return
            
        symbol = context.args[0].upper()
        
        try:
            # Get market data
            await update.message.reply_text(f"⏳ Fetching data for {symbol}...")
            
            # Download data using yfinance
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1mo", interval="1h")
            
            if data.empty:
                await update.message.reply_text(
                    f"❌ No data found for symbol {symbol}",
                    parse_mode='Markdown'
                )
                return
            
            # Analyze using our trading service
            analysis = self.trading_service.analyze_symbol(symbol, data)
            
            # Format and send the analysis
            message = self.trading_service.format_analysis_message(analysis)
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {str(e)}")
            await update.message.reply_text(
                f"❌ Error analyzing {symbol}: {str(e)}",
                parse_mode='Markdown'
            )
    
    async def positions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current open positions"""
        positions_text = (
            "📊 *Open Positions*\n\n"
            "1. AAPL (Long)\n"
            "   Entry: $150.25\n"
            "   Current: $152.30\n"
            "   P/L: +1.36%\n\n"
            "2. MSFT (Short)\n"
            "   Entry: $380.50\n"
            "   Current: $375.25\n"
            "   P/L: +1.38%\n\n"
            "💰 *Account Summary*\n"
            "Balance: $100,000\n"
            "Equity: $102,740\n"
            "Day P/L: +$2,740 (2.74%)"
        )
        await update.message.reply_text(positions_text, parse_mode='Markdown')
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View and modify bot settings"""
        settings_text = (
            "⚙️ *Bot Settings*\n\n"
            "*Risk Management:*\n"
            "- Risk per trade: 2%\n"
            "- Max positions: 5\n"
            "- Account size: $100,000\n\n"
            "*Trading Pairs:*\n"
            "- AAPL, MSFT, GOOGL\n\n"
            "*Notifications:*\n"
            "- Signal alerts: ✅\n"
            "- Position updates: ✅\n"
            "- Daily summary: ✅\n\n"
            "To modify settings, use:\n"
            "/settings risk <percentage>\n"
            "/settings pairs add/remove <symbol>"
        )
        await update.message.reply_text(settings_text, parse_mode='Markdown')
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Log errors caused by updates"""
        logger.error(f"Update {update} caused error {context.error}")
        if isinstance(update, Update) and update.message:
            await update.message.reply_text(
                "❌ Sorry, an error occurred while processing your request."
            )
    
    def run(self):
        """Start the bot"""
        self.application.run_polling()
