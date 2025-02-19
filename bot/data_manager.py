import os
from typing import Optional, Dict, List, Callable
import pandas as pd
from datetime import datetime, timedelta
import logging
from alpaca.data import StockHistoricalDataClient
from alpaca.data.live import StockDataStream
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed

logger = logging.getLogger(__name__)

class AlpacaDataManager:
    """Manages all interactions with Alpaca's data APIs, including real-time and historical data."""
    
    def __init__(self):
        # Initialize API credentials from environment
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.api_secret = os.getenv('ALPACA_SECRET_KEY')
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Alpaca API credentials not found in environment variables")
        
        # Initialize clients
        self.hist_client = StockHistoricalDataClient(self.api_key, self.api_secret)
        self.stream_client = StockDataStream(self.api_key, self.api_secret)
        
        # Cache for latest market data
        self._latest_bars: Dict[str, pd.DataFrame] = {}
        self._callbacks: List[Callable] = []
        
        # Setup WebSocket handlers
        self._setup_stream_handlers()
    
    def _setup_stream_handlers(self):
        """Setup WebSocket stream handlers for real-time data."""
        
        @self.stream_client.on_bar
        async def handle_bar(bar):
            """Process incoming bar data."""
            symbol = bar.symbol
            
            # Convert bar to DataFrame format
            bar_df = pd.DataFrame([{
                'timestamp': bar.timestamp,
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume
            }])
            bar_df.set_index('timestamp', inplace=True)
            
            # Update latest bars
            if symbol not in self._latest_bars:
                self._latest_bars[symbol] = bar_df
            else:
                self._latest_bars[symbol] = pd.concat([self._latest_bars[symbol], bar_df])
                # Keep only last 100 bars for memory efficiency
                self._latest_bars[symbol] = self._latest_bars[symbol].tail(100)
            
            # Notify callbacks
            for callback in self._callbacks:
                callback(symbol, bar_df)
    
    async def start_streaming(self, symbols: List[str], timeframe: TimeFrame):
        """Start streaming market data for specified symbols."""
        try:
            await self.stream_client.subscribe_bars(symbols)
            logger.info(f"Started streaming for symbols: {symbols}")
        except Exception as e:
            logger.error(f"Error starting stream: {e}")
            raise
    
    def get_historical_bars(
        self,
        symbol: str,
        start: datetime,
        end: Optional[datetime] = None,
        timeframe: TimeFrame = TimeFrame.Minute
    ) -> pd.DataFrame:
        """Fetch historical bar data for a symbol."""
        if end is None:
            end = datetime.now()
        
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
            feed=DataFeed.IEX  # Can be configured based on subscription
        )
        
        try:
            bars = self.hist_client.get_stock_bars(request)
            df = bars.df
            
            if df.empty:
                logger.warning(f"No historical data found for {symbol}")
                return pd.DataFrame()
            
            return df
        
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            raise
    
    def register_callback(self, callback: Callable):
        """Register a callback function for real-time updates."""
        self._callbacks.append(callback)
    
    def get_latest_bars(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get the latest cached bars for a symbol."""
        return self._latest_bars.get(symbol)
    
    async def stop_streaming(self):
        """Stop streaming market data."""
        try:
            await self.stream_client.close()
            logger.info("Stopped streaming")
        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
            raise
