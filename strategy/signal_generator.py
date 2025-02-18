from decimal import Decimal
from typing import Literal, Optional

PositionType = Literal['long', 'short']

class SignalGenerator:
    """
    Implements signal generation logic from the Blackprint strategy
    """
    
    def check_long_entry(self,
                        close: float,
                        ema_5: float,
                        ema_13: float,
                        ema_34: float,
                        ema_89: float,
                        psar: float,
                        macd_line: Optional[float] = None,
                        signal_line: Optional[float] = None) -> bool:
        """
        Check if conditions for long entry are met
        
        Args:
            close: Current closing price
            ema_5: 5-period EMA
            ema_13: 13-period EMA
            ema_34: 34-period EMA
            ema_89: 89-period EMA
            psar: Current Parabolic SAR value
            macd_line: Optional MACD line value
            signal_line: Optional MACD signal line value
            
        Returns:
            Boolean indicating if long entry conditions are met
        """
        # Check if not in unordered phase
        if (ema_13 < ema_34 and ema_13 > ema_89) or (ema_13 > ema_34 and ema_13 < ema_89):
            return False
            
        # Check if price pulled back to 13 EMA
        if abs(close - ema_13) / ema_13 > 0.001:  # 0.1% threshold
            return False
            
        # Check if price is above 5 EMA
        if close <= ema_5:
            return False
            
        # Check if PSAR is below price
        if psar >= close:
            return False
            
        # Optional MACD confirmation
        if macd_line is not None and signal_line is not None:
            if macd_line <= signal_line:  # Not bullish
                return False
                
        return True
    
    def check_short_entry(self,
                         close: float,
                         ema_13: float,
                         ema_34: float,
                         ema_89: float,
                         psar: float,
                         macd_line: Optional[float] = None,
                         signal_line: Optional[float] = None) -> bool:
        """
        Check if conditions for short entry are met
        
        Args:
            close: Current closing price
            ema_13: 13-period EMA
            ema_34: 34-period EMA
            ema_89: 89-period EMA
            psar: Current Parabolic SAR value
            macd_line: Optional MACD line value
            signal_line: Optional MACD signal line value
            
        Returns:
            Boolean indicating if short entry conditions are met
        """
        # Check if not in unordered phase
        if (ema_13 < ema_34 and ema_13 > ema_89) or (ema_13 > ema_34 and ema_13 < ema_89):
            return False
            
        # Check if price pulled back to 34 EMA
        if abs(close - ema_34) / ema_34 > 0.001:  # 0.1% threshold
            return False
            
        # Check if price is below 13 EMA
        if close >= ema_13:
            return False
            
        # Check if PSAR is above price
        if psar <= close:
            return False
            
        # Optional MACD confirmation
        if macd_line is not None and signal_line is not None:
            if macd_line >= signal_line:  # Not bearish
                return False
                
        return True
    
    def check_exit(self,
                  position_type: PositionType,
                  close: float,
                  psar: float) -> bool:
        """
        Check if position should be exited based on trailing stop
        
        Args:
            position_type: Type of position ('long' or 'short')
            close: Current closing price
            psar: Current Parabolic SAR value
            
        Returns:
            Boolean indicating if position should be exited
        """
        if position_type == 'long':
            return close < psar
        else:  # short position
            return close > psar
