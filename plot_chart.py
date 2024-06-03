import plotly.graph_objects as go
import logging
import pandas as pd
import numpy as np  # Ensure NumPy is imported

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def find_nearest_date(index, target):
    """Find the nearest date in the index to the target."""
    # If the index is timezone-aware and the target is not, localize the target to the index's timezone
    if index.tz is not None and target.tzinfo is None:
        target = target.tz_localize(index.tz)
    # If the index is timezone-naive and the target is timezone-aware, remove the timezone from the target
    elif index.tz is None and target.tzinfo is not None:
        target = target.tz_localize(None)
    
    # Calculate the absolute difference between the target and each datetime in the index, then find the index of the minimum difference
    nearest_index = np.abs(index - target).argmin()
    return index[nearest_index]


def plot_chart(tickerData, fvg_list, major_highs, major_lows, bos_list):
    """Create a candlestick chart with colored candles, FVGs, and major highs/lows."""
    fig = go.Figure()

    fig.add_trace(go.Candlestick(x=tickerData.index,
                                 open=tickerData['Open'],
                                 high=tickerData['High'],
                                 low=tickerData['Low'],
                                 close=tickerData['Close'],
                                 increasing_line_color='blue',   
                                 decreasing_line_color='black',
                                 name='Price'))

    # Modify FVGs to the chart based on position
    for fvg in fvg_list:
        start_pos, end_pos, fvg_type = fvg  # Use positions instead of dates
        color = 'yellow' if fvg_type == 'Bullish' else 'orange'
        y0 = tickerData.iloc[start_pos]['High'] if fvg_type == 'Bullish' else tickerData.iloc[start_pos]['Low']
        y1 = tickerData.iloc[end_pos]['Low'] if fvg_type == 'Bullish' else tickerData.iloc[end_pos]['High']
        
        logging.info(f"Adding {fvg_type} FVG shape: Start={tickerData.index[start_pos]}, End={tickerData.index[end_pos]}, Color={color}")
        
        fig.add_shape(type="rect",
                      x0=tickerData.index[start_pos], x1=tickerData.index[end_pos],
                      y0=y0, y1=y1,
                      fillcolor=color, opacity=0.3, line_width=2)

  # Modify major highs to the chart to extend only to the right
    for high_pos in major_highs:
        y_high = tickerData.iloc[high_pos]['High']
        x_high_date = tickerData.index[high_pos]  # Get the date/index of the high
        
        logging.info(f"Adding major high line: Date={x_high_date}, Y={y_high}")
        
        fig.add_shape(type="line",
                      x0=x_high_date, x1=tickerData.index[-1],  # Start from the high and extend to the end
                      y0=y_high, y1=y_high,
                      line=dict(color="green", width=1, dash="dash"))

    # Modify major lows to the chart to extend only to the right
    for low_pos in major_lows:
        y_low = tickerData.iloc[low_pos]['Low']
        x_low_date = tickerData.index[low_pos]  # Get the date/index of the low
        
        logging.info(f"Adding major low line: Date={x_low_date}, Y={y_low}")
        
        fig.add_shape(type="line",
                      x0=x_low_date, x1=tickerData.index[-1],  # Start from the low and extend to the end
                      y0=y_low, y1=y_low,
                      line=dict(color="red", width=1, dash="dash"))

    # Modify BoS to the chart based on position
    for bos in bos_list:
        bos_pos, bos_type = bos
        y_bos = tickerData.iloc[bos_pos]['Close']
        color = 'blue' if bos_type == 'Bullish' else 'red'
        
        logging.info(f"Adding BoS line: Date={tickerData.index[bos_pos]}, Type={bos_type}, Color={color}")
        
        fig.add_shape(type="line",
                      x0=tickerData.index[bos_pos], x1=tickerData.index[bos_pos],
                      y0=tickerData['Low'].min(), y1=tickerData['High'].max(),
                      line=dict(color=color, width=2, dash="dot"))

    fig.update_layout(
        yaxis_title='Price',
        xaxis_title='Date',
        xaxis=dict(
            rangeslider=dict(visible=True),
            type='category'  # this line will remove the gaps for non-trading days
        ),
    )

    # Show the figure
    fig.show()