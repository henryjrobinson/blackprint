from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum

class MarketPhase(Enum):
    UNORDERED = "unordered"
    EMERGING = "emerging"
    TRENDING = "trending"
    PULLBACK = "pullback"

class MarketIndex(Enum):
    US30 = "^DJI"      # Dow Jones Industrial Average
    SPX = "^GSPC"      # S&P 500
    NDX = "^IXIC"      # Nasdaq Composite
    RUT = "^RUT"       # Russell 2000
    VIX = "^VIX"       # Volatility Index
    FTSE = "^FTSE"     # FTSE 100
    DAX = "^GDAXI"     # German DAX
    NIKKEI = "^N225"   # Nikkei 225

@dataclass
class PhaseDetectionConfig:
    candle_size: str = "15Min"  # Default 15-minute candles
    fast_ema: int = 13
    medium_ema: int = 34
    slow_ema: int = 89
    pullback_threshold: float = 0.382  # Fibonacci retracement level
    index: MarketIndex = MarketIndex.US30  # Default to US30 (Dow Jones)

class MarketPhaseDetector:
    def __init__(self, config: PhaseDetectionConfig = None):
        self.config = config or PhaseDetectionConfig()
        self.index_data = None
        self.last_index_update = None
        
    def set_index(self, index: MarketIndex):
        """Update the reference index"""
        self.config.index = index
        self.index_data = None  # Reset cached data
        
    def get_index_symbol(self) -> str:
        """Get the current index symbol"""
        return self.config.index.value
        
    def update_index_data(self, data: pd.DataFrame):
        """Update the cached index data"""
        self.index_data = data
        self.last_index_update = pd.Timestamp.now()
        
    def calculate_emas(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate EMAs for phase detection"""
        df = data.copy()
        df[f'ema_{self.config.fast_ema}'] = df['close'].ewm(span=self.config.fast_ema, adjust=False).mean()
        df[f'ema_{self.config.medium_ema}'] = df['close'].ewm(span=self.config.medium_ema, adjust=False).mean()
        df[f'ema_{self.config.slow_ema}'] = df['close'].ewm(span=self.config.slow_ema, adjust=False).mean()
        return df
    
    def detect_unordered_phase(self, df: pd.DataFrame) -> bool:
        """Detect unordered market phase - 13 EMA between 34 and 89 EMAs"""
        # Check last 5 periods for persistent unordered conditions
        last_n = 5
        fast = df[f'ema_{self.config.fast_ema}'].iloc[-last_n:]
        medium = df[f'ema_{self.config.medium_ema}'].iloc[-last_n:]
        slow = df[f'ema_{self.config.slow_ema}'].iloc[-last_n:]
        
        # Count how many periods fast EMA is between medium and slow EMAs
        between_count = 0
        for i in range(last_n):
            if ((fast.iloc[i] < medium.iloc[i] and fast.iloc[i] > slow.iloc[i]) or 
                (fast.iloc[i] > medium.iloc[i] and fast.iloc[i] < slow.iloc[i])):
                between_count += 1
                
        between_emas = between_count >= 3  # Most periods should show between condition
        
        # Check for choppy price action
        recent_close = df['close'].iloc[-20:]  # Last 20 periods
        price_volatility = recent_close.std() / recent_close.mean()
        high_volatility = price_volatility > 0.05  # Increased threshold for high volatility
        
        # Also check for lack of clear trend
        ema_spread = abs(medium.iloc[-1] - slow.iloc[-1]) / slow.iloc[-1]
        no_trend = ema_spread < 0.01  # EMAs are close together
        
        return between_emas or (high_volatility and no_trend)
    
    def detect_emerging_phase(self, df: pd.DataFrame) -> bool:
        """Detect emerging market phase - 13 EMA above both 34 and 89 EMAs"""
        fast = df[f'ema_{self.config.fast_ema}']
        medium = df[f'ema_{self.config.medium_ema}']
        slow = df[f'ema_{self.config.slow_ema}']
        
        # Check last 3 periods to confirm emergence
        last_n = 3
        emerging_conditions = (
            (fast.iloc[-last_n:] > medium.iloc[-last_n:]).all() and
            (fast.iloc[-last_n:] > slow.iloc[-last_n:]).all() and
            (fast.iloc[-1] - fast.iloc[-last_n]) > 0  # Upward slope
        )
        
        return emerging_conditions
    
    def detect_trending_phase(self, df: pd.DataFrame) -> bool:
        """
        Detect trending market phase - Emerging phase with additional confirmation
        Requires alignment of EMAs and price momentum
        """
        if not self.detect_emerging_phase(df):
            return False
            
        # Check EMA alignment (fast > medium > slow) for multiple periods
        last_n = 5
        fast = df[f'ema_{self.config.fast_ema}'].iloc[-last_n:]
        medium = df[f'ema_{self.config.medium_ema}'].iloc[-last_n:]
        slow = df[f'ema_{self.config.slow_ema}'].iloc[-last_n:]
        
        # Check consistent alignment and increasing spread
        aligned = (fast > medium).all() and (medium > slow).all()
        spread_increasing = (fast - slow).diff().mean() > 0
        
        # Also check index alignment if we have index data
        index_aligned = True
        if self.index_data is not None:
            index_emas = self.calculate_emas(self.index_data)
            index_fast = index_emas[f'ema_{self.config.fast_ema}'].iloc[-last_n:]
            index_medium = index_emas[f'ema_{self.config.medium_ema}'].iloc[-last_n:]
            index_slow = index_emas[f'ema_{self.config.slow_ema}'].iloc[-last_n:]
            index_aligned = (index_fast > index_medium).all() and (index_medium > index_slow).all()
        
        return aligned and spread_increasing and index_aligned
    
    def detect_pullback(self, df: pd.DataFrame) -> bool:
        """
        Detect pullback conditions using price retracement to EMAs
        and Fibonacci retracement levels
        """
        # First confirm we were in a trend
        was_trending = False
        if len(df) > 30:  # Need enough data to look back
            prev_data = df.iloc[:-15].copy()  # Look at data before pullback
            was_trending = self.detect_trending_phase(prev_data)
        
        if not was_trending:
            return False
        
        # Find trend start and peak
        trend_start = df['low'].iloc[:-15].min()  # Approximate trend start
        peak = df['high'].iloc[:-15].max()  # Peak before pullback
        current_price = df['close'].iloc[-1]
        
        # Calculate retracement from trend start to peak
        trend_range = peak - trend_start
        if trend_range == 0:
            return False
            
        retracement = (peak - current_price) / trend_range
        
        # Check if price is near EMAs with wider threshold
        fast_ema = df[f'ema_{self.config.fast_ema}'].iloc[-1]
        medium_ema = df[f'ema_{self.config.medium_ema}'].iloc[-1]
        
        price_near_ema = (
            abs(current_price - fast_ema) / fast_ema < 0.02 or  # Within 2%
            abs(current_price - medium_ema) / medium_ema < 0.02
        )
        
        # Check for bullish momentum over last 5 bars
        recent_close = df['close'].iloc[-5:]
        momentum_bullish = recent_close.diff().mean() > 0
        
        # Check if EMAs are still in bullish alignment
        last_n = 3
        fast = df[f'ema_{self.config.fast_ema}'].iloc[-last_n:]
        medium = df[f'ema_{self.config.medium_ema}'].iloc[-last_n:]
        slow = df[f'ema_{self.config.slow_ema}'].iloc[-last_n:]
        emas_bullish = (medium > slow).all()  # Medium above slow shows trend intact
        
        # Check index condition if available
        index_supports_pullback = True
        if self.index_data is not None:
            index_emas = self.calculate_emas(self.index_data)
            index_price = self.index_data['close'].iloc[-1]
            index_fast_ema = index_emas[f'ema_{self.config.fast_ema}'].iloc[-1]
            index_supports_pullback = (
                index_price > index_fast_ema and  # Index still in uptrend
                (index_price - index_fast_ema) / index_price < 0.01  # But not extended
            )
        
        valid_retracement = 0.236 <= retracement <= 0.618  # Fibonacci levels
        return (price_near_ema and valid_retracement and 
                momentum_bullish and emas_bullish and 
                index_supports_pullback)
    
    def detect_phase(self, data: pd.DataFrame) -> Tuple[MarketPhase, Dict]:
        """
        Detect the current market phase and return relevant metrics
        """
        df = self.calculate_emas(data)
        
        # Add index metrics
        index_metrics = {}
        if self.index_data is not None:
            index_emas = self.calculate_emas(self.index_data)
            index_metrics = {
                "index_symbol": self.config.index.name,
                "index_price": self.index_data['close'].iloc[-1],
                "index_ema_fast": index_emas[f'ema_{self.config.fast_ema}'].iloc[-1],
                "index_ema_medium": index_emas[f'ema_{self.config.medium_ema}'].iloc[-1],
                "index_ema_slow": index_emas[f'ema_{self.config.slow_ema}'].iloc[-1]
            }
        
        # Check phases in order of specificity
        # First check if we're in a pullback
        if self.detect_pullback(df):
            metrics = {
                "ema_fast": df[f'ema_{self.config.fast_ema}'].iloc[-1],
                "ema_medium": df[f'ema_{self.config.medium_ema}'].iloc[-1],
                "current_price": df['close'].iloc[-1],
                **index_metrics
            }
            return MarketPhase.PULLBACK, metrics
            
        # Then check other phases
        elif self.detect_trending_phase(df):
            metrics = {
                "ema_alignment": "bullish",
                "trend_strength": "strong",
                **index_metrics
            }
            return MarketPhase.TRENDING, metrics
            
        elif self.detect_emerging_phase(df):
            metrics = {
                "ema_fast": df[f'ema_{self.config.fast_ema}'].iloc[-1],
                "ema_medium": df[f'ema_{self.config.medium_ema}'].iloc[-1],
                **index_metrics
            }
            return MarketPhase.EMERGING, metrics
            
        else:
            metrics = {
                "ema_fast": df[f'ema_{self.config.fast_ema}'].iloc[-1],
                "ema_medium": df[f'ema_{self.config.medium_ema}'].iloc[-1],
                "ema_slow": df[f'ema_{self.config.slow_ema}'].iloc[-1],
                **index_metrics
            }
            return MarketPhase.UNORDERED, metrics
