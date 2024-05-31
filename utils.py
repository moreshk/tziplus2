import numpy as np
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_body_and_shadow(tickerData):
    """Calculate the body size and the upper and lower shadow sizes."""
    tickerData['Body'] = abs(tickerData['Open'] - tickerData['Close'])
    tickerData['Lower Shadow'] = tickerData[['Open', 'Close']].min(axis=1) - tickerData['Low']
    tickerData['Upper Shadow'] = tickerData['High'] - tickerData[['Open', 'Close']].max(axis=1)
    return tickerData


# def identify_fvg(tickerData):
#     """Identify Fair Value Gaps (FVG) in the data."""
#     fvg_list = []
#     # Adjust the range to ensure we have a next candle to compare with
#     for i in range(1, len(tickerData) - 2):  # Adjusted to -2 to access the third candle
#         first_candle = tickerData.iloc[i - 1]
#         third_candle = tickerData.iloc[i + 1]  # This is now the third candle
        
#         # Bullish FVG: Check if there's a gap between the high of the first candle and the low of the third candle
#         if first_candle['High'] < third_candle['Low']:
#             fvg_list.append((tickerData.index[i - 1].normalize(), tickerData.index[i + 1].normalize(), 'Bullish'))
#             logging.info(f"Bullish FVG identified between {tickerData.index[i - 1].normalize()} and {tickerData.index[i + 1].normalize()}")
        
#         # Bearish FVG: Check if there's a gap between the low of the first candle and the high of the third candle
#         if first_candle['Low'] > third_candle['High']:
#             fvg_list.append((tickerData.index[i - 1].normalize(), tickerData.index[i + 1].normalize(), 'Bearish'))
#             logging.info(f"Bearish FVG identified between {tickerData.index[i - 1].normalize()} and {tickerData.index[i + 1].normalize()}")
    
#     logging.info(f"Total FVGs identified: {len(fvg_list)}")
#     return fvg_list


def identify_fvg(tickerData):
    """Identify Fair Value Gaps (FVG) in the data."""
    fvg_list = []
    # Adjust the range to ensure we have a next candle to compare with
    for i in range(1, len(tickerData) - 1):  # Adjusted to -1 to access the third-to-last candle
        first_candle = tickerData.iloc[i - 1]
        third_candle = tickerData.iloc[i + 1]  # This is now the third candle
        
        # Bullish FVG: Check if there's a gap between the high of the first candle and the low of the third candle
        if first_candle['High'] < third_candle['Low']:
            fvg_list.append((tickerData.index[i - 1].normalize(), tickerData.index[i + 1].normalize(), 'Bullish'))
            logging.info(f"Bullish FVG identified between {tickerData.index[i - 1].normalize()} and {tickerData.index[i + 1].normalize()}")
        
        # Bearish FVG: Check if there's a gap between the low of the first candle and the high of the third candle
        if first_candle['Low'] > third_candle['High']:
            fvg_list.append((tickerData.index[i - 1].normalize(), tickerData.index[i + 1].normalize(), 'Bearish'))
            logging.info(f"Bearish FVG identified between {tickerData.index[i - 1].normalize()} and {tickerData.index[i + 1].normalize()}")
    
    logging.info(f"Total FVGs identified: {len(fvg_list)}")
    return fvg_list