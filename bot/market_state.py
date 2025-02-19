from typing import Dict, List, Optional, Tuple, Callable
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum

from .market_phases import MarketPhase, MarketPhaseDetector, PhaseDetectionConfig
from .data_manager import AlpacaDataManager

logger = logging.getLogger(__name__)

@dataclass
class MarketMetrics:
    """Container for market metrics and indicators"""
    timestamp: datetime
    phase: MarketPhase
    ema_5: float
    ema_7: float
    ema_9: float
    ema_11: float
    ema_13: float
    ema_34: float
    ema_89: float
    psar: float
    macd: float
    macd_signal: float
    macd_hist: float
    candle_size: str
    symbol: str

    def to_dict(self) -> dict:
        """Convert metrics to dictionary for easy serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'phase': self.phase.name,
            'ema_5': round(self.ema_5, 4),
            'ema_7': round(self.ema_7, 4),
            'ema_9': round(self.ema_9, 4),
            'ema_11': round(self.ema_11, 4),
            'ema_13': round(self.ema_13, 4),
            'ema_34': round(self.ema_34, 4),
            'ema_89': round(self.ema_89, 4),
            'psar': round(self.psar, 4),
            'macd': round(self.macd, 4),
            'macd_signal': round(self.macd_signal, 4),
            'macd_hist': round(self.macd_hist, 4),
            'candle_size': self.candle_size,
            'symbol': self.symbol
        }

class MarketStateManager:
    """Manages market state tracking and phase detection"""
    
    def __init__(self, data_manager: AlpacaDataManager, config: Optional[PhaseDetectionConfig] = None):
        self.data_manager = data_manager
        self.config = config or PhaseDetectionConfig()
        self.detector = MarketPhaseDetector(config=self.config)
        
        # Cache for latest market states
        self._latest_states: Dict[str, MarketMetrics] = {}
        self._phase_change_callbacks: List[Callable] = []
        
        # Register for real-time updates
        self.data_manager.register_callback(self._handle_market_update)
    
    def _handle_market_update(self, symbol: str, new_data: pd.DataFrame):
        """Handle real-time market data updates"""
        try:
            # Get enough historical data for accurate calculations
            latest_bars = self.data_manager.get_latest_bars(symbol)
            if latest_bars is None or len(latest_bars) < 90:  # Need at least 90 bars for EMA-89
                logger.warning(f"Insufficient data for {symbol}, waiting for more bars")
                return
            
            # Detect phase and calculate metrics
            phase, metrics = self.detector.detect_phase(latest_bars)
            
            # Create market metrics
            current_metrics = MarketMetrics(
                timestamp=latest_bars.index[-1],
                phase=phase,
                ema_5=metrics['ema_5'][-1],
                ema_7=metrics['ema_7'][-1],
                ema_9=metrics['ema_9'][-1],
                ema_11=metrics['ema_11'][-1],
                ema_13=metrics['ema_13'][-1],
                ema_34=metrics['ema_34'][-1],
                ema_89=metrics['ema_89'][-1],
                psar=metrics['psar'][-1],
                macd=metrics['macd'][-1],
                macd_signal=metrics['macd_signal'][-1],
                macd_hist=metrics['macd_hist'][-1],
                candle_size=self.config.candle_size,
                symbol=symbol
            )
            
            # Check for phase change
            old_metrics = self._latest_states.get(symbol)
            phase_changed = (
                old_metrics is None or 
                old_metrics.phase != current_metrics.phase
            )
            
            # Update latest state
            self._latest_states[symbol] = current_metrics
            
            # Notify callbacks if phase changed
            if phase_changed:
                for callback in self._phase_change_callbacks:
                    callback(symbol, current_metrics)
                    
        except Exception as e:
            logger.error(f"Error handling market update for {symbol}: {e}")
    
    def get_current_state(self, symbol: str) -> Optional[MarketMetrics]:
        """Get the current market state for a symbol"""
        return self._latest_states.get(symbol)
    
    async def get_historical_state(
        self, 
        symbol: str, 
        timestamp: datetime
    ) -> Optional[MarketMetrics]:
        """Get the market state at a specific historical timestamp"""
        try:
            # Get enough historical data before the timestamp
            start_time = timestamp - pd.Timedelta(days=30)  # Get 30 days before
            end_time = timestamp + pd.Timedelta(minutes=1)  # Include the target timestamp
            
            historical_data = self.data_manager.get_historical_bars(
                symbol=symbol,
                start=start_time,
                end=end_time
            )
            
            if historical_data.empty:
                logger.warning(f"No historical data found for {symbol} at {timestamp}")
                return None
            
            # Detect phase and calculate metrics
            phase, metrics = self.detector.detect_phase(historical_data)
            
            # Create market metrics for the specific timestamp
            return MarketMetrics(
                timestamp=timestamp,
                phase=phase,
                ema_5=metrics['ema_5'][-1],
                ema_7=metrics['ema_7'][-1],
                ema_9=metrics['ema_9'][-1],
                ema_11=metrics['ema_11'][-1],
                ema_13=metrics['ema_13'][-1],
                ema_34=metrics['ema_34'][-1],
                ema_89=metrics['ema_89'][-1],
                psar=metrics['psar'][-1],
                macd=metrics['macd'][-1],
                macd_signal=metrics['macd_signal'][-1],
                macd_hist=metrics['macd_hist'][-1],
                candle_size=self.config.candle_size,
                symbol=symbol
            )
            
        except Exception as e:
            logger.error(f"Error getting historical state for {symbol} at {timestamp}: {e}")
            return None
    
    def register_phase_change_callback(self, callback: Callable):
        """Register a callback for market phase changes"""
        self._phase_change_callbacks.append(callback)
    
    def format_market_state(self, metrics: MarketMetrics, is_historical: bool = False) -> str:
        """Format market state for display"""
        timestamp_str = metrics.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        historical_prefix = "[HISTORICAL] " if is_historical else ""
        
        return f"""{historical_prefix}Market State Report
Symbol: {metrics.symbol}
Timestamp: {timestamp_str}
Candle Size: {metrics.candle_size}
Market Phase: {metrics.phase.name}

Key Indicators:
- EMAs:
  • Fast (5,7,9): {metrics.ema_5:.2f}, {metrics.ema_7:.2f}, {metrics.ema_9:.2f}
  • Medium (11,13): {metrics.ema_11:.2f}, {metrics.ema_13:.2f}
  • Slow (34,89): {metrics.ema_34:.2f}, {metrics.ema_89:.2f}
- PSAR: {metrics.psar:.2f}
- MACD:
  • Line: {metrics.macd:.2f}
  • Signal: {metrics.macd_signal:.2f}
  • Histogram: {metrics.macd_hist:.2f}
"""
