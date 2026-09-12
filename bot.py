
import os
import yfinance as yf
import pandas_ta as ta
import requests
import time

# Pulls your secure token from GitHub Actions Secrets
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") 
# Replace this with your actual numeric Channel ID (keep the quotes)
CHANNEL_ID = "YOUR_CHANNEL_ID_HERE"

# --- Configuration ---
# List of assets you want to track
TICKERS = ["BTC-USD", "ETH-USD", "SOL-USD", "AAPL", "MSFT"] 
SHORT_WINDOW = 20
LONG_WINDOW = 50
RSI_LENGTH = 14
RSI_OVERBOUGHT = 70
BUFFER_PCT = 0.002  # 0.2% buffer to prevent choppy false alerts

def send_telegram_alert(message):
    """Sends the formatted message to your Telegram channel."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

def check_crossover_with_rsi(ticker):
    """Fetches hourly data, calculates indicators, and sends alerts."""
    print(f"Analyzing {ticker}...")
    
    # Fetching 1-hour interval data for the last month
    data = yf.Ticker(ticker).history(period="1mo", interval="1h")
    
    if data.empty:
        print(f"Failed to fetch data for {ticker}.")
        return

    # Calculate Moving Averages and RSI
    data['SMA_Short'] = data['Close'].rolling(window=SHORT_WINDOW).mean()
    data['SMA_Long'] = data['Close'].rolling(window=LONG_WINDOW).mean()
    data.ta.rsi(length=RSI_LENGTH, append=True)
    
    # Isolate yesterday's and today's completed hourly candles
    yesterday = data.iloc[-2]
    today = data.iloc[-1]
    
    y_short, y_long = yesterday['SMA_Short'], yesterday['SMA_Long']
    t_short, t_long = today['SMA_Short'], today['SMA_Long']
    current_price = today['Close']
    current_rsi = today[f'RSI_{RSI_LENGTH}']
    
    # Check for Bullish Crossover with Buffer and RSI filter
    if y_short <= y_long and t_short > (t_long * (1 + BUFFER_PCT)):
        if current_rsi < RSI_OVERBOUGHT:
            msg = f"🟢 *BULLISH CROSSOVER* 🟢\n\n*Asset:* {ticker}\n*Price:* ${current_price:.2f}\n*RSI:* {current_rsi:.1f}"
            send_telegram_alert(msg)
            print(f"Bullish alert sent for {ticker}!")
        else:
            print(f"[{ticker}] Ignored: RSI is overbought at {current_rsi:.1f}")
            
    # Check for Bearish Crossover with Buffer
    elif y_short >= y_long and t_short < (t_long * (1 - BUFFER_PCT)):
        msg = f"🔴 *BEARISH CROSSOVER* 🔴\n\n*Asset:* {ticker}\n*Price:* ${current_price:.2f}\n*RSI:* {current_rsi:.1f}"
        send_telegram_alert(msg)
        print(f"Bearish alert sent for {ticker}!")
        
    else:
        print(f"No crossover detected for {ticker}.")

if __name__ == "__main__":
    # Loop through the list and process each asset
    for ticker in TICKERS:
        check_crossover_with_rsi(ticker)
        time.sleep(1) # Pauses for 1 second to avoid rate limits
