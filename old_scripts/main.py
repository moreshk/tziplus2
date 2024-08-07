from datetime import datetime, timedelta
from plot_chart import plot_chart
import yfinance as yf
import pandas as pd
from utils import calculate_body_and_shadow, identify_fvg, identify_major_highs_lows, identify_bos, identify_demand_zones, identify_supply_zones
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# tickerSymbols = ['SHYAMMETL.NS', 'UDS.NS', 'PVRINOX.NS', 'STAR.NS']

# tickerSymbols = ['SCHAND.NS', 'EKC.NS', 'IOLCP.NS', 'ADSL.NS', 'NILKAMAL.NS', 'RAJESHEXPO.NS', 'HEG.NS', 'UDS.NS']
tickerSymbols = ['PVRINOX.NS']
# List of ticker symbols
# tickerSymbols = [
#     'POWERGRID.NS', 'ULTRACEMCO.NS', 'HEROMOTOCO.NS', 'GRASIM.NS', 'CIPLA.NS', 'NTPC.NS', 'NESTLEIND.NS', 'AXISBANK.NS',
#     'TATASTEEL.NS', 'BRITANNIA.NS', 'LT.NS', 'ADANIPORTS.NS', 'BAJAJFINSV.NS', 'DIVISLAB.NS', 'SBIN.NS', 'HDFCLIFE.NS',
#     'RELIANCE.NS', 'DRREDDY.NS', 'COALINDIA.NS', 'BPCL.NS', 'EICHERMOT.NS', 'ADANIENT.NS', 'BAJAJ-AUTO.NS', 'BHARTIARTL.NS',
#     'TATAMOTORS.NS', 'APOLLOHOSP.NS', 'SHRIRAMFIN.NS', 'SUNPHARMA.NS', 'TATACONSUM.NS', 'SBILIFE.NS', 'ONGC.NS', 'ICICIBANK.NS',
#     'HINDALCO.NS', 'INDUSINDBK.NS', 'ASIANPAINT.NS', 'KOTAKBANK.NS', 'ITC.NS', 'BAJFINANCE.NS', 'MARUTI.NS', 'HDFCBANK.NS',
#     'HINDUNILVR.NS', 'JSWSTEEL.NS', 'M&M.NS', 'TITAN.NS', 'TCS.NS', 'WIPRO.NS', 'HCLTECH.NS', 'LTIM.NS', 'INFY.NS', 'TECHM.NS'
# ]

# Define the interval (e.g., '1d' for daily, '1h' for hourly, '30m' for 30 minutes)
interval = '1d'  # Change this to your desired interval <----------------------------------------

# Get today's date
endDate = datetime.now()

# Get the data for the desired period <-----------------------------------------
startDate = endDate - timedelta(days=180)  # change to your desired period

# Before reading the CSV file, determine the correct index column name
if interval == '1d':
    index_col_name = 'Date'
else:
    index_col_name = 'Datetime'

# Define the file name for storing the data, ensuring it's saved in the 'data' folder
data_folder = 'data'
if not os.path.exists(data_folder):
    os.makedirs(data_folder)  # Create the data folder if it doesn't exist

for tickerSymbol in tickerSymbols:
    fileName = f"{data_folder}/{tickerSymbol}_data_{startDate.strftime('%Y%m%d')}_{endDate.strftime('%Y%m%d')}_{interval}.csv"

    # Check if data is already downloaded
    if os.path.exists(fileName):
        # Load data from CSV file
        tickerData = pd.read_csv(fileName, parse_dates=True, index_col=index_col_name)
        # Convert index to UTC datetime objects if they are timezone-aware
        if tickerData.index.tz is not None:
            tickerData.index = tickerData.index.tz_convert('UTC')
        else:
            tickerData.index = pd.to_datetime(tickerData.index)
    else:
        # Download data if not already downloaded
        tickerData = yf.download(tickerSymbol, start=startDate, end=endDate, interval=interval)
        tickerData = tickerData.round(2)
        # Ensure the index is in datetime format and convert to UTC if timezone-aware
        tickerData.index = pd.to_datetime(tickerData.index, utc=True)
        # Save data to CSV file
        tickerData.to_csv(fileName)
    # Ensure the index is in datetime format
    tickerData.index = pd.to_datetime(tickerData.index)

    # Convert the dates into string format without time
    tickerData['Date'] = tickerData.index.strftime('%Y-%m-%d %H:%M:%S' if interval != '1d' else '%Y-%m-%d')

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

    # Ensure the index is a DatetimeIndex and localize or convert timezone if necessary
    if not isinstance(tickerData.index, pd.DatetimeIndex):
        tickerData.index = pd.to_datetime(tickerData.index)

    # Identify demand zones
    demand_zones = identify_demand_zones(tickerData, major_lows, 10, 1.1)

    # Identify supply zones
    supply_zones = identify_supply_zones(tickerData, major_highs, 10, 1.1)  # Adjust parameters as needed

    # Check if there are any demand and supply zones
    if demand_zones or supply_zones:
        logging.info(f"{tickerSymbol}: Both demand and supply zones are identified.")
        plot_chart(tickerData, fvg_list, demand_zones, supply_zones, major_highs, major_lows, tickerSymbol)
    else:
        logging.info(f"{tickerSymbol}: Either demand or supply zones are not identified.")