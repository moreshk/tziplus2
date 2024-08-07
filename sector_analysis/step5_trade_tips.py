from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import os
import logging
import sys
import pytz
import traceback

# Determine the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add the project root to the system path
sys.path.append(project_root)

# Import modules from the project root
from plot_chart_v2 import plot_chart_v2  # Import the new function

from utils import calculate_body_and_shadow, identify_fvg, identify_major_highs_lows, identify_bos, identify_demand_zones, identify_supply_zones, find_closest_zones

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Read ticker symbols from step4_volatile_tickers.csv
csv_file_path = 'sector_analysis/sector_data/output/step4_volatile_tickers.csv'
ticker_data_df = pd.read_csv(csv_file_path)
tickerSymbols = ticker_data_df['Ticker'].tolist()

# Define the interval
interval = '15m'

# Get today's date
endDate = datetime.now(pytz.timezone('Asia/Kolkata')).replace(hour=0, minute=0, second=0, microsecond=0)

# Get the data for the desired period (last 7 days)
startDate = endDate - timedelta(days=7)

# Define the file name for storing the data
data_folder = 'sector_analysis/sector_data/input'
if not os.path.exists(data_folder):
    os.makedirs(data_folder)

# List to store tickers that meet the criteria
identified_tickers = []

for tickerSymbol in tickerSymbols:
    fileName = f"{data_folder}/{tickerSymbol}_data_{startDate.strftime('%Y%m%d')}_{endDate.strftime('%Y%m%d')}_{interval}.csv"

    try:
        if os.path.exists(fileName):
            tickerData = pd.read_csv(fileName, parse_dates=['Datetime'], index_col='Datetime')
            logging.info(f"Loaded existing data for {tickerSymbol}")
        else:
            logging.info(f"Downloading data for {tickerSymbol}")
            tickerData = yf.download(tickerSymbol, start=startDate, end=endDate, interval=interval)
            if tickerData.empty:
                logging.warning(f"No data available for {tickerSymbol}. Skipping...")
                continue
            tickerData = tickerData.round(2)
            tickerData.to_csv(fileName)
            logging.info(f"Data saved for {tickerSymbol}")

        if tickerData.empty:
            logging.warning(f"No data available for {tickerSymbol} after processing. Skipping...")
            continue

        logging.info(f"Processing {tickerSymbol}")
        
        # Ensure the index is in datetime format and convert to Asia/Kolkata timezone
        tickerData.index = pd.to_datetime(tickerData.index, utc=True).tz_convert('Asia/Kolkata')
        
        # Convert the dates into string format
        tickerData['Date'] = tickerData.index.strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            tickerData = calculate_body_and_shadow(tickerData)
        except Exception as e:
            logging.error(f"Error in calculate_body_and_shadow for {tickerSymbol}: {str(e)}")
            logging.error(traceback.format_exc())
            continue

        try:
            fvg_list = identify_fvg(tickerData)
        except Exception as e:
            logging.error(f"Error in identify_fvg for {tickerSymbol}: {str(e)}")
            logging.error(traceback.format_exc())
            fvg_list = []

        try:
            major_highs, major_lows = identify_major_highs_lows(tickerData)
        except Exception as e:
            logging.error(f"Error in identify_major_highs_lows for {tickerSymbol}: {str(e)}")
            logging.error(traceback.format_exc())
            major_highs, major_lows = [], []

        try:
            bos_list = identify_bos(tickerData, major_highs, major_lows)
        except Exception as e:
            logging.error(f"Error in identify_bos for {tickerSymbol}: {str(e)}")
            logging.error(traceback.format_exc())
            bos_list = []
        
        # Reset the index and set 'Date' as the new index
        tickerData.reset_index(drop=True, inplace=True)
        tickerData.set_index('Date', inplace=True)

        try:
            demand_zones = identify_demand_zones(tickerData, major_lows, 10, 1.1)
        except Exception as e:
            logging.error(f"Error in identify_demand_zones for {tickerSymbol}: {str(e)}")
            logging.error(traceback.format_exc())
            demand_zones = []

        try:
            supply_zones = identify_supply_zones(tickerData, major_highs, 10, 1.1)
        except Exception as e:
            logging.error(f"Error in identify_supply_zones for {tickerSymbol}: {str(e)}")
            logging.error(traceback.format_exc())
            supply_zones = []

        try:
            closest_demand, closest_supply = find_closest_zones(tickerData, demand_zones, supply_zones)
        except Exception as e:
            logging.error(f"Error in find_closest_zones for {tickerSymbol}: {str(e)}")
            logging.error(traceback.format_exc())
            closest_demand, closest_supply = None, None

        if closest_demand is not None and closest_supply is not None:
            last_low = tickerData.iloc[-1]['Low']
            last_high = tickerData.iloc[-1]['High']
            last_close = tickerData.iloc[-1]['Close']
            closest_demand_high = tickerData.iloc[closest_demand]['High']
            closest_supply_low = tickerData.iloc[closest_supply]['Low']
            threshold_demand = closest_demand_high * 1.05
            threshold_supply = closest_supply_low * 0.95

            demand_condition_met = last_low <= threshold_demand and last_low > closest_demand_high
            supply_condition_met = last_high < threshold_supply

            if demand_condition_met and supply_condition_met:
                logging.info(f"{tickerSymbol}: Both demand and supply conditions are met.")
                plot_chart_v2(tickerData, fvg_list, demand_zones, supply_zones, major_highs, major_lows, tickerSymbol)
                identified_tickers.append({
                    'Ticker': tickerSymbol,
                    'Sector': ticker_data_df[ticker_data_df['Ticker'] == tickerSymbol]['Sector'].values[0],
                    'Change in Daily Average %': ticker_data_df[ticker_data_df['Ticker'] == tickerSymbol]['Change in Daily Average %'].values[0],
                    'Average Volatility': ticker_data_df[ticker_data_df['Ticker'] == tickerSymbol]['Average Volatility'].values[0],
                    'Last Close': last_close,
                    'Closest Demand': closest_demand,
                    'Closest Supply': closest_supply
                })
            else:
                if not demand_condition_met:
                    logging.info(f"{tickerSymbol}: Demand condition not met.")
                if not supply_condition_met:
                    logging.info(f"{tickerSymbol}: Supply condition not met.")
        else:
            logging.info(f"{tickerSymbol}: Either demand or supply zones are not identified.")
    except Exception as e:
        logging.error(f"Error processing {tickerSymbol}: {str(e)}")
        logging.error(traceback.format_exc())

# Save identified tickers to CSV
output_csv_path = 'sector_analysis/sector_data/output/step5_trade_tips.csv'
if identified_tickers:
    identified_tickers_df = pd.DataFrame(identified_tickers)
    identified_tickers_df.to_csv(output_csv_path, index=False)
    print(f"Trade tips saved to {output_csv_path}")
else:
    print("No tickers identified for trade tips.")