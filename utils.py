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
    for i in range(1, len(tickerData) - 1):
        first_candle = tickerData.iloc[i - 1]
        third_candle = tickerData.iloc[i + 1]
        
        if first_candle['High'] < third_candle['Low']:
            fvg_list.append((i - 1, i + 1, 'Bullish'))
            
        if first_candle['Low'] > third_candle['High']:
            fvg_list.append((i - 1, i + 1, 'Bearish'))
    
    return fvg_list


def identify_major_highs_lows(tickerData, window=5):
    major_highs = []
    major_lows = []

    for i in range(window, len(tickerData) - window):
        current_high = tickerData.iloc[i]['High']
        current_low = tickerData.iloc[i]['Low']
        
        preceding_highs = tickerData.iloc[i - window:i]['High']
        following_highs = tickerData.iloc[i + 1:i + 1 + window]['High']
        preceding_lows = tickerData.iloc[i - window:i]['Low']
        following_lows = tickerData.iloc[i + 1:i + 1 + window]['Low']
        
        if current_high > preceding_highs.max() and current_high > following_highs.max():
            major_highs.append(i)
        
        if current_low < preceding_lows.min() and current_low < following_lows.min():
            major_lows.append(i)
    
    return major_highs, major_lows

def identify_bos(tickerData, major_highs, major_lows):
    bos_list = []

    for i in range(1, len(tickerData)):
        current_candle = tickerData.iloc[i]

        for high_index in major_highs:
            if i > high_index:
                major_high_value = tickerData.iloc[high_index]['High']
                if current_candle['Open'] < major_high_value and current_candle['Close'] > major_high_value:
                    bos_list.append((i, 'Bullish'))
                    break

        for low_index in major_lows:
            if i > low_index:
                major_low_value = tickerData.iloc[low_index]['Low']
                if current_candle['Open'] > major_low_value and current_candle['Close'] < major_low_value:
                    bos_list.append((i, 'Bearish'))
                    break
    
    return bos_list

def identify_demand_zones(tickerData, major_lows, candles_count, comparison_multiplier):
    """Identify demand zones based on major lows and absolute differences, with customizable parameters for analysis,
    ensuring no candle to the right has a low lower than the high of the demand zone candle."""
    demand_zones = []

    # Calculate average body size and volume for boring candle detection
    average_body_size = calculate_average_body_size(tickerData)
    average_volume = calculate_average_volume(tickerData)

    for low_pos in major_lows:
        # Ensure there are enough candles before and after the major low
        if low_pos > candles_count - 1 and low_pos < len(tickerData) - candles_count:
            candle = tickerData.iloc[low_pos]
            logging.debug(f"Checking major low at position {low_pos}: {candle.to_dict()}")
            # Check if the major low is not a boring candle
            if not is_boring_candle(candle, average_body_size, average_volume):
                logging.info(f"Skipping non-boring candle at position {low_pos}: {candle.to_dict()}")
                continue  # Skip this major low if it is not a boring candle

            # Check if at least one of the next three candles is a bullish exciting candle
            has_bullish_exciting_candle = False
            for i in range(1, 6):
                if low_pos + i < len(tickerData):
                    next_candle = tickerData.iloc[low_pos + i]
                    is_exciting, candle_type = is_exciting_candle(next_candle, average_body_size, average_volume)
                    if is_exciting and candle_type == 'Bullish':
                        has_bullish_exciting_candle = True
                        break

            if not has_bullish_exciting_candle:
                logging.info(f"No bullish exciting candle found in the next three candles after position {low_pos}")
                continue  # Skip this major low if no bullish exciting candle is found

            logging.debug(f"Processing major low at position {low_pos}: {candle.to_dict()}")
            # Get the 'Low' of the candle 'candles_count' positions before the major low
            pre_low = tickerData.iloc[low_pos - candles_count]['Low']
            # Get the 'Low' of the candle 'candles_count' positions after the major low
            post_low = tickerData.iloc[low_pos + candles_count]['Low']
            # Get the 'High' of the demand zone candle (major low candle)
            demand_zone_high = candle['High']
            major_low = candle['Low']

            # Calculate the absolute differences
            abs_diff_decline = abs(major_low - pre_low)
            abs_diff_increase = abs(post_low - major_low)

            if abs_diff_increase > comparison_multiplier * abs_diff_decline:
                # Check for any candle to the right with a close lower than the close of the demand zone candle
                invalid_zone = False
                for i in range(low_pos + 1, len(tickerData)):
                    if tickerData.iloc[i]['Close'] < candle['High']:
                        invalid_zone = True
                        break

                if not invalid_zone:
                    demand_zones.append(low_pos)
                    logging.info(f"Demand zone identified at position {low_pos}: {candle.to_dict()}, "
                                 f"Average body size: {average_body_size}, Average volume: {average_volume}, "
                                 f"Body size: {abs(candle['Open'] - candle['Close'])}, Volume: {candle['Volume']}")

    if not demand_zones:
        logging.info("No demand zones were identified.")
    return demand_zones


