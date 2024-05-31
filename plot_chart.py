
# import plotly.graph_objects as go
# import numpy as np
# import logging

# # Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# import plotly.graph_objects as go
# import numpy as np
# import logging
# import pandas as pd  # Ensure pandas is imported

# # Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# def plot_chart(tickerData, fvg_list):
#     """Create a candlestick chart with colored candles and FVGs."""
#     fig = go.Figure()

#     fig.add_trace(go.Candlestick(x=tickerData.index,
#                                  open=tickerData['Open'],
#                                  high=tickerData['High'],
#                                  low=tickerData['Low'],
#                                  close=tickerData['Close'],
#                                  increasing_line_color='blue',   
#                                  decreasing_line_color='black',
#                                  name='Price'))

#     # Ensure tickerData.index is a DatetimeIndex and convert to string format for comparison
#     if not isinstance(tickerData.index, pd.DatetimeIndex):
#         tickerData.index = pd.to_datetime(tickerData.index)
#     tickerData_dates_str = tickerData.index.strftime('%Y-%m-%d').tolist()

#     # Add FVGs to the chart
#     for fvg in fvg_list:
#         start_date, end_date, fvg_type = fvg
#         # Convert start_date and end_date to string for comparison
#         start_date_str = start_date.strftime('%Y-%m-%d')
#         end_date_str = end_date.strftime('%Y-%m-%d')
        
#         logging.info(f"Checking FVG: start_date={start_date_str}, end_date={end_date_str}")
#         if start_date_str in tickerData_dates_str and end_date_str in tickerData_dates_str:
#             if fvg_type == 'Bullish':
#                 color = 'yellow'
#             else:
#                 color = 'orange'
            
#             # Locate the original dates in tickerData for y0 and y1 values
#             y0 = tickerData.loc[pd.to_datetime(start_date_str)]['High']
#             y1 = tickerData.loc[pd.to_datetime(end_date_str)]['Low']
            
#             logging.info(f"Adding FVG: start_date={start_date_str}, end_date={end_date_str}, y0={y0}, y1={y1}, color={color}")
            
#             fig.add_shape(type="rect",
#                           x0=start_date_str, x1=end_date_str,
#                           y0=y0, y1=y1,
#                           fillcolor=color, opacity=0.3, line_width=0)
#         else:
#             logging.warning(f"Dates not found in tickerData: start_date={start_date_str}, end_date={end_date_str}")

#     fig.update_layout(
#         yaxis_title='Price',
#         xaxis_title='Date',
#         xaxis=dict(
#             rangeslider=dict(visible=True),
#             type='category'  # this line will remove the gaps for non-trading days
#         ),
#     )

#     # Show the figure
#     fig.show()


import plotly.graph_objects as go
import numpy as np
import logging
import pandas as pd  # Ensure pandas is imported

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def plot_chart(tickerData, fvg_list):
    """Create a candlestick chart with colored candles and FVGs."""
    fig = go.Figure()

    fig.add_trace(go.Candlestick(x=tickerData.index,
                                 open=tickerData['Open'],
                                 high=tickerData['High'],
                                 low=tickerData['Low'],
                                 close=tickerData['Close'],
                                 increasing_line_color='blue',   
                                 decreasing_line_color='black',
                                 name='Price'))

    # Ensure tickerData.index is a DatetimeIndex and convert to string format for comparison
    if not isinstance(tickerData.index, pd.DatetimeIndex):
        tickerData.index = pd.to_datetime(tickerData.index)
    tickerData_dates_str = tickerData.index.strftime('%Y-%m-%d').tolist()

    # Add FVGs to the chart
    for fvg in fvg_list:
        start_date, end_date, fvg_type = fvg
        # Convert start_date and end_date to string for comparison
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        logging.info(f"Checking FVG: start_date={start_date_str}, end_date={end_date_str}")
        if start_date_str in tickerData_dates_str and end_date_str in tickerData_dates_str:
            if fvg_type == 'Bullish':
                color = 'yellow'
                y0 = tickerData.loc[pd.to_datetime(start_date_str)]['High']
                y1 = tickerData.loc[pd.to_datetime(end_date_str)]['Low']
            else:
                color = 'orange'
                y0 = tickerData.loc[pd.to_datetime(start_date_str)]['Low']
                y1 = tickerData.loc[pd.to_datetime(end_date_str)]['High']
            
            logging.info(f"Adding FVG: start_date={start_date_str}, end_date={end_date_str}, y0={y0}, y1={y1}, color={color}")
            
            fig.add_shape(type="rect",
                          x0=start_date_str, x1=end_date_str,
                          y0=y0, y1=y1,
                          fillcolor=color, opacity=0.3, line_width=0)
        else:
            logging.warning(f"Dates not found in tickerData: start_date={start_date_str}, end_date={end_date_str}")

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