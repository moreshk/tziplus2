import os
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Read ticker symbols from NSE200.csv without a header
ticker_symbols = pd.read_csv('NSE200.csv', header=None)[0].tolist()

# Define the interval and time period
interval = '1h'
end_date = datetime.now()
start_date = end_date - timedelta(days=360)  # 6 months

# Create the chart_data folder if it doesn't exist
chart_data_folder = 'chart_data'
if not os.path.exists(chart_data_folder):
    os.makedirs(chart_data_folder)

for ticker_symbol in ticker_symbols:
    file_name = f"{chart_data_folder}/{ticker_symbol}_data_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_{interval}.csv"

    # Check if data is already downloaded
    if os.path.exists(file_name):
        logging.info(f"{ticker_symbol}: Data already exists. Skipping download.")
        continue

    # Download data
    logging.info(f"{ticker_symbol}: Downloading data...")
    ticker_data = yf.download(ticker_symbol, start=start_date, end=end_date, interval=interval)
    
    if ticker_data.empty:
        logging.warning(f"{ticker_symbol}: No data available. Skipping.")
        continue

    ticker_data = ticker_data.round(2)
    
    # Ensure the index is in datetime format and convert to UTC if timezone-aware
    ticker_data.index = pd.to_datetime(ticker_data.index, utc=True)
    
    # Save data to CSV file
    ticker_data.to_csv(file_name)
    logging.info(f"{ticker_symbol}: Data saved to {file_name}")

logging.info("Data download completed for all available symbols.")