def identify_supply_zones(tickerData, major_highs, candles_count, comparison_multiplier):
    """Identify supply zones based on major highs and absolute differences, with customizable parameters for analysis,
    ensuring no candle to the right has a high higher than the low of the supply zone candle."""
    supply_zones = []

    # Calculate average body size and volume for boring candle detection
    average_body_size = calculate_average_body_size(tickerData)
    average_volume = calculate_average_volume(tickerData)

    for high_pos in major_highs:
        # Ensure there are enough candles before and after the major high
        if high_pos > candles_count - 1 and high_pos < len(tickerData) - candles_count:
            candle = tickerData.iloc[high_pos]
            logging.debug(f"Checking major high at position {high_pos}: {candle.to_dict()}")
            # Check if the major high is not a boring candle
            if not is_boring_candle(candle, average_body_size, average_volume):
                logging.info(f"Skipping non-boring candle at position {high_pos}: {candle.to_dict()}")
                continue  # Skip this major high if it is not a boring candle

            # Check if at least one of the next three candles is a bearish exciting candle
            has_bearish_exciting_candle = False
            for i in range(1, 6):
                if high_pos + i < len(tickerData):
                    next_candle = tickerData.iloc[high_pos + i]
                    is_exciting, candle_type = is_exciting_candle(next_candle, average_body_size, average_volume)
                    if is_exciting and candle_type == 'Bearish':
                        has_bearish_exciting_candle = True
                        break

            if not has_bearish_exciting_candle:
                logging.info(f"No bearish exciting candle found in the next three candles after position {high_pos}")
                continue  # Skip this major high if no bearish exciting candle is found

            logging.debug(f"Processing major high at position {high_pos}: {candle.to_dict()}")
            # Get the 'High' of the candle 'candles_count' positions before the major high
            pre_high = tickerData.iloc[high_pos - candles_count]['High']
            # Get the 'High' of the candle 'candles_count' positions after the major high
            post_high = tickerData.iloc[high_pos + candles_count]['High']
            # Get the 'Low' of the supply zone candle (major high candle)
            supply_zone_low = candle['Low']
            major_high = candle['High']

            # Calculate the absolute differences
            abs_diff_increase = abs(major_high - pre_high)
            abs_diff_decline = abs(post_high - major_high)

            # Check if the absolute decline is more than the absolute increase by a factor of the comparison_multiplier
            if abs_diff_decline > comparison_multiplier * abs_diff_increase:
                # Check for any candle to the right with a close higher than the high of the supply zone candle
                invalid_zone = False
                for i in range(high_pos + 1, len(tickerData)):
                    if tickerData.iloc[i]['Close'] > candle['Low']:
                        invalid_zone = True
                        break

                if not invalid_zone:
                    supply_zones.append(high_pos)
                    logging.info(f"Supply zone identified at position {high_pos}: {candle.to_dict()}, "
                                 f"Average body size: {average_body_size}, Average volume: {average_volume}, "
                                 f"Body size: {abs(candle['Open'] - candle['Close'])}, Volume: {candle['Volume']}")

    if not supply_zones:
        logging.info("No supply zones were identified.")
    return supply_zones

