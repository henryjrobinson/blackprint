import pytest
import pandas as pd
import numpy as np
from strategy.signal_generator import SignalGenerator
from strategy.market_phase import MarketPhaseDetector

@pytest.fixture
def signal_generator():
    return SignalGenerator()

@pytest.fixture
def sample_data():
    """Create sample market data for testing"""
    return pd.DataFrame({
        'close': np.random.random(100) * 100,
        'high': np.random.random(100) * 100,
        'low': np.random.random(100) * 100,
        'ema_5': np.random.random(100) * 100,
        'ema_13': np.random.random(100) * 100,
        'ema_34': np.random.random(100) * 100,
        'ema_89': np.random.random(100) * 100,
        'psar': np.random.random(100) * 100,
        'macd_line': np.random.random(100) - 0.5,
        'signal_line': np.random.random(100) - 0.5,
    })

def test_long_entry_signal(signal_generator, sample_data):
    """Test long entry signal generation"""
    # Set up conditions for long entry
    data = sample_data.copy()
    idx = 0
    
    # Set EMAs for non-unordered phase
    data.loc[idx, 'ema_13'] = 60
    data.loc[idx, 'ema_34'] = 55
    data.loc[idx, 'ema_89'] = 50
    
    # Price pulled back to 13 EMA
    data.loc[idx, 'close'] = 60
    
    # Price above 5 EMA
    data.loc[idx, 'ema_5'] = 59
    
    # PSAR below price
    data.loc[idx, 'psar'] = 58
    
    # MACD bullish
    data.loc[idx, 'macd_line'] = 0.5
    data.loc[idx, 'signal_line'] = 0.3
    
    signal = signal_generator.check_long_entry(
        close=data.loc[idx, 'close'],
        ema_5=data.loc[idx, 'ema_5'],
        ema_13=data.loc[idx, 'ema_13'],
        ema_34=data.loc[idx, 'ema_34'],
        ema_89=data.loc[idx, 'ema_89'],
        psar=data.loc[idx, 'psar'],
        macd_line=data.loc[idx, 'macd_line'],
        signal_line=data.loc[idx, 'signal_line']
    )
    
    assert signal == True

def test_short_entry_signal(signal_generator, sample_data):
    """Test short entry signal generation"""
    # Set up conditions for short entry
    data = sample_data.copy()
    idx = 0
    
    # Set EMAs for non-unordered phase
    data.loc[idx, 'ema_13'] = 40
    data.loc[idx, 'ema_34'] = 45
    data.loc[idx, 'ema_89'] = 50
    
    # Price pulled back to 34 EMA
    data.loc[idx, 'close'] = 45
    
    # Price below 13 EMA
    data.loc[idx, 'ema_13'] = 46
    
    # PSAR above price
    data.loc[idx, 'psar'] = 47
    
    # MACD bearish
    data.loc[idx, 'macd_line'] = -0.5
    data.loc[idx, 'signal_line'] = -0.3
    
    signal = signal_generator.check_short_entry(
        close=data.loc[idx, 'close'],
        ema_13=data.loc[idx, 'ema_13'],
        ema_34=data.loc[idx, 'ema_34'],
        ema_89=data.loc[idx, 'ema_89'],
        psar=data.loc[idx, 'psar'],
        macd_line=data.loc[idx, 'macd_line'],
        signal_line=data.loc[idx, 'signal_line']
    )
    
    assert signal == True

def test_exit_signal(signal_generator, sample_data):
    """Test exit signal generation"""
    # Test trailing stop using PSAR
    data = sample_data.copy()
    idx = 0
    
    # Set up long position exit condition
    data.loc[idx, 'psar'] = 55
    data.loc[idx, 'close'] = 50
    
    exit_signal = signal_generator.check_exit(
        position_type='long',
        close=data.loc[idx, 'close'],
        psar=data.loc[idx, 'psar']
    )
    
    assert exit_signal == True
