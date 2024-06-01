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



def identify_major_highs_lows(tickerData, window=5):
    """
    Identify major highs and major lows in the data.
    
    A major high is defined as a high point that is higher than the highs of the preceding and following `window` candles.
    A major low is defined as a low point that is lower than the lows of the preceding and following `window` candles.
    
    Parameters:
    - tickerData: DataFrame containing the OHLC data.
    - window: Number of candles to consider before and after for identifying major highs and lows.
    
    Returns:
    - major_highs: List of indices where major highs are identified.
    - major_lows: List of indices where major lows are identified.
    """
    major_highs = []
    major_lows = []

    for i in range(window, len(tickerData) - window):
        # Get the high and low of the current candle
        current_high = tickerData.iloc[i]['High']
        current_low = tickerData.iloc[i]['Low']
        
        # Get the highs and lows of the preceding and following `window` candles
        preceding_highs = tickerData.iloc[i - window:i]['High']
        following_highs = tickerData.iloc[i + 1:i + 1 + window]['High']
        preceding_lows = tickerData.iloc[i - window:i]['Low']
        following_lows = tickerData.iloc[i + 1:i + 1 + window]['Low']
        
        # Check if the current high is higher than all preceding and following highs
        if current_high > preceding_highs.max() and current_high > following_highs.max():
            major_highs.append(tickerData.index[i])
            logging.info(f"Major high identified at {tickerData.index[i]} with high {current_high}")
        
        # Check if the current low is lower than all preceding and following lows
        if current_low < preceding_lows.min() and current_low < following_lows.min():
            major_lows.append(tickerData.index[i])
            logging.info(f"Major low identified at {tickerData.index[i]} with low {current_low}")

    logging.info(f"Total major highs identified: {len(major_highs)}")
    logging.info(f"Total major lows identified: {len(major_lows)}")
    
    return major_highs, major_lows