def calculate_average_body_size(tickerData):
    """Calculate the average body size of the candles (absolute of open minus close)."""
    valid_data = tickerData.dropna(subset=['Open', 'Close'])
    average_body_size = (valid_data['Open'] - valid_data['Close']).abs().mean()
    return average_body_size

def calculate_average_volume(tickerData):
    """Calculate the average volume of the candles."""
    valid_data = tickerData.dropna(subset=['Volume'])
    average_volume = valid_data['Volume'].mean()
    return average_volume


def is_boring_candle(candle, average_body_size, average_volume):
    """Identify if a particular candle is a boring candle.
    
    A boring candle has:
    - Body size lower than the average body size
    - Volume lower than the average volume
    - Body size lower than its total wick (upper shadow + lower shadow)
    """
    body_size = abs(candle['Open'] - candle['Close'])
    lower_shadow = min(candle['Open'], candle['Close']) - candle['Low']
    upper_shadow = candle['High'] - max(candle['Open'], candle['Close'])
    total_wick = lower_shadow + upper_shadow

    is_boring = (body_size < average_body_size and
                #  candle['Volume'] < average_volume and
                 body_size <= 0.75 * total_wick)

    logging.info(f"Checking candle at position: {candle.name}, Body size: {body_size}, "
                 f"Lower shadow: {lower_shadow}, Upper shadow: {upper_shadow}, Total wick: {total_wick}, "
                 f"Average body size: {average_body_size}, Average volume: {average_volume}, "
                 f"Volume: {candle['Volume']}, Is boring: {is_boring}")

    return is_boring

def is_exciting_candle(candle, average_body_size, average_volume):
    """Identify if a particular candle is an exciting candle and its type (bullish or bearish).
    
    An exciting candle has:
    - Volume higher than the average volume
    - Body size at least 1.5 times the average body size
    - Body size at least 2 times the total wicks (upper shadow + lower shadow)
    
    Returns:
    - is_exciting (bool): Whether the candle is exciting
    - type (str): 'Bullish' if the candle is bullish exciting, 'Bearish' if the candle is bearish exciting, 
                  'None' if the candle is not exciting
    """
    body_size = abs(candle['Open'] - candle['Close'])
    lower_shadow = min(candle['Open'], candle['Close']) - candle['Low']
    upper_shadow = candle['High'] - max(candle['Open'], candle['Close'])
    total_wick = lower_shadow + upper_shadow

    is_volume_exciting = candle['Volume'] > average_volume
    is_body_size_exciting = body_size >= average_body_size
    is_body_size_greater_than_wick = body_size >= total_wick

    is_exciting = is_volume_exciting and is_body_size_exciting and is_body_size_greater_than_wick

    if is_exciting:
        if candle['Close'] > candle['Open']:
            candle_type = 'Bullish'
        else:
            candle_type = 'Bearish'
    else:
        candle_type = 'None'

    logging.info(f"Checking candle at position: {candle.name}, Body size: {body_size}, "
                 f"Lower shadow: {lower_shadow}, Upper shadow: {upper_shadow}, Total wick: {total_wick}, "
                 f"Average body size: {average_body_size}, Average volume: {average_volume}, "
                 f"Volume: {candle['Volume']}, Is volume exciting: {is_volume_exciting}, "
                 f"Is body size exciting: {is_body_size_exciting}, Is body size greater than wick: {is_body_size_greater_than_wick}, "
                 f"Is exciting: {is_exciting}, Type: {candle_type}")

    return is_exciting, candle_type