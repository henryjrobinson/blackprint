from dotenv import load_dotenv, find_dotenv
import os
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient

def test_connection():
    print("Loading environment variables...")
    dotenv_path = find_dotenv()
    print(f"Loading .env file from: {dotenv_path}")
    
    # Read file directly first
    print("\nDirect file contents (first line with API key):")
    with open(dotenv_path, 'r') as f:
        for line in f:
            if 'ALPACA_API_KEY' in line:
                print(f"Raw line from file: {line.strip()}")
                break
    
    # Now load through dotenv
    load_dotenv(dotenv_path)
    
    # Get API credentials from environment variables
    api_key = os.getenv('ALPACA_API_KEY')
    api_secret = os.getenv('ALPACA_API_SECRET')
    
    # Debug prints
    print("\nAPI Key details:")
    print(f"- Found: {'Yes' if api_key else 'No'}")
    if api_key:
        print(f"- First 4 chars (lowercase): {api_key[:4].lower()}")
        print(f"- First 4 chars (original): {api_key[:4]}")
        print(f"- Length: {len(api_key)}")
        print(f"- Contains whitespace: {'Yes' if any(c.isspace() for c in api_key) else 'No'}")
    
    print("\nAPI Secret details:")
    print(f"- Found: {'Yes' if api_secret else 'No'}")
    if api_secret:
        print(f"- Length: {len(api_secret)}")
        print(f"- Contains whitespace: {'Yes' if any(c.isspace() for c in api_secret) else 'No'}")
    
    if not api_key or not api_secret:
        print("ERROR: Missing API credentials in environment variables!")
        return
    
    print("\nTesting Trading API connection...")
    trading_client = TradingClient(api_key, api_secret, paper=True)
    try:
        account = trading_client.get_account()
        print(f"Connection successful! Account status: {account.status}")
        print(f"Cash balance: ${float(account.cash)}")
    except Exception as e:
        print(f"Error connecting to Alpaca: {str(e)}")
        print("Full error details:", e)
    
    print("\nTesting Market Data API connection...")
    data_client = StockHistoricalDataClient(api_key, api_secret)
    try:
        data_client.get_stock_latest_bar("AAPL")
        print("Market Data API connection successful!")
    except Exception as e:
        print(f"Market Data API error: {e}")

if __name__ == "__main__":
    test_connection()
