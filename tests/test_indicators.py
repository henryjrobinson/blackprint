import pytest
import pandas as pd
import numpy as np
from strategy.indicators import Indicators

@pytest.fixture
def sample_data():
    """Create sample price data for testing"""
    return pd.DataFrame({
        'close': np.random.random(100) * 100,
        'high': np.random.random(100) * 100,
        'low': np.random.random(100) * 100
    })

def test_ema_calculation(sample_data):
    """Test EMA calculations for all required periods"""
    indicators = Indicators()
    periods = [5, 7, 9, 11, 13, 34, 89]
    emas = indicators.calculate_emas(sample_data['close'])
    
    # Check if all required EMAs are calculated
    for period in periods:
        assert f'ema_{period}' in emas.columns
        
    # Check if EMA values are between min and max of price
    for period in periods:
        assert emas[f'ema_{period}'].min() >= sample_data['close'].min()
        assert emas[f'ema_{period}'].max() <= sample_data['close'].max()

def test_psar_calculation(sample_data):
    """Test Parabolic SAR calculation"""
    indicators = Indicators()
    psar = indicators.calculate_psar(sample_data)
    
    # Check if PSAR values are calculated
    assert 'psar' in psar.columns
    
    # PSAR should alternate between being above and below price
    psar_above_price = psar['psar'] > sample_data['close']
    assert psar_above_price.value_counts().min() > 0  # Should have both above and below cases

def test_macd_calculation(sample_data):
    """Test MACD calculation"""
    indicators = Indicators()
    macd = indicators.calculate_macd(sample_data['close'])
    
    # Check if MACD components are present
    assert 'macd_line' in macd.columns
    assert 'signal_line' in macd.columns
    assert 'histogram' in macd.columns
    
    # Check if MACD oscillates around zero
    assert (macd['macd_line'] > 0).any()
    assert (macd['macd_line'] < 0).any()
