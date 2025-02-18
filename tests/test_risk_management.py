import pytest
from risk.management import RiskManager
from decimal import Decimal

@pytest.fixture
def risk_manager():
    return RiskManager(
        account_size=100000,
        risk_per_trade=0.02,  # 2% risk per trade
        max_positions=5
    )

def test_stop_loss_calculation():
    """Test stop loss calculations for different timeframes"""
    risk_manager = RiskManager(account_size=100000)
    
    # Test stop loss distances as per Blackprint specification
    assert risk_manager.get_stop_loss_pips('5min') == 15
    assert risk_manager.get_stop_loss_pips('15min') == 20
    assert risk_manager.get_stop_loss_pips('1hour') == 30
    assert risk_manager.get_stop_loss_pips('4hour') == 50

def test_position_size_calculation(risk_manager):
    """Test position size calculation based on risk parameters"""
    # Example: Entry at 100, Stop at 99 (100 pip stop)
    position_size = risk_manager.calculate_position_size(
        entry_price=Decimal('100.00'),
        stop_loss_price=Decimal('99.00'),
        pip_value=Decimal('0.0001')
    )
    
    # Expected position size calculation:
    # Account size: 100,000
    # Risk amount: 2,000 (2%)
    # Risk per pip: 2,000/100 = 20
    # Position size should be 20 / pip_value
    expected_size = Decimal('20') / Decimal('0.0001')
    assert position_size == expected_size

def test_max_position_validation(risk_manager):
    """Test validation of maximum open positions"""
    # Simulate existing positions
    current_positions = 4
    assert risk_manager.can_open_position(current_positions) == True
    
    current_positions = 5
    assert risk_manager.can_open_position(current_positions) == False

def test_risk_per_trade_validation(risk_manager):
    """Test validation of risk per trade limits"""
    # Test normal risk (2%)
    assert risk_manager.validate_trade_risk(
        risk_amount=2000,  # 2% of 100,000
        account_size=100000
    ) == True
    
    # Test excessive risk (6%)
    assert risk_manager.validate_trade_risk(
        risk_amount=6000,  # 6% of 100,000
        account_size=100000
    ) == False
