from typing import Optional, Literal

MarketPhase = Literal['unordered', 'emerging', 'trending']

class MarketPhaseDetector:
    """
    Implements the market phase detection logic from the Blackprint strategy
    """
    
    def detect_phase(self, 
                    ema_13: float,
                    ema_34: float,
                    ema_89: float,
                    prev_ema_13: Optional[float] = None,
                    prev_ema_34: Optional[float] = None,
                    prev_ema_89: Optional[float] = None) -> MarketPhase:
        """
        Detect the current market phase based on EMA relationships
        
        Args:
            ema_13: Current 13-period EMA value
            ema_34: Current 34-period EMA value
            ema_89: Current 89-period EMA value
            prev_ema_13: Previous 13-period EMA value (for trend confirmation)
            prev_ema_34: Previous 34-period EMA value (for trend confirmation)
            prev_ema_89: Previous 89-period EMA value (for trend confirmation)
            
        Returns:
            Current market phase: 'unordered', 'emerging', or 'trending'
        """
        # Check for unordered phase
        if (ema_13 < ema_34 and ema_13 > ema_89) or (ema_13 > ema_34 and ema_13 < ema_89):
            return 'unordered'
            
        # Check for emerging/trending phase conditions
        if ema_13 > ema_89 and ema_13 > ema_34:
            # If we have previous values, we can check for trending phase
            if all(v is not None for v in [prev_ema_13, prev_ema_34, prev_ema_89]):
                # Confirm trend continuation
                if (ema_13 > prev_ema_13 and 
                    ema_34 > prev_ema_34 and 
                    ema_89 > prev_ema_89):
                    return 'trending'
            return 'emerging'
            
        # Default to unordered if no other conditions met
        return 'unordered'
    
    def is_pullback_to_ema(self,
                          price: float,
                          ema: float,
                          threshold_percent: float = 0.1) -> bool:
        """
        Check if price has pulled back to a specific EMA
        
        Args:
            price: Current price
            ema: EMA value to check against
            threshold_percent: Percentage threshold for pullback detection
            
        Returns:
            Boolean indicating if price has pulled back to EMA
        """
        threshold = ema * threshold_percent
        return abs(price - ema) <= threshold
