import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from telegram import Update, Message, Chat, User, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, ContextTypes
from bot.telegram_bot import BlackprintBot
from bot.market_phases import MarketIndex, MarketPhase
from datetime import datetime
import pytz

@pytest.fixture
def mock_alpaca_data():
    """Mock Alpaca data responses"""
    mock_data = MagicMock()
    mock_data.get_bars.return_value = AsyncMock()
    return mock_data

@pytest.fixture
def mock_market_state():
    """Mock market state responses"""
    mock_state = MagicMock()
    mock_state.get_current_state.return_value = {
        'symbol': 'AAPL',
        'phase': MarketPhase.TRENDING,
        'timestamp': datetime.now(pytz.UTC),
        'indicators': {
            'ema_20': 150.0,
            'ema_50': 145.0,
            'ema_200': 140.0
        }
    }
    mock_state.format_market_state.return_value = "Market Analysis for AAPL"
    return mock_state

@pytest.fixture
def bot(mock_alpaca_data, mock_market_state):
    """Create a bot instance for testing"""
    token = "test_token"
    with patch('telegram.ext.Application.builder') as mock_builder:
        mock_app = Mock()
        mock_builder.return_value.token.return_value.build.return_value = mock_app
        with patch('bot.telegram_bot.AlpacaDataManager') as mock_data_manager:
            mock_data_manager.return_value = mock_alpaca_data
            with patch('bot.telegram_bot.MarketStateManager') as mock_state_manager:
                mock_state_manager.return_value = mock_market_state
                bot = BlackprintBot(token)
                return bot

@pytest.fixture
def update():
    """Create a mock update object"""
    update = Mock(spec=Update)
    update.message = Mock(spec=Message)
    update.message.chat = Mock(spec=Chat)
    update.message.chat.id = 123
    update.effective_user = Mock(spec=User)
    update.effective_user.id = 123
    update.message.reply_text = AsyncMock()
    return update

@pytest.fixture
def context():
    """Create a mock context object"""
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    return context

@pytest.mark.asyncio
async def test_main_keyboard(bot):
    """Test main keyboard creation"""
    keyboard = bot.get_main_keyboard()
    assert isinstance(keyboard, ReplyKeyboardMarkup)
    
    # Check keyboard structure
    buttons = keyboard.keyboard
    assert len(buttons) == 4  # 4 rows
    assert len(buttons[0]) == 2  # 2 buttons in first row
    
    # Check button commands
    assert buttons[0][0].text == "/analyze"
    assert buttons[0][1].text == "/historical"

@pytest.mark.asyncio
async def test_symbol_keyboard(bot):
    """Test symbol keyboard creation"""
    keyboard = bot.get_symbol_keyboard()
    assert isinstance(keyboard, InlineKeyboardMarkup)
    
    # Check keyboard structure
    buttons = keyboard.inline_keyboard
    assert len(buttons) > 0
    
    # Check first symbol button
    first_button = buttons[0][0]
    assert first_button.callback_data == "analyze_AAPL"
    assert first_button.text == "AAPL"

@pytest.mark.asyncio
async def test_timeframe_keyboard(bot):
    """Test timeframe keyboard creation"""
    keyboard = bot.get_timeframe_keyboard()
    assert isinstance(keyboard, InlineKeyboardMarkup)
    
    # Check keyboard structure
    buttons = keyboard.inline_keyboard
    assert len(buttons) > 0
    
    # Check first timeframe button
    first_button = buttons[0][0]
    assert first_button.callback_data.startswith("timeframe_")

@pytest.mark.asyncio
async def test_index_keyboard(bot):
    """Test index keyboard creation"""
    keyboard = bot.get_index_keyboard()
    assert isinstance(keyboard, InlineKeyboardMarkup)
    
    # Check keyboard structure
    buttons = keyboard.inline_keyboard
    assert len(buttons) > 0
    
    # Check first index button
    first_button = buttons[0][0]
    assert first_button.callback_data.startswith("index_")

@pytest.mark.asyncio
async def test_start_command(bot, update, context):
    """Test start command response"""
    # Call start command
    await bot.start_command(update, context)
    
    # Check that reply_text was called twice (welcome message and symbol keyboard)
    assert update.message.reply_text.call_count == 2
    
    # Check that keyboards were included in responses
    first_call_kwargs = update.message.reply_text.call_args_list[0][1]
    second_call_kwargs = update.message.reply_text.call_args_list[1][1]
    
    assert isinstance(first_call_kwargs['reply_markup'], ReplyKeyboardMarkup)
    assert isinstance(second_call_kwargs['reply_markup'], InlineKeyboardMarkup)

@pytest.mark.asyncio
async def test_button_callback(bot, update, context):
    """Test button callback handling"""
    # Setup callback query mock
    update.callback_query = Mock()
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    
    # Test analyze button callback
    update.callback_query.data = "analyze_AAPL"
    with patch.object(bot, 'analyze_command', new_callable=AsyncMock) as mock_analyze:
        await bot.button_callback(update, context)
        assert mock_analyze.called
        assert context.args == ["AAPL"]
    
    # Test timeframe button callback
    update.callback_query.data = "timeframe_15Min"
    with patch.object(bot, 'set_candle_command', new_callable=AsyncMock) as mock_candle:
        await bot.button_callback(update, context)
        assert mock_candle.called
        assert context.args == ["15Min"]
    
    # Test index button callback
    update.callback_query.data = "index_US30"
    with patch.object(bot, 'set_index_command', new_callable=AsyncMock) as mock_index:
        await bot.button_callback(update, context)
        assert mock_index.called
        assert context.args == ["US30"]

@pytest.mark.asyncio
async def test_analyze_command_with_buttons(bot, update, context):
    """Test analyze command with symbol selection"""
    # Test without symbol (should show symbol keyboard)
    await bot.analyze_command(update, context)
    
    # Check that symbol keyboard was shown
    update.message.reply_text.assert_called_once()
    call_kwargs = update.message.reply_text.call_args[1]
    assert isinstance(call_kwargs['reply_markup'], InlineKeyboardMarkup)

@pytest.mark.asyncio
async def test_analyze_command_with_symbol(bot, update, context):
    """Test analyze command with a specific symbol"""
    context.args = ["AAPL"]
    await bot.analyze_command(update, context)
    
    # Check that market analysis was shown
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0]
    assert "Market Analysis for AAPL" in str(call_args)

@pytest.mark.asyncio
async def test_set_candle_command_with_buttons(bot, update, context):
    """Test setcandle command with timeframe selection"""
    # Test without timeframe (should show timeframe keyboard)
    await bot.set_candle_command(update, context)
    
    # Check that timeframe keyboard was shown
    update.message.reply_text.assert_called_once()
    call_kwargs = update.message.reply_text.call_args[1]
    assert isinstance(call_kwargs['reply_markup'], InlineKeyboardMarkup)

@pytest.mark.asyncio
async def test_set_index_command_with_buttons(bot, update, context):
    """Test setindex command with index selection"""
    # Test without index (should show index keyboard)
    await bot.set_index_command(update, context)
    
    # Check that index keyboard was shown
    update.message.reply_text.assert_called_once()
    call_kwargs = update.message.reply_text.call_args[1]
    assert isinstance(call_kwargs['reply_markup'], InlineKeyboardMarkup)
