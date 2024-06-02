
from datetime import datetime, timedelta
from plot_chart import plot_chart
import yfinance as yf
import pandas as pd
from utils import calculate_body_and_shadow, identify_fvg, identify_major_highs_lows, identify_bos
import os
import logging

# Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime=s - %(message=s')
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Define the ticker symbol
tickerSymbol = '^NSEI'

# Get today's date
endDate = datetime.now()

# Get the data for the desired period
startDate = endDate - timedelta(days=360)  # change to your desired period

# Define the file name for storing the data
fileName = f"{tickerSymbol}_data_{startDate.strftime('%Y%m%d')}_{endDate.strftime('%Y%m%d')}.csv"

# Check if data is already downloaded
if os.path.exists(fileName):
    # Load data from CSV file
    tickerData = pd.read_csv(fileName, parse_dates=True, index_col='Date')
else:
    # Download data if not already downloaded
    tickerData = yf.download(tickerSymbol, start=startDate, end=endDate)
    tickerData = tickerData.round(2)
    # Save data to CSV file
    tickerData.to_csv(fileName)

# Ensure the index is in datetime format
tickerData.index = pd.to_datetime(tickerData.index)

# Print the dates in tickerData
logging.info(f"Dates in tickerData: {tickerData.index}")

# Convert the dates into string format without time
tickerData['Date'] = tickerData.index.strftime('%Y-%m-%d')

# Calculate body and shadow
tickerData = calculate_body_and_shadow(tickerData)

# Identify FVGs
fvg_list = identify_fvg(tickerData)

# Identify major highs and lows
major_highs, major_lows = identify_major_highs_lows(tickerData)

# Identify break of structure (BoS)
bos_list = identify_bos(tickerData, major_highs, major_lows)

# Convert the index to integers for pattern detection
tickerData.reset_index(drop=True, inplace=True)

# Set 'Date' as the index
tickerData.set_index('Date', inplace=True)

# Plot the chart with FVGs and major highs/lows
plot_chart(tickerData, fvg_list, major_highs, major_lows, bos_list)

# Log the major highs and lows, and BoS
logging.info(f"Major highs: {major_highs}")
logging.info(f"Major lows: {major_lows}")
logging.info(f"Break of Structure: {bos_list}")