import unittest
import pandas as pd
import numpy as np
from bot.market_phases import MarketPhaseDetector, PhaseDetectionConfig, MarketPhase

class TestMarketPhaseDetector(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.detector = MarketPhaseDetector()
        self.sample_data = pd.DataFrame()  # Initialize empty DF
        
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
        print("\nUnordered Phase Test Metrics:")
        print(metrics)
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
            
        # Next 30 bars initial move up with increasing momentum
        for i in range(30):
            base += 0.2 + (i * 0.02)  # Accelerating move up
            prices.append(base + np.random.uniform(-0.02, 0.02))
            
        # Last 10 bars maintain strong upward bias
        last_price = prices[-1]
        for i in range(10):
            last_price += 0.2  # Consistent upward movement
            prices.append(last_price + np.random.uniform(-0.05, 0.05))
            
        self.sample_data['close'] = pd.Series(prices, index=self.sample_data.index)
        self.sample_data['high'] = self.sample_data['close'] + 0.1
        self.sample_data['low'] = self.sample_data['close'] - 0.1
        
        phase, metrics = self.detector.detect_phase(self.sample_data)
        print("\nEmerging Phase Test Metrics:")
        print(metrics)
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
        print("\nTrending Phase Test Metrics:")
        print(metrics)
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
        trend_phase, trend_metrics = self.detector.detect_phase(df)
        print("\nPullback Pre-Trend Metrics:")
        print(trend_metrics)
        self.assertTrue(self.detector.detect_trending_phase(df))
        
        # Then check pullback detection
        phase, metrics = self.detector.detect_phase(self.sample_data)
        print("\nPullback Phase Test Metrics:")
        print(metrics)
        self.assertEqual(phase, MarketPhase.PULLBACK)
        
    def test_candle_size_config(self):
        """Test candle size configuration"""
        detector = MarketPhaseDetector(config=PhaseDetectionConfig(candle_size="1H"))
        self.assertEqual(detector.config.candle_size, "1H")

    def test_strong_emerging_borderline_trending(self):
        """Test emerging phase that approaches trending thresholds"""
        prices = self._generate_base_movement(initial=100, bars=100, direction=1)
        
        # Accelerate into strong but not quite trending movement
        for i in range(20):
            prices.append(prices[-1] + 0.35 + (i * 0.015))
        
        self._load_price_data(prices)
        phase, metrics = self.detector.detect_phase(self.sample_data)
        print("\nBorderline Emerging/Trending Metrics:")
        print(f"Fast Slope: {metrics['fast_slope']:.3f}")
        print(f"Medium Slope: {metrics['medium_slope']:.3f}")
        print(f"Momentum: {metrics['price_momentum']:.3f}")
        self.assertEqual(phase, MarketPhase.EMERGING)
        self.assertTrue(0.35 <= metrics['fast_slope'] < 0.4)

    def test_failed_emerging_phase(self):
        """Test aborted emerging phase that falls back to unordered"""
        prices = self._generate_base_movement(initial=100, bars=60, direction=1)
        
        # 20 bars of emerging characteristics
        for _ in range(20):
            prices.append(prices[-1] + 0.25)
        
        # Momentum collapse
        for _ in range(20):
            prices.append(prices[-1] - 0.15)
        
        self._load_price_data(prices)
        phase, metrics = self.detector.detect_phase(self.sample_data)
        self.assertEqual(phase, MarketPhase.UNORDERED)

    def test_deep_pullback(self):
        """Test pullback that exceeds normal retracement levels"""
        # Establish strong trend
        prices = self._generate_base_movement(initial=100, bars=100, direction=1)
        prices = self._add_trend_acceleration(prices, bars=30, acceleration=0.02)
        
        # Deep retracement (40% of trend move)
        trend_height = prices[-1] - prices[0]
        for _ in range(25):
            prices.append(prices[-1] - (trend_height * 0.4)/25)
        
        self._load_price_data(prices)
        phase, metrics = self.detector.detect_phase(self.sample_data)
        self.assertNotEqual(phase, MarketPhase.PULLBACK)

    def test_ranging_market(self):
        """Test prolonged ranging market after a trend"""
        prices = self._generate_base_movement(initial=100, bars=100, direction=1)
        
        # 50 bars of sideways movement
        base = prices[-1]
        for _ in range(50):
            prices.append(base + np.random.uniform(-0.15, 0.15))
        
        self._load_price_data(prices)
        phase, metrics = self.detector.detect_phase(self.sample_data)
        self.assertEqual(phase, MarketPhase.UNORDERED)

    def test_whipsaw_market(self):
        """Test volatile market with rapid phase changes"""
        prices = []
        base = 100
        
        # Generate 10 rapid cycles of up/down moves
        for _ in range(10):
            # Up move
            for _ in range(5):
                base += 0.5
                prices.append(base)
            # Down move
            for _ in range(5):
                base -= 0.5
                prices.append(base)
        
        self._load_price_data(prices)
        phase, metrics = self.detector.detect_phase(self.sample_data)
        self.assertEqual(phase, MarketPhase.UNORDERED)

    def _generate_base_movement(self, initial, bars, direction):
        prices = [initial]
        for _ in range(bars):
            prices.append(prices[-1] + np.random.uniform(-0.05, 0.05) * direction)
        return prices

    def _add_trend_acceleration(self, prices, bars, acceleration):
        for _ in range(bars):
            prices.append(prices[-1] + 0.2 + acceleration)
        return prices

    def _load_price_data(self, prices):
        self.sample_data = pd.DataFrame({
            'close': prices,
            'timestamp': pd.date_range(start='2023-01-01', periods=len(prices), freq='15min')
        }).set_index('timestamp')
        self.sample_data.index = self.sample_data.index.tz_localize('UTC')
        self.sample_data['high'] = self.sample_data['close'] + 0.1
        self.sample_data['low'] = self.sample_data['close'] - 0.1

if __name__ == '__main__':
    unittest.main()
