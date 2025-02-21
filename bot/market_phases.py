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
        """Detect unordered market phase - choppy price action with no clear trend"""
        # Calculate EMAs if not already present
        ema_cols = [f'ema_{self.config.fast_ema}', f'ema_{self.config.medium_ema}', f'ema_{self.config.slow_ema}']
        if not all(col in df.columns for col in ema_cols):
            df = self.calculate_emas(df)
            
        fast = df[f'ema_{self.config.fast_ema}']
        medium = df[f'ema_{self.config.medium_ema}']
        slow = df[f'ema_{self.config.slow_ema}']
        
        # Calculate slopes over different windows
        fast_slope = self.calculate_slope(df[f'ema_{self.config.fast_ema}'])
        medium_slope = self.calculate_slope(df[f'ema_{self.config.medium_ema}'])
        slow_slope = self.calculate_slope(df[f'ema_{self.config.slow_ema}'])
        
        # Calculate momentum
        momentum = self.calculate_momentum(df)
        
        # Get latest values
        fast_val = fast.iloc[-1]
        medium_val = medium.iloc[-1]
        slow_val = slow.iloc[-1]
        price = df['close'].iloc[-1]

        # Check for clear lack of trend - all slopes near zero
        slopes_weak = all(abs(slope) < 0.05 for slope in [fast_slope, medium_slope, slow_slope])
        
        # Check for EMAs too close together
        emas_compressed = abs(fast_val - slow_val) < 0.002 * price
        
        # Check for choppy price action
        price_changes = df['close'].diff().rolling(5).std()
        high_volatility = price_changes.iloc[-5:].mean() > 0.8  # Higher threshold
        
        # Detect unordered only when multiple conditions are met
        return (slopes_weak and emas_compressed) or (slopes_weak and high_volatility)
    
    def detect_emerging_phase(self, df: pd.DataFrame) -> bool:
        """Detect emerging phase - initial trend with accelerating momentum"""
        # Calculate EMAs if not already present
        ema_cols = [f'ema_{self.config.fast_ema}', f'ema_{self.config.medium_ema}', f'ema_{self.config.slow_ema}']
        if not all(col in df.columns for col in ema_cols):
            df = self.calculate_emas(df)

        # Calculate slopes over different windows
        fast_slope = self.calculate_slope(df[f'ema_{self.config.fast_ema}'])
        medium_slope = self.calculate_slope(df[f'ema_{self.config.medium_ema}'])
        slow_slope = self.calculate_slope(df[f'ema_{self.config.slow_ema}'])
        
        # Calculate momentum
        momentum = self.calculate_momentum(df)
        
        # Get latest values
        fast = df[f'ema_{self.config.fast_ema}'].iloc[-1]
        medium = df[f'ema_{self.config.medium_ema}'].iloc[-1]
        slow = df[f'ema_{self.config.slow_ema}'].iloc[-1]
        price = df['close'].iloc[-1]

        # Check for accelerating momentum - price above EMAs with margin
        margin = 0.001 * price  # 0.1% margin
        accelerating = (
            price > fast - margin and
            fast > medium - margin and
            medium > slow - margin
        )
        
        # All slopes should be positive but not too strong yet
        slopes_emerging = (
            0.25 < fast_slope <= 0.75 and
            0.15 < medium_slope <= 0.5 and
            0 < slow_slope < 0.4  # Increased upper bound
        )
        
        # Momentum should be positive but not too strong
        momentum_emerging = 0.2 <= momentum <= 0.8  # Expanded upper bound
        
        return accelerating and slopes_emerging and momentum_emerging

    def detect_trending_phase(self, df: pd.DataFrame) -> bool:
        """
        Detect trending market phase - Emerging phase with additional confirmation
        """
        # Calculate EMAs if not already present
        ema_cols = [f'ema_{self.config.fast_ema}', f'ema_{self.config.medium_ema}', f'ema_{self.config.slow_ema}']
        if not all(col in df.columns for col in ema_cols):
            df = self.calculate_emas(df)

        # Calculate slopes
        fast_slope = self.calculate_slope(df[f'ema_{self.config.fast_ema}'])
        medium_slope = self.calculate_slope(df[f'ema_{self.config.medium_ema}'])
        slow_slope = self.calculate_slope(df[f'ema_{self.config.slow_ema}'])
        
        # Calculate momentum
        momentum = self.calculate_momentum(df)
        
        # Get latest values
        fast = df[f'ema_{self.config.fast_ema}'].iloc[-1]
        medium = df[f'ema_{self.config.medium_ema}'].iloc[-1]
        slow = df[f'ema_{self.config.slow_ema}'].iloc[-1]
        price = df['close'].iloc[-1]

        # Check for strong trend - EMAs well aligned with margin
        margin = 0.001 * price  # 0.1% margin
        aligned = (
            price > fast - margin and
            fast > medium - margin and
            medium > slow - margin and
            fast - slow > 0.01 * price  # EMAs must be well separated
        )
        
        # All slopes should be strongly positive
        steady_trend = (
            fast_slope >= 0.35 and
            medium_slope >= 0.35 and
            slow_slope >= 0.25
        )
        
        # Strong momentum
        price_momentum = momentum >= 0.25
        
        return aligned and steady_trend and price_momentum
    
    def detect_pullback(self, df: pd.DataFrame) -> bool:
        """Detect pullback phase - price between EMAs with positive momentum"""
        # Calculate EMAs if not already present
        ema_cols = [f'ema_{self.config.fast_ema}', f'ema_{self.config.medium_ema}', f'ema_{self.config.slow_ema}']
        if not all(col in df.columns for col in ema_cols):
            df = self.calculate_emas(df)

        # Get latest values
        fast = df[f'ema_{self.config.fast_ema}'].iloc[-1]
        medium = df[f'ema_{self.config.medium_ema}'].iloc[-1]
        slow = df[f'ema_{self.config.slow_ema}'].iloc[-1]
        price = df['close'].iloc[-1]

        # Calculate slopes
        fast_slope = self.calculate_slope(df[f'ema_{self.config.fast_ema}'])
        medium_slope = self.calculate_slope(df[f'ema_{self.config.medium_ema}'])
        slow_slope = self.calculate_slope(df[f'ema_{self.config.slow_ema}'])
        
        # Calculate momentum
        momentum = self.calculate_momentum(df)

        # Price should be between fast and medium EMAs with margin
        margin = 0.001 * price  # 0.1% margin
        price_in_zone = (
            min(fast, medium) - margin <= price <= max(fast, medium) + margin
        )
        
        # Check for prior uptrend - EMAs properly aligned
        prior_trend = slow < medium
        
        # Allow more negative slopes but still require slow EMA positive
        slopes_ok = (
            fast_slope > -0.1 and
            medium_slope > -0.1 and
            slow_slope > 0
        )

        # Momentum should be turning positive after pullback
        momentum_recovering = momentum > 0
        
        return price_in_zone and prior_trend and slopes_ok and momentum_recovering
    
    def detect_phase(self, df: pd.DataFrame) -> tuple[MarketPhase, dict]:
        # Validate input data
        if df.empty or 'close' not in df.columns:
            return MarketPhase.UNORDERED, {'error': 'Invalid input data'}
            
        # Always recalculate EMAs with latest data
        df = self.calculate_emas(df)
            
        # Get latest values for metrics
        metrics = {
            'ema_fast': df[f'ema_{self.config.fast_ema}'].iloc[-1],
            'ema_medium': df[f'ema_{self.config.medium_ema}'].iloc[-1],
            'ema_slow': df[f'ema_{self.config.slow_ema}'].iloc[-1],
            'close': df['close'].iloc[-1]
        }
        
        # Calculate slopes and momentum
        metrics['fast_slope'] = self.calculate_slope(df[f'ema_{self.config.fast_ema}'])
        metrics['medium_slope'] = self.calculate_slope(df[f'ema_{self.config.medium_ema}'])
        metrics['slow_slope'] = self.calculate_slope(df[f'ema_{self.config.slow_ema}'])
        metrics['price_momentum'] = self.calculate_momentum(df)

        # Check phases in order of priority
        # 1. Check for trending phase first - most definitive
        if self.detect_trending_phase(df):
            metrics['detected_phase'] = 'trending'
            return MarketPhase.TRENDING, metrics
            
        # 2. Check for pullback - requires prior trend
        if self.detect_pullback(df):
            metrics['detected_phase'] = 'pullback'
            return MarketPhase.PULLBACK, metrics
            
        # 3. Check for emerging phase - early trend
        if self.detect_emerging_phase(df):
            metrics['detected_phase'] = 'emerging'
            return MarketPhase.EMERGING, metrics
            
        # 4. Check for unordered phase - least definitive
        if self.detect_unordered_phase(df):
            metrics['detected_phase'] = 'unordered'
            return MarketPhase.UNORDERED, metrics
            
        # Default to unordered if no other phase detected
        metrics['detected_phase'] = 'unordered'
        return MarketPhase.UNORDERED, metrics

    def _check_ema_alignment(self, metrics: dict) -> bool:
        # Require EMA hierarchy: fast > medium > slow
        return (
            metrics['ema_fast'] > metrics['ema_medium'] and
            metrics['ema_medium'] > metrics['ema_slow']
        )

    def calculate_slope(self, series: pd.Series, window: int = 5) -> float:
        """Robust slope calculation with error handling"""
        try:
            if len(series) < window or series.isna().all():
                return 0.0
            
            # Use last valid window of data
            valid_series = series.dropna().iloc[-window:]
            if len(valid_series) < 2:
                return 0.0
            
            x = np.arange(len(valid_series))
            y = valid_series.values.astype(float)
            
            # Handle constant values
            if np.all(y == y[0]):
                return 0.0
            
            # Calculate linear regression
            A = np.vstack([x, np.ones(len(x))]).T
            slope = np.linalg.lstsq(A, y, rcond=None)[0][0]
            return float(slope)
        except:
            return 0.0

    def calculate_momentum(self, df: pd.DataFrame) -> float:
        try:
            momentum = df['close'].diff().dropna().rolling(5, min_periods=1).mean().iloc[-1]
            return float(momentum) if not np.isnan(momentum) else 0.0
        except:
            return 0.0
