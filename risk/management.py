from decimal import Decimal
from typing import Dict, Literal

TimeFrame = Literal['5min', '15min', '1hour', '4hour']

class RiskManager:
    """
    Implements risk management rules from the Blackprint strategy
    """
    
    def __init__(self, account_size: float, risk_per_trade: float = 0.02, max_positions: int = 5):
        """
        Initialize risk manager
        
        Args:
            account_size: Current account size in base currency
            risk_per_trade: Maximum risk per trade as decimal (default 0.02 = 2%)
            max_positions: Maximum number of concurrent positions allowed
        """
        self.account_size = Decimal(str(account_size))
        self.risk_per_trade = Decimal(str(risk_per_trade))
        self.max_positions = max_positions
        
        # Stop loss pips by timeframe as per Blackprint specification
        self.stop_loss_pips: Dict[TimeFrame, int] = {
            '5min': 15,
            '15min': 20,
            '1hour': 30,
            '4hour': 50
        }
    
    def get_stop_loss_pips(self, timeframe: TimeFrame) -> int:
        """
        Get stop loss distance in pips for given timeframe
        
        Args:
            timeframe: Trading timeframe
            
        Returns:
            Stop loss distance in pips
        """
        return self.stop_loss_pips[timeframe]
    
    def calculate_position_size(self, entry_price: Decimal, 
                              stop_loss_price: Decimal,
                              pip_value: Decimal) -> Decimal:
        """
        Calculate position size based on risk parameters
        
        Args:
            entry_price: Entry price of the trade
            stop_loss_price: Stop loss price
            pip_value: Value of one pip in the trading instrument
            
        Returns:
            Position size in units of the trading instrument
        """
        risk_amount = self.account_size * self.risk_per_trade
        price_distance = abs(entry_price - stop_loss_price)
        pips_at_risk = price_distance / pip_value
        
        # Calculate risk per pip
        risk_per_pip = risk_amount / pips_at_risk
        
        # Position size = Risk per pip / Pip value
        position_size = risk_per_pip / pip_value
        
        return position_size.quantize(Decimal('0.01'))
    
    def can_open_position(self, current_positions: int) -> bool:
        """
        Check if new position can be opened based on maximum positions limit
        
        Args:
            current_positions: Number of currently open positions
            
        Returns:
            Boolean indicating if new position can be opened
        """
        return current_positions < self.max_positions
    
    def validate_trade_risk(self, risk_amount: Decimal, account_size: Decimal) -> bool:
        """
        Validate if trade risk is within acceptable limits
        
        Args:
            risk_amount: Amount at risk for the trade
            account_size: Current account size
            
        Returns:
            Boolean indicating if trade risk is acceptable
        """
        # Convert inputs to Decimal if they aren't already
        risk_amount = Decimal(str(risk_amount)) if not isinstance(risk_amount, Decimal) else risk_amount
        account_size = Decimal(str(account_size)) if not isinstance(account_size, Decimal) else account_size
        
        risk_percentage = risk_amount / account_size
        return risk_percentage <= self.risk_per_trade
