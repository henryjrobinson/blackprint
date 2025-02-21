import os
from typing import Optional, Dict, List, Callable
import pandas as pd
from datetime import datetime, timedelta
import logging
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.live import StockDataStream
import pytz
import asyncio

logger = logging.getLogger(__name__)

class AlpacaDataManager:
    """Manages all interactions with Alpaca's data APIs, including real-time and historical data."""
    
    def __init__(self):
        # Initialize API credentials from environment
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.api_secret = os.getenv('ALPACA_API_SECRET')
        
        logger.info(f"Initializing AlpacaDataManager with API key: {'*' * len(self.api_key) if self.api_key else 'None'}")
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Alpaca API credentials not found in environment variables. Please check ALPACA_API_KEY and ALPACA_API_SECRET in .env file")
        
        # Initialize clients
        self.hist_client = StockHistoricalDataClient(self.api_key, self.api_secret)
        self.stream_client = StockDataStream(self.api_key, self.api_secret)
        
        # Cache for latest market data
        self._latest_bars: Dict[str, pd.DataFrame] = {}
        self._callbacks: List[Callable] = []
        
        # Map timeframes
        self.timeframe_map = {
            "1Min": TimeFrame.Minute,
            "5Min": TimeFrame(5, TimeFrame.Minute),
            "15Min": TimeFrame(15, TimeFrame.Minute),
            "30Min": TimeFrame(30, TimeFrame.Minute),
            "1H": TimeFrame.Hour,
            "4H": TimeFrame(4, TimeFrame.Hour),
            "1D": TimeFrame.Day
        }
        
        # Initialize subscribed symbols
        self.subscribed_symbols = set()
    
    async def subscribe_to_bars(self, symbols: List[str]):
        """Subscribe to real-time bar updates for symbols"""
        try:
            # Add new symbols to subscribed set
            self.subscribed_symbols.update(symbols)
            
            # Subscribe to bar updates
            await self.stream_client.subscribe_bars(self._handle_bar, *symbols)
            
            logger.info(f"Subscribed to bar updates for: {symbols}")
        except Exception as e:
            logger.error(f"Error subscribing to bars: {e}")
            raise
    
    async def _handle_bar(self, bar):
        """Handle incoming bar data"""
        try:
            symbol = bar.symbol
            if symbol not in self._latest_bars:
                self._latest_bars[symbol] = pd.DataFrame()
            
            # Convert bar to DataFrame row
            bar_data = {
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume,
                'timestamp': bar.timestamp
            }
            
            # Update latest bars
            new_row = pd.DataFrame([bar_data])
            self._latest_bars[symbol] = pd.concat([self._latest_bars[symbol], new_row], ignore_index=True)
            
            # Notify callbacks
            for callback in self._callbacks:
                await callback(symbol, self._latest_bars[symbol])
                
        except Exception as e:
            logger.error(f"Error handling bar data: {e}")
    
    async def start_streaming(self):
        """Start streaming real-time market data"""
        try:
            logger.info("Starting market data streaming...")
            
            # Subscribe to the stream
            self.stream_client.subscribe_bars(self._handle_bar, "SPY")
            
            # Start the connection
            await self.stream_client.run()
            
        except Exception as e:
            logger.error(f"Error connecting to streaming API: {e}")
            raise
    
    async def stop_streaming(self):
        """Stop the streaming connection"""
        try:
            await self.stream_client.disconnect()
            logger.info("Disconnected from Alpaca streaming API")
        except Exception as e:
            logger.error(f"Error disconnecting from streaming API: {e}")
            raise
    
    async def get_bars(self, symbol: str, timeframe: str = "1H", limit: int = 100) -> pd.DataFrame:
        """Fetch historical bars for a symbol"""
        try:
            # Calculate start and end times
            end = datetime.now(pytz.UTC)
            # For higher timeframes, we need more historical data to calculate indicators
            multiplier = 3 if timeframe in ["4H", "1D"] else 1
            start = end - timedelta(days=limit * multiplier)
            
            # Create the request
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=self.timeframe_map[timeframe],
                start=start,
                end=end
            )
            
            # Get the bars
            bars = self.hist_client.get_stock_bars(request)
            
            # Convert to DataFrame
            if bars and hasattr(bars, 'df'):
                df = bars.df
                
                if len(df) == 0:
                    raise ValueError(f"No data returned for {symbol}")
                
                # Reset index to make timestamp a column
                df = df.reset_index(level=[0,1])
                
                # Basic data cleaning
                df = df.dropna()
                df = df.sort_values('timestamp')
                
                return df
            else:
                raise ValueError(f"No data returned for {symbol}")
                
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            raise
    
    async def get_current_price(self, symbol: str) -> float:
        """Get the current price for a symbol"""
        try:
            bars = await self.get_bars(symbol, timeframe="1Min", limit=1)
            if len(bars) > 0:
                return bars.iloc[-1]['close']
            raise ValueError(f"No current price data for {symbol}")
        except Exception as e:
            logger.error(f"Error fetching current price for {symbol}: {e}")
            raise
    
    async def get_multiple_symbols(self, symbols: List[str], timeframe: str = "1H", limit: int = 100) -> Dict[str, pd.DataFrame]:
        """Fetch historical bars for multiple symbols"""
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = await self.get_bars(symbol, timeframe, limit)
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
                continue
        return results
    
    def register_callback(self, callback: Callable):
        """Register a callback function for real-time updates."""
        self._callbacks.append(callback)
    
    def get_latest_bars(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get the latest cached bars for a symbol."""
        return self._latest_bars.get(symbol)
