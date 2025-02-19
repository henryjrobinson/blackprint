import unittest
import pandas as pd
import numpy as np
from bot.market_phases import MarketPhaseDetector, PhaseDetectionConfig, MarketPhase

class TestMarketPhaseDetector(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.detector = MarketPhaseDetector()
        
        # Create sample data with proper index
        dates = pd.date_range(start='2023-01-01', periods=100, freq='15min')
        self.sample_data = pd.DataFrame({
            'open': np.random.randn(100).cumsum() + 100,
            'high': np.random.randn(100).cumsum() + 102,
            'low': np.random.randn(100).cumsum() + 98,
            'close': np.random.randn(100).cumsum() + 100,
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
    def test_unordered_phase(self):
        """Test unordered phase detection"""
        # Create choppy market data with high volatility
        close_prices = []
        base = 100
        
        # First create some baseline data
        for i in range(30):
            close_prices.append(base + np.random.uniform(-1, 1))
            
        # Then add choppy price action
        for i in range(70):
            # Random walk with high volatility
            base += np.random.uniform(-2, 2)  # Random drift
            close_prices.append(base + np.random.uniform(-3, 3))  # Add noise
        
        self.sample_data['close'] = pd.Series(close_prices, index=self.sample_data.index)
        self.sample_data['high'] = self.sample_data['close'] + 0.5
        self.sample_data['low'] = self.sample_data['close'] - 0.5
        
        phase, metrics = self.detector.detect_phase(self.sample_data)
        self.assertEqual(phase, MarketPhase.UNORDERED)
        
    def test_emerging_phase(self):
        """Test emerging phase detection"""
        # Create data where fast EMA crosses above medium and slow EMAs
        prices = []
        base = 100
        
        # First 60 bars sideways to slightly down
        for i in range(60):
            base -= 0.05  # Downward bias
            prices.append(base + np.random.uniform(-0.1, 0.1))
        
        # Next 20 bars initial move up with increasing momentum
        for i in range(20):
            base += 0.2 + (i * 0.02)  # Accelerating move up
            prices.append(base + np.random.uniform(-0.02, 0.02))
            
        # Last 20 bars consolidation near highs
        last_price = prices[-1]
        for i in range(20):
            prices.append(last_price + np.random.uniform(-0.1, 0.1))
        
        self.sample_data['close'] = pd.Series(prices, index=self.sample_data.index)
        self.sample_data['high'] = self.sample_data['close'] + 0.1
        self.sample_data['low'] = self.sample_data['close'] - 0.1
        
        phase, metrics = self.detector.detect_phase(self.sample_data)
        self.assertEqual(phase, MarketPhase.EMERGING)
        
    def test_trending_phase(self):
        """Test trending phase detection"""
        # Create strong upward trend with aligned EMAs
        prices = []
        base = 100
        
        # First 20 bars establishing upward momentum
        for i in range(20):
            base += 0.3
            prices.append(base + np.random.uniform(-0.05, 0.05))
            
        # Next 80 bars strong trend with increasing spread
        for i in range(80):
            base += 0.4  # Accelerating trend
            prices.append(base + np.random.uniform(-0.05, 0.05))
        
        self.sample_data['close'] = pd.Series(prices, index=self.sample_data.index)
        self.sample_data['high'] = self.sample_data['close'] + 0.1
        self.sample_data['low'] = self.sample_data['close'] - 0.1
        
        phase, metrics = self.detector.detect_phase(self.sample_data)
        self.assertEqual(phase, MarketPhase.TRENDING)
        
    def test_pullback_phase(self):
        """Test pullback detection"""
        # Create strong uptrend followed by pullback
        prices = []
        base = 100
        
        # First 70 bars: strong uptrend
        for i in range(70):
            base += 0.5  # Strong consistent uptrend
            prices.append(base + np.random.uniform(-0.02, 0.02))  # Minimal noise
            
        peak = base
        # Next 20 bars: controlled pullback to 38.2% retracement
        retracement = (peak - 100) * 0.382  # Using full trend range
        
        # Initial sharp pullback (15 bars)
        for i in range(15):
            current = peak - (retracement * i / 15)  # Linear drop
            prices.append(current + np.random.uniform(-0.02, 0.02))
            
        # Final consolidation near support (15 bars)
        last_price = prices[-1]
        for i in range(15):
            # Slight bullish bias while staying near EMAs
            current = last_price + (i * 0.1)  # Clear bullish bias
            prices.append(current + np.random.uniform(-0.01, 0.01))
        
        # Convert to DataFrame
        self.sample_data['close'] = pd.Series(prices, index=self.sample_data.index)
        self.sample_data['high'] = self.sample_data['close'] * 1.002  # Slightly wider ranges
        self.sample_data['low'] = self.sample_data['close'] * 0.998
        
        # First verify we were in a trend
        df = self.detector.calculate_emas(self.sample_data.iloc[:-30])  # Data before pullback
        self.assertTrue(self.detector.detect_trending_phase(df))
        
        # Then check pullback detection
        phase, metrics = self.detector.detect_phase(self.sample_data)
        self.assertEqual(phase, MarketPhase.PULLBACK)
        
    def test_candle_size_config(self):
        """Test candle size configuration"""
        detector = MarketPhaseDetector(config=PhaseDetectionConfig(candle_size="1H"))
        self.assertEqual(detector.config.candle_size, "1H")
        
if __name__ == '__main__':
    unittest.main()
