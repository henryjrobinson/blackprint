import pandas as pd
import pandas_ta as ta
from typing import Tuple, List

class Indicators:
    """Technical indicators for market analysis"""
    
    def calculate_emas(self, data: pd.Series, periods: List[int] = [5, 7, 9, 11, 13, 34, 89]) -> pd.DataFrame:
        """Calculate EMAs for the given periods."""
        df = pd.DataFrame()
        for period in periods:
            df[f'ema_{period}'] = ta.ema(data, length=period)
        return df

    def calculate_psar(self, data: pd.DataFrame, acceleration: float = 0.02, maximum: float = 0.2) -> pd.DataFrame:
        """Calculate Parabolic SAR."""
        df = data.copy()
        psar = ta.psar(df['high'], df['low'], af=acceleration, max_af=maximum)
        df['psar'] = psar['PSARl_0.02_0.2']  # Long signals
        return df

    def calculate_macd(self, data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """Calculate MACD indicator."""
        df = pd.DataFrame()
        macd = ta.macd(data, fast=fast, slow=slow, signal=signal)
        df['macd_line'] = macd['MACD_12_26_9']
        df['signal_line'] = macd['MACDs_12_26_9']
        df['histogram'] = macd['MACDh_12_26_9']
        return df

    def calculate_rsi(self, data: pd.Series, period: int = 14) -> pd.DataFrame:
        """Calculate RSI indicator."""
        df = pd.DataFrame()
        df['rsi'] = ta.rsi(data, length=period)
        return df

    def get_market_phase(self, data: pd.DataFrame) -> str:
        """
        Determine the market phase based on EMA relationships.
        Returns: 'BULLISH', 'BEARISH', or 'CHOPPY'
        """
        last_row = data.iloc[-1]
        ema_13 = last_row['ema_13']
        ema_34 = last_row['ema_34']
        ema_89 = last_row['ema_89']
        
        if ema_13 > ema_34 > ema_89:
            return 'BULLISH'
        elif ema_13 < ema_34 < ema_89:
            return 'BEARISH'
        else:
            return 'CHOPPY'
