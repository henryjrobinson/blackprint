from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import pandas as pd
from strategy.signal_generator import SignalGenerator
from strategy.market_phase import MarketPhaseDetector
from strategy.indicators import calculate_emas, calculate_psar, calculate_macd
from risk.management import RiskManager

class TradingService:
    """
    Service to handle trading operations and strategy execution
    """
    
    def __init__(self, account_size: float = 100000, risk_per_trade: float = 0.02):
        self.signal_generator = SignalGenerator()
        self.phase_detector = MarketPhaseDetector()
        self.risk_manager = RiskManager(
            account_size=account_size,
            risk_per_trade=risk_per_trade
        )
        
    def analyze_symbol(self, symbol: str, data: pd.DataFrame) -> Dict:
        """
        Analyze a symbol using the Blackprint strategy
        
        Args:
            symbol: Trading symbol
            data: OHLCV data for the symbol
            
        Returns:
            Dictionary containing analysis results
        """
        # Calculate indicators
        emas = calculate_emas(data['close'])
        psar = calculate_psar(data['high'], data['low'])
        macd, signal = calculate_macd(data['close'])
        
        # Get latest values
        current_close = data['close'].iloc[-1]
        current_emas = {k: v.iloc[-1] for k, v in emas.items()}
        current_psar = psar.iloc[-1]
        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]
        
        # Check market phase
        phase = self.phase_detector.detect_phase(
            ema_13=current_emas['ema_13'],
            ema_34=current_emas['ema_34'],
            ema_89=current_emas['ema_89']
        )
        
        # Check for signals
        long_signal = self.signal_generator.check_long_entry(
            close=current_close,
            ema_5=current_emas['ema_5'],
            ema_13=current_emas['ema_13'],
            ema_34=current_emas['ema_34'],
            ema_89=current_emas['ema_89'],
            psar=current_psar,
            macd_line=current_macd,
            signal_line=current_signal
        )
        
        short_signal = self.signal_generator.check_short_entry(
            close=current_close,
            ema_13=current_emas['ema_13'],
            ema_34=current_emas['ema_34'],
            ema_89=current_emas['ema_89'],
            psar=current_psar,
            macd_line=current_macd,
            signal_line=current_signal
        )
        
        # Calculate potential trade parameters if there's a signal
        trade_params = None
        if long_signal or short_signal:
            direction = "LONG" if long_signal else "SHORT"
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
            "indicators": {
                "ema_5": current_emas['ema_5'],
                "ema_13": current_emas['ema_13'],
                "ema_34": current_emas['ema_34'],
                "ema_89": current_emas['ema_89'],
                "psar": current_psar,
                "macd": current_macd,
                "macd_signal": current_signal
            },
            "market_phase": phase,
            "signals": {
                "long": long_signal,
                "short": short_signal
            },
            "trade_parameters": trade_params
        }
    
    def _calculate_stop_loss(self, direction: str, current_price: float, psar: float) -> float:
        """Calculate stop loss price based on PSAR"""
        buffer = current_price * 0.001  # 0.1% buffer
        
        if direction == "LONG":
            return min(psar, current_price - buffer)
        else:  # SHORT
            return max(psar, current_price + buffer)
    
    def format_analysis_message(self, analysis: Dict) -> str:
        """Format analysis results as a Telegram message"""
        # Determine signal emoji
        signal_emoji = "🔍"
        if analysis['signals']['long']:
            signal_emoji = "🟢"
        elif analysis['signals']['short']:
            signal_emoji = "🔴"
        
        # Format indicators with arrows
        def get_arrow(current: float, prev: float) -> str:
            return "⬆️" if current > prev else "⬇️"
        
        # Create message
        message = (
            f"{signal_emoji} *Analysis for {analysis['symbol']}*\n\n"
            f"💰 Price: ${analysis['current_price']:.2f}\n\n"
            f"📊 *Technical Indicators:*\n"
            f"- EMA (13): ${analysis['indicators']['ema_13']:.2f}\n"
            f"- EMA (34): ${analysis['indicators']['ema_34']:.2f}\n"
            f"- EMA (89): ${analysis['indicators']['ema_89']:.2f}\n"
            f"- PSAR: ${analysis['indicators']['psar']:.2f}\n"
            f"- MACD: {'Bullish 📈' if analysis['indicators']['macd'] > analysis['indicators']['macd_signal'] else 'Bearish 📉'}\n\n"
            f"📈 *Market Phase:* {analysis['market_phase']}\n"
        )
        
        # Add trade parameters if there's a signal
        if analysis['trade_parameters']:
            trade = analysis['trade_parameters']
            message += (
                f"\n💡 *Trading Signal:*\n"
                f"Direction: {trade['direction']}\n"
                f"Entry: ${trade['entry_price']:.2f}\n"
                f"Stop Loss: ${trade['stop_loss']:.2f}\n"
                f"Position Size: {trade['position_size']:.2f} units\n"
            )
        
        return message
