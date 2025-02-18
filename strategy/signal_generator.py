import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Optional, Tuple, Dict, Any

class SignalGenerator:
    def __init__(self, ema_fast: int = 9, ema_slow: int = 21, rsi_period: int = 14):
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.rsi_period = rsi_period

    def generate_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signals based on technical indicators.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Dict with signal information
        """
        # Calculate indicators
        data['ema_fast'] = ta.ema(data['close'], length=self.ema_fast)
        data['ema_slow'] = ta.ema(data['close'], length=self.ema_slow)
        data['rsi'] = ta.rsi(data['close'], length=self.rsi_period)
        
        # Get latest values
        current_close = data['close'].iloc[-1]
        current_ema_fast = data['ema_fast'].iloc[-1]
        current_ema_slow = data['ema_slow'].iloc[-1]
        current_rsi = data['rsi'].iloc[-1]
        
        # Determine market trend
        market_trend = "BULLISH" if current_ema_fast > current_ema_slow else "BEARISH"
        
        # Generate signals
        long_entry = (
            market_trend == "BULLISH" and
            current_rsi < 70 and
            current_close > current_ema_fast
        )
        
        short_entry = (
            market_trend == "BEARISH" and
            current_rsi > 30 and
            current_close < current_ema_fast
        )
        
        return {
            "market_trend": market_trend,
            "long_entry": long_entry,
            "short_entry": short_entry,
            "current_close": current_close,
            "current_rsi": current_rsi,
            "ema_fast": current_ema_fast,
            "ema_slow": current_ema_slow,
            "timestamp": data.index[-1]
        }
