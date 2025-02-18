import pandas as pd
import numpy as np
from typing import List, Dict

class Indicators:
    """
    Implementation of technical indicators used in the Blackprint strategy
    """
    
    @staticmethod
    def calculate_emas(price_data: pd.Series, periods: List[int] = [5, 7, 9, 11, 13, 34, 89]) -> pd.DataFrame:
        """
        Calculate multiple EMAs for given periods
        
        Args:
            price_data: Series of closing prices
            periods: List of EMA periods to calculate
            
        Returns:
            DataFrame with EMA values for each period
        """
        results = pd.DataFrame(index=price_data.index)
        
        for period in periods:
            results[f'ema_{period}'] = price_data.ewm(span=period, adjust=False).mean()
            
        return results
    
    @staticmethod
    def calculate_psar(data: pd.DataFrame, af_start: float = 0.02, af_max: float = 0.2) -> pd.DataFrame:
        """
        Calculate Parabolic SAR
        
        Args:
            data: DataFrame with 'high' and 'low' columns
            af_start: Starting acceleration factor
            af_max: Maximum acceleration factor
            
        Returns:
            DataFrame with PSAR values
        """
        high, low = data['high'], data['low']
        
        # Initialize
        psar = pd.Series(index=data.index, dtype=float)
        af = pd.Series(index=data.index, dtype=float)
        ep = pd.Series(index=data.index, dtype=float)
        trend = pd.Series(index=data.index, dtype=bool)
        
        # Set initial values
        trend.iloc[0] = True
        psar.iloc[0] = low.iloc[0]
        ep.iloc[0] = high.iloc[0]
        af.iloc[0] = af_start
        
        # Calculate PSAR values
        for i in range(1, len(data)):
            psar.iloc[i] = psar.iloc[i-1] + af.iloc[i-1] * (ep.iloc[i-1] - psar.iloc[i-1])
            
            if trend.iloc[i-1]:  # Uptrend
                if low.iloc[i] > psar.iloc[i]:
                    trend.iloc[i] = True
                    if high.iloc[i] > ep.iloc[i-1]:
                        ep.iloc[i] = high.iloc[i]
                        af.iloc[i] = min(af.iloc[i-1] + af_start, af_max)
                    else:
                        ep.iloc[i] = ep.iloc[i-1]
                        af.iloc[i] = af.iloc[i-1]
                else:
                    trend.iloc[i] = False
                    psar.iloc[i] = ep.iloc[i-1]
                    ep.iloc[i] = low.iloc[i]
                    af.iloc[i] = af_start
            else:  # Downtrend
                if high.iloc[i] < psar.iloc[i]:
                    trend.iloc[i] = False
                    if low.iloc[i] < ep.iloc[i-1]:
                        ep.iloc[i] = low.iloc[i]
                        af.iloc[i] = min(af.iloc[i-1] + af_start, af_max)
                    else:
                        ep.iloc[i] = ep.iloc[i-1]
                        af.iloc[i] = af.iloc[i-1]
                else:
                    trend.iloc[i] = True
                    psar.iloc[i] = ep.iloc[i-1]
                    ep.iloc[i] = high.iloc[i]
                    af.iloc[i] = af_start
        
        return pd.DataFrame({'psar': psar, 'trend': trend}, index=data.index)
    
    @staticmethod
    def calculate_macd(price_data: pd.Series, fast_period: int = 12, 
                      slow_period: int = 26, signal_period: int = 9) -> pd.DataFrame:
        """
        Calculate MACD indicator
        
        Args:
            price_data: Series of closing prices
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period
            
        Returns:
            DataFrame with MACD line, signal line, and histogram
        """
        # Calculate MACD components
        fast_ema = price_data.ewm(span=fast_period, adjust=False).mean()
        slow_ema = price_data.ewm(span=slow_period, adjust=False).mean()
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return pd.DataFrame({
            'macd_line': macd_line,
            'signal_line': signal_line,
            'histogram': histogram
        }, index=price_data.index)
