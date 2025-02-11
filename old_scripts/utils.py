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
            for offset in range(3):  # Check the major low and the next 2 candles
                current_pos = low_pos + offset
                if current_pos >= len(tickerData):
                    break

                candle = tickerData.iloc[current_pos]
                logging.debug(f"Checking major low at position {current_pos}: {candle.to_dict()}")
                # Check if the major low is not a boring candle
                if not is_boring_candle(candle, average_body_size, average_volume):
                    logging.info(f"Skipping non-boring candle at position {current_pos}: {candle.to_dict()}")
                    continue  # Skip this major low if it is not a boring candle

                has_bullish_signal = False

                # Check if at least one of the next few candles is a bullish exciting candle or a bullish FVG
                for i in range(1, 6):
                    if current_pos + i < len(tickerData):
                        next_candle = tickerData.iloc[current_pos + i]
                        is_exciting, candle_type = is_exciting_candle(next_candle, average_body_size, average_volume)
                        if is_exciting and candle_type == 'Bullish':
                            has_bullish_signal = True
                            break

                # Check for bullish FVG in the next few candles
                if not has_bullish_signal:
                    fvg_list = identify_fvg(tickerData.iloc[current_pos:current_pos + 6])
                    for fvg in fvg_list:
                        if fvg[2] == 'Bullish':
                            has_bullish_signal = True
                            break

                # Compulsory check for an exciting candle in the couple of candles to the immediate left
                has_exciting_left = False
                for i in range(1, 3):
                    if current_pos - i >= 0:
                        prev_candle = tickerData.iloc[current_pos - i]
                        is_exciting, _ = is_exciting_candle(prev_candle, average_body_size, average_volume)
                        if is_exciting:
                            has_exciting_left = True
                            break

                if not has_bullish_signal or not has_exciting_left:
                    logging.info(f"No valid signal found around position {current_pos}")
                    continue  # Skip this major low if no valid signal is found

                logging.debug(f"Processing major low at position {current_pos}: {candle.to_dict()}")
                # Get the 'Low' of the candle 'candles_count' positions before the major low
                pre_low = tickerData.iloc[current_pos - candles_count]['Low']
                # Ensure the 'Low' of the candle 'candles_count' positions after the major low is within bounds
                if current_pos + candles_count < len(tickerData):
                    post_low = tickerData.iloc[current_pos + candles_count]['Low']
                else:
                    continue  # Skip if out of bounds
                # Get the 'High' of the demand zone candle (major low candle)
                demand_zone_high = candle['High']

                # Check for any candle to the right with a close lower than the close of the demand zone candle
                invalid_zone = False
                for i in range(current_pos + 1, len(tickerData)):
                    if tickerData.iloc[i]['Close'] < candle['Close']:
                        invalid_zone = True
                        break

                if not invalid_zone:
                    demand_zones.append(current_pos)
                    logging.info(f"Demand zone identified at position {current_pos}: {candle.to_dict()}, "
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
            for offset in range(3):  # Check the major high and the next 2 candles
                current_pos = high_pos + offset
                if current_pos >= len(tickerData):
                    break

                candle = tickerData.iloc[current_pos]
                logging.debug(f"Checking major high at position {current_pos}: {candle.to_dict()}")
                # Check if the major high is not a boring candle
                if not is_boring_candle(candle, average_body_size, average_volume):
                    logging.info(f"Skipping non-boring candle at position {current_pos}: {candle.to_dict()}")
                    continue  # Skip this major high if it is not a boring candle

                has_bearish_signal = False

                # Check if at least one of the next few candles is a bearish exciting candle or a bearish FVG
                for i in range(1, 6):
                    if current_pos + i < len(tickerData):
                        next_candle = tickerData.iloc[current_pos + i]
                        is_exciting, candle_type = is_exciting_candle(next_candle, average_body_size, average_volume)
                        if is_exciting and candle_type == 'Bearish':
                            has_bearish_signal = True
                            break

                # Check for bearish FVG in the next few candles
                if not has_bearish_signal:
                    fvg_list = identify_fvg(tickerData.iloc[current_pos:current_pos + 6])
                    for fvg in fvg_list:
                        if fvg[2] == 'Bearish':
                            has_bearish_signal = True
                            break

                # Compulsory check for an exciting candle in the couple of candles to the immediate left
                has_exciting_left = False
                for i in range(1, 3):
                    if current_pos - i >= 0:
                        prev_candle = tickerData.iloc[current_pos - i]
                        is_exciting, _ = is_exciting_candle(prev_candle, average_body_size, average_volume)
                        if is_exciting:
                            has_exciting_left = True
                            break

                if not has_bearish_signal or not has_exciting_left:
                    logging.info(f"No valid signal found around position {current_pos}")
                    continue  # Skip this major high if no valid signal is found

                logging.debug(f"Processing major high at position {current_pos}: {candle.to_dict()}")
                # Get the 'High' of the candle 'candles_count' positions before the major high
                pre_high = tickerData.iloc[current_pos - candles_count]['High']
                # Ensure the 'High' of the candle 'candles_count' positions after the major high is within bounds
                if current_pos + candles_count < len(tickerData):
                    post_high = tickerData.iloc[current_pos + candles_count]['High']
                else:
                    continue  # Skip if out of bounds
                # Get the 'Low' of the supply zone candle (major high candle)
                supply_zone_low = candle['Low']

                # Check for any candle to the right with a close higher than the high of the supply zone candle
                invalid_zone = False
                for i in range(current_pos + 1, len(tickerData)):
                    if tickerData.iloc[i]['Close'] > candle['Close']:
                        invalid_zone = True
                        break

                if not invalid_zone:
                    supply_zones.append(current_pos)
                    logging.info(f"Supply zone identified at position {current_pos}: {candle.to_dict()}, "
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
    - Body size lower than half of the absolute difference between high and low
    """
    body_size = abs(candle['Open'] - candle['Close'])
    high_low_diff = abs(candle['High'] - candle['Low'])

    # is_boring = (body_size < average_body_size and
    #              body_size <= 0.5 * high_low_diff)
    
    is_boring = (body_size <= 0.5 * high_low_diff)

    logging.info(f"Checking candle at position: {candle.name}, Body size: {body_size}, "
                 f"High-Low difference: {high_low_diff}, "
                 f"Average body size: {average_body_size}, Average volume: {average_volume}, "
                 f"Volume: {candle['Volume']}, Is boring: {is_boring}")

    return is_boring



def is_exciting_candle(candle, average_body_size, average_volume):
    """Identify if a particular candle is an exciting candle and its type (bullish or bearish).
    
    An exciting candle has:
    - Volume higher than the average volume
    - Body size at least 1.5 times the average body size
    - Body size at least 50% of the absolute difference between high and low
    
    Returns:
    - is_exciting (bool): Whether the candle is exciting
    - type (str): 'Bullish' if the candle is bullish exciting, 'Bearish' if the candle is bearish exciting, 
                  'None' if the candle is not exciting
    """
    body_size = abs(candle['Open'] - candle['Close'])
    high_low_diff = abs(candle['High'] - candle['Low'])

    is_volume_exciting = candle['Volume'] > average_volume
    is_body_size_exciting = body_size >= 1.5 * average_body_size
    is_body_size_greater_than_half_diff = (body_size >= 0.5 * high_low_diff)

    # is_exciting = is_volume_exciting and is_body_size_exciting and is_body_size_greater_than_half_diff

    is_exciting = is_body_size_greater_than_half_diff

    if is_exciting:
        if candle['Close'] > candle['Open']:
            candle_type = 'Bullish'
        else:
            candle_type = 'Bearish'
    else:
        candle_type = 'None'

    logging.info(f"Checking candle at position: {candle.name}, Body size: {body_size}, "
                 f"High-Low difference: {high_low_diff}, "
                 f"Average body size: {average_body_size}, Average volume: {average_volume}, "
                 f"Volume: {candle['Volume']}, Is volume exciting: {is_volume_exciting}, "
                 f"Is body size exciting: {is_body_size_exciting}, Is body size greater than half of high-low difference: {is_body_size_greater_than_half_diff}, "
                 f"Is exciting: {is_exciting}, Type: {candle_type}")

    return is_exciting, candle_type

def identify_trend(tickerData, major_highs, major_lows):
    """Identify the trend based on major highs and lows.
    
    Args:
        tickerData (pd.DataFrame): The ticker data.
        major_highs (list): List of indices of major highs.
        major_lows (list): List of indices of major lows.
        
    Returns:
        list: A list of trends ('up', 'down', 'side') for each candle.
    """
    trends = ['side'] * len(tickerData)  # Initialize all trends as 'side'
    all_points = sorted(major_highs + major_lows)  # Combine and sort major highs and lows

    for i in range(1, len(all_points)):
        start = all_points[i - 1]
        end = all_points[i]
        if start in major_lows and end in major_highs:
            trend = 'up'
        elif start in major_highs and end in major_lows:
            trend = 'down'
        else:
            trend = 'side'
        
        for j in range(start, end):
            trends[j] = trend

    # Handle the segment from the last major high or low to the latest candle
    if all_points:
        last_point = all_points[-1]
        for i in range(last_point, len(tickerData)):
            if tickerData.iloc[i]['Close'] > tickerData.iloc[last_point]['Close']:
                trends[i] = 'up'
            elif tickerData.iloc[i]['Close'] < tickerData.iloc[last_point]['Close']:
                trends[i] = 'down'
            else:
                trends[i] = 'side'

    return trends


def find_closest_zones(tickerData, demand_zones, supply_zones):
    """Find the closest demand and supply zones to the last candle's close price."""
    last_close = tickerData.iloc[-1]['Close']
    
    closest_demand = None
    closest_supply = None
    
    if demand_zones:
        closest_demand = min(demand_zones, key=lambda pos: abs(tickerData.iloc[pos]['Low'] - last_close))
    
    if supply_zones:
        closest_supply = min(supply_zones, key=lambda pos: abs(tickerData.iloc[pos]['High'] - last_close))
    
    return closest_demand, closest_supply

def calculate_split_lines(tickerData, demand_pos, supply_pos):
    """Calculate the points for the two lines that split the region between the low of the supply zone and the high of the demand zone into three."""
    demand_price = tickerData.iloc[demand_pos]['High']
    supply_price = tickerData.iloc[supply_pos]['Low']
    
    split1 = demand_price + (supply_price - demand_price) / 3
    split2 = demand_price + 2 * (supply_price - demand_price) / 3
    
    return split1, split2