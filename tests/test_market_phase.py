import pytest
import pandas as pd
import numpy as np
from strategy.market_phase import MarketPhaseDetector

@pytest.fixture
def sample_ema_data():
    """Create sample EMA data for testing market phases"""
    return pd.DataFrame({
        'ema_13': np.random.random(100) * 100,
        'ema_34': np.random.random(100) * 100,
        'ema_89': np.random.random(100) * 100
    })

def test_unordered_phase_detection(sample_ema_data):
    """Test unordered phase detection"""
    detector = MarketPhaseDetector()
    
    # Create specific case for unordered phase
    sample_ema_data.loc[0, 'ema_13'] = 50
    sample_ema_data.loc[0, 'ema_34'] = 60
    sample_ema_data.loc[0, 'ema_89'] = 40
    
    phase = detector.detect_phase(
        ema_13=sample_ema_data.loc[0, 'ema_13'],
        ema_34=sample_ema_data.loc[0, 'ema_34'],
        ema_89=sample_ema_data.loc[0, 'ema_89']
    )
    
    assert phase == 'unordered'

def test_emerging_phase_detection(sample_ema_data):
    """Test emerging phase detection"""
    detector = MarketPhaseDetector()
    
    # Create specific case for emerging phase
    sample_ema_data.loc[0, 'ema_13'] = 60
    sample_ema_data.loc[0, 'ema_34'] = 50
    sample_ema_data.loc[0, 'ema_89'] = 40
    
    phase = detector.detect_phase(
        ema_13=sample_ema_data.loc[0, 'ema_13'],
        ema_34=sample_ema_data.loc[0, 'ema_34'],
        ema_89=sample_ema_data.loc[0, 'ema_89']
    )
    
    assert phase == 'emerging'

def test_trending_phase_detection(sample_ema_data):
    """Test trending phase detection"""
    detector = MarketPhaseDetector()
    
    # Create specific case for trending phase
    # Similar to emerging but with additional trend confirmation
    sample_ema_data.loc[0, 'ema_13'] = 60
    sample_ema_data.loc[0, 'ema_34'] = 50
    sample_ema_data.loc[0, 'ema_89'] = 40
    
    # Previous values showing consistent trend
    sample_ema_data.loc[1, 'ema_13'] = 59
    sample_ema_data.loc[1, 'ema_34'] = 49
    sample_ema_data.loc[1, 'ema_89'] = 39
    
    phase = detector.detect_phase(
        ema_13=sample_ema_data.loc[0, 'ema_13'],
        ema_34=sample_ema_data.loc[0, 'ema_34'],
        ema_89=sample_ema_data.loc[0, 'ema_89'],
        prev_ema_13=sample_ema_data.loc[1, 'ema_13'],
        prev_ema_34=sample_ema_data.loc[1, 'ema_34'],
        prev_ema_89=sample_ema_data.loc[1, 'ema_89']
    )
    
    assert phase == 'trending'
