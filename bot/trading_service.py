from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import pandas as pd
import yfinance as yf
from .market_phases import MarketPhaseDetector, PhaseDetectionConfig, MarketPhase, MarketIndex
from strategy.indicators import calculate_emas, calculate_psar, calculate_macd
from risk.management import RiskManager

class TradingService:
    """
    Service to handle trading operations and strategy execution
    """
    
    def __init__(self, account_size: float = 100000, risk_per_trade: float = 0.02, candle_size: str = "15Min"):
        self.phase_detector = MarketPhaseDetector(
            config=PhaseDetectionConfig(candle_size=candle_size)
        )
        self.risk_manager = RiskManager(
            account_size=account_size,
            risk_per_trade=risk_per_trade
        )
        self.candle_size = candle_size
        
    def set_candle_size(self, candle_size: str):
        """Update the candle size configuration"""
        self.candle_size = candle_size
        self.phase_detector = MarketPhaseDetector(
            config=PhaseDetectionConfig(candle_size=candle_size)
        )
        
    def set_index(self, index: MarketIndex):
        """Update the reference index"""
        self.phase_detector.set_index(index)
        
    def get_current_index(self) -> MarketIndex:
        """Get the current reference index"""
        return self.phase_detector.config.index
        
    def _fetch_index_data(self):
        """Fetch current index data"""
        try:
            index_symbol = self.phase_detector.get_index_symbol()
            index = yf.Ticker(index_symbol)
            data = index.history(period="1mo", interval=self.candle_size)
            if not data.empty:
                self.phase_detector.update_index_data(data)
            return data
        except Exception as e:
            print(f"Error fetching index data: {str(e)}")
            return None
        
    def analyze_symbol(self, symbol: str, data: pd.DataFrame) -> Dict:
        """
        Analyze a symbol using the Blackprint strategy
        
        Args:
            symbol: Trading symbol
            data: OHLCV data for the symbol
            
        Returns:
            Dictionary containing analysis results
        """
        # Fetch and update index data
        index_data = self._fetch_index_data()
        
        # Detect market phase
        phase, phase_metrics = self.phase_detector.detect_phase(data)
        
        # Calculate additional indicators
        psar = calculate_psar(data['high'], data['low'])
        macd, signal = calculate_macd(data['close'])
        
        # Get latest values
        current_close = data['close'].iloc[-1]
        current_psar = psar.iloc[-1]
        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]
        
        # Determine if conditions are suitable for trading
        can_trade = phase in [MarketPhase.TRENDING, MarketPhase.EMERGING]
        is_pullback = phase == MarketPhase.PULLBACK
        
        # Calculate potential trade parameters if conditions are suitable
        trade_params = None
        if can_trade or is_pullback:
            # For pullbacks, we want to enter in the direction of the trend
            direction = "LONG" if data[f'ema_{self.phase_detector.config.fast_ema}'].iloc[-1] > \
                                 data[f'ema_{self.phase_detector.config.slow_ema}'].iloc[-1] else "SHORT"
            
            stop_loss = self._calculate_stop_loss(
                direction=direction,
                current_price=current_close,
                psar=current_psar
            )
            
            position_size = self.risk_manager.calculate_position_size(
                entry_price=Decimal(str(current_close)),
                stop_loss_price=Decimal(str(stop_loss)),
                pip_value=Decimal('0.0001')  # Assuming forex/crypto
            )
            
            trade_params = {
                "direction": direction,
                "entry_price": current_close,
                "stop_loss": stop_loss,
                "position_size": float(position_size)
            }
        
        return {
            "symbol": symbol,
            "timestamp": data.index[-1],
            "current_price": current_close,
            "market_phase": {
                "phase": phase.value,
                "metrics": phase_metrics
            },
            "indicators": {
                "psar": float(current_psar),
                "macd": {
                    "line": float(current_macd),
                    "signal": float(current_signal)
                }
            },
            "trade_opportunity": trade_params,
            "candle_size": self.candle_size,
            "reference_index": self.phase_detector.config.index.name
        }
        
    def _calculate_stop_loss(self, direction: str, current_price: float, psar: float) -> float:
        """Calculate stop loss level based on direction and PSAR"""
        if direction == "LONG":
            return min(psar, current_price * 0.99)  # 1% below entry for long
        else:
            return max(psar, current_price * 1.01)  # 1% above entry for short

    def format_analysis_message(self, analysis: Dict) -> str:
        """Format analysis results as a Telegram message"""
        # Determine signal emoji
        signal_emoji = "🔍"
        if analysis['trade_opportunity']:
            signal_emoji = "🟢" if analysis['trade_opportunity']['direction'] == "LONG" else "🔴"
        
        # Format indicators with arrows
        def get_arrow(current: float, prev: float) -> str:
            return "⬆️" if current > prev else "⬇️"
        
        # Create message
        message = (
            f"{signal_emoji} *Analysis for {analysis['symbol']}*\n\n"
            f"💰 Price: ${analysis['current_price']:.2f}\n\n"
            f"📊 *Technical Indicators:*\n"
            f"- PSAR: ${analysis['indicators']['psar']:.2f}\n"
            f"- MACD: {'Bullish 📈' if analysis['indicators']['macd']['line'] > analysis['indicators']['macd']['signal'] else 'Bearish 📉'}\n\n"
            f"📈 *Market Phase:* {analysis['market_phase']['phase']}\n"
        )
        
        # Add trade parameters if there's a signal
        if analysis['trade_opportunity']:
            trade = analysis['trade_opportunity']
            message += (
                f"\n💡 *Trading Signal:*\n"
                f"Direction: {trade['direction']}\n"
                f"Entry: ${trade['entry_price']:.2f}\n"
                f"Stop Loss: ${trade['stop_loss']:.2f}\n"
                f"Position Size: {trade['position_size']:.2f} units\n"
            )
        
        return message
