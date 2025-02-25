from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import os
import pandas as pd
import pytz
from typing import Dict, List, Callable
import logging
import asyncio
import websocket
import json
import ssl
import threading
import random
import base64

logger = logging.getLogger(__name__)

class AlpacaDataManager:
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        """Initialize the data manager"""
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        
        # Use test stream endpoint
        if "paper" in base_url:
            self.ws_endpoint = "wss://stream.data.sandbox.alpaca.markets/v2/iex"
        else:
            self.ws_endpoint = "wss://stream.data.alpaca.markets/v2/iex"
        
        # Debug log the first few characters of credentials
        if self.api_key:
            logger.debug(f"API Key starts with: {self.api_key[:4]}...")
        else:
            logger.error("API Key not found in environment")
            
        if self.api_secret:
            logger.debug(f"API Secret starts with: {self.api_secret[:4]}...")
        else:
            logger.error("API Secret not found in environment")
        
        logger.info(f"Initializing AlpacaDataManager with API key: {'*' * len(self.api_key) if self.api_key else 'None'}")
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Alpaca API credentials not found in environment variables")
        
        # Initialize historical client
        self.hist_client = StockHistoricalDataClient(self.api_key, self.api_secret)
        
        # Initialize WebSocket connection
        self.ws = None
        self.ws_thread = None
        self.ws_running = False
        
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
        
        # Initialize data storage
        self._latest_bars: Dict[str, pd.DataFrame] = {}
        self._callbacks: List[Callable] = []
        self.subscribed_symbols = set()

    def _run_websocket(self):
        """Run WebSocket connection in a separate thread"""
        def on_message(ws, message):
            data = json.loads(message)
            logger.debug(f"Message received: {data}")
            if isinstance(data, list):
                for msg in data:
                    self._handle_message(msg)
            else:
                self._handle_message(data)

        def on_error(ws, error):
            logger.error(f"WebSocket error: {error}")

        def on_close(ws, close_status_code, close_msg):
            logger.info(f"WebSocket connection closed: {close_status_code} - {close_msg}")
            self.ws_running = False

        def on_open(ws):
            logger.info("WebSocket connection opened")
            # Send authentication message
            auth_data = {
                "action": "auth",
                "key": self.api_key,
                "secret": self.api_secret
            }
            ws.send(json.dumps(auth_data))
            logger.info("Authentication message sent")
            
            # Wait a bit before subscribing
            import time
            time.sleep(1)
            
            # Subscribe to test stream
            subscribe_message = {
                "action": "subscribe",
                "trades": ["SPY"],
                "quotes": ["SPY"],
                "bars": ["SPY"]
            }
            ws.send(json.dumps(subscribe_message))
            logger.info("Stream subscriptions sent")

        # Create WebSocket connection with exponential backoff
        max_retries = 5
        base_delay = 5  # seconds
        
        while self.ws_running:
            for attempt in range(max_retries):
                try:
                    # Add jitter to avoid thundering herd
                    import random
                    jitter = random.uniform(0, 1)
                    delay = (base_delay * (2 ** attempt)) + jitter
                    
                    if attempt > 0:
                        logger.info(f"Waiting {delay:.2f} seconds before retry {attempt + 1}/{max_retries}...")
                        import time
                        time.sleep(delay)
                    
                    # Create WebSocket connection
                    websocket.enableTrace(True)
                    self.ws = websocket.WebSocketApp(
                        self.ws_endpoint,
                        on_message=on_message,
                        on_error=on_error,
                        on_close=on_close,
                        on_open=on_open
                    )
                    
                    # Run the WebSocket connection
                    self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
                    
                    # If we get here and ws_running is still True, try to reconnect
                    if self.ws_running:
                        logger.warning(f"WebSocket disconnected, attempting to reconnect...")
                    else:
                        break
                        
                except Exception as e:
                    if attempt < max_retries - 1 and self.ws_running:
                        logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                    else:
                        logger.error(f"Failed to connect after {max_retries} attempts")
                        self.ws_running = False
                        break

    async def start_streaming(self):
        """Start streaming real-time market data"""
        try:
            logger.info("Starting market data streaming...")
            
            if self.ws_thread and self.ws_thread.is_alive():
                logger.warning("WebSocket thread is already running")
                return
            
            self.ws_running = True
            self.ws_thread = threading.Thread(target=self._run_websocket)
            self.ws_thread.daemon = True  # Thread will be terminated when main program exits
            self.ws_thread.start()
            
        except Exception as e:
            logger.error(f"Error connecting to streaming API: {e}", exc_info=True)
            raise

    def _handle_message(self, msg):
        """Handle incoming WebSocket message"""
        try:
            msg_type = msg.get('T')
            if msg_type == 'b':  # Bar data
                # Create a task to handle the bar data
                asyncio.create_task(self._handle_bar(msg))
            elif msg_type == 't':  # Trade data
                logger.debug(f"Trade received: {msg}")
            elif msg_type == 'q':  # Quote data
                logger.debug(f"Quote received: {msg}")
            elif msg_type == 'success':  # Authentication success
                logger.info("Authentication successful")
            elif msg_type == 'error':  # Error message
                logger.error(f"Stream error: {msg}")
            else:
                logger.warning(f"Unknown message type: {msg}")
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)

    async def _handle_bar(self, bar):
        """Handle incoming bar data"""
        try:
            symbol = bar['S']
            # Convert bar data to DataFrame format
            bar_df = pd.DataFrame([{
                'timestamp': bar['t'],
                'open': bar['o'],
                'high': bar['h'],
                'low': bar['l'],
                'close': bar['c'],
                'volume': bar['v']
            }])
            
            # Update latest bars
            self._latest_bars[symbol] = bar_df
            
            # Call registered callbacks
            for callback in self._callbacks:
                try:
                    await callback(symbol, bar_df)
                except Exception as e:
                    logger.error(f"Error in callback: {e}")
            
        except Exception as e:
            logger.error(f"Error handling bar data: {e}")

    async def stop_streaming(self):
        """Stop streaming market data"""
        logger.info("Stopping market data streaming...")
        
        if self.ws:
            try:
                # Send unsubscribe message for all symbols
                if self.subscribed_symbols:
                    unsubscribe_msg = {
                        "action": "unsubscribe",
                        "trades": list(self.subscribed_symbols),
                        "quotes": list(self.subscribed_symbols),
                        "bars": list(self.subscribed_symbols)
                    }
                    self.ws.send(json.dumps(unsubscribe_msg))
                
                # Close WebSocket connection
                self.ws.close()
                self.ws = None
                
                # Clear subscribed symbols
                self.subscribed_symbols.clear()
                
                # Stop WebSocket thread
                self.ws_running = False
                if self.ws_thread and self.ws_thread.is_alive():
                    self.ws_thread.join(timeout=5)
                    
            except Exception as e:
                logger.error(f"Error stopping WebSocket: {e}", exc_info=True)
        
        logger.info("Market data streaming stopped")

    async def get_historical_bars(self, symbol: str, timeframe: str, start: datetime = None, end: datetime = None) -> pd.DataFrame:
        """Get historical bars for a symbol"""
        try:
            if not start:
                start = datetime.now(pytz.UTC) - timedelta(days=7)
            if not end:
                end = datetime.now(pytz.UTC)

            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=self.timeframe_map[timeframe],
                start=start,
                end=end
            )
            
            bars = self.hist_client.get_stock_bars(request)
            return pd.DataFrame(bars[symbol])
            
        except Exception as e:
            logger.error(f"Error fetching historical bars: {e}")
            return pd.DataFrame()

    def get_latest_bar(self, symbol: str) -> pd.DataFrame:
        """Get the latest bar for a symbol"""
        return self._latest_bars.get(symbol, pd.DataFrame())

    def add_bar_callback(self, callback: Callable):
        """Add a callback to be notified of new bars"""
        self._callbacks.append(callback)

    def remove_bar_callback(self, callback: Callable):
        """Remove a callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def subscribe_to_symbol(self, symbol: str):
        """Subscribe to market data for a symbol"""
        if not self.ws or not self.ws_running:
            logger.warning("WebSocket not connected, cannot subscribe")
            return
            
        if symbol in self.subscribed_symbols:
            logger.info(f"Already subscribed to {symbol}")
            return
            
        # Add to subscribed symbols
        self.subscribed_symbols.add(symbol)
        
        # Send subscription message
        subscribe_msg = {
            "action": "subscribe",
            "trades": [symbol],
            "quotes": [symbol],
            "bars": [symbol],
            "dailyBars": [symbol],
            "statuses": [symbol]
        }
        self.ws.send(json.dumps(subscribe_msg))
        logger.info("Stream subscriptions sent")
