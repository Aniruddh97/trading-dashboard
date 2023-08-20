import math
import pandas as pd
import streamlit as st

from algo import *
from .util import *
from .paginate import *

def evaluate_trade(data, date, strike_price, target, stop_loss):
    end = data.index.stop - 1
    start = data.index[data['DATE'] == pd.to_datetime(date).date()].tolist()[0] + 1
    if start >= end:
        return 0, 0

    result = 0
    result_index = start
    position = 'LONG' if target > strike_price else 'SHORT'

    for i in range(start, end):
        if position == 'LONG':
            if data.LOW[i] <= stop_loss:
                result = stop_loss - strike_price
            elif data.HIGH[i] >= target:
                result = target - strike_price
        else:
            if data.LOW[i] <= target:
                result = strike_price - target
            elif data.HIGH[i] >= stop_loss:
                result = strike_price - stop_loss

        result_index = i
        if result != 0:
            break
    
    return result, result_index


def process_open_trades():
    open_position_df = execute_query(ORDER_DATABASE_PATH, query="SELECT * FROM orders WHERE result IS NULL")
    if open_position_df is None or open_position_df.empty:
        return
    
    tickers = open_position_df.ticker.to_list()
    data_dict = most_recent_data(tickers=tickers)

    for index, row in open_position_df.iterrows():
        data = data_dict[row.ticker]
        result, result_idx = evaluate_trade(
            data=data, 
            date=row.start_date, 
            strike_price=row.strike_price,
            target=row.target,
            stop_loss=row.stoploss)
        
        if result != 0:
            result *= result * row.units

            query = """
                UPDATE orders SET result = ?, end_date = ? WHERE ticker = ? and target = ?
            """
            update_query(ORDER_DATABASE_PATH, query, (result, data.DATE[result_idx], row.ticker, row.target))


def display_pnl():
    orders_df = execute_query(ORDER_DATABASE_PATH, query="SELECT * FROM orders")

    if orders_df is None or orders_df.empty:
        st.info('No data available')
        return

    st.session_state.pnl = []
    rrr = orders_df.rrr.mean()
    closed_positions_df = orders_df[orders_df.result.notnull()]
    pnl = round(float(closed_positions_df.result.sum()), 2)

    last_pnl = ''
    if not closed_positions_df.empty:
        last_pnl = round(float(closed_positions_df.result[orders_df.index.stop-1]), 2)

    col1, col2 = st.columns(2)
    col1.metric("P&L", str(pnl), str(last_pnl))
    col2.metric("Avg. RRR", str(round(rrr,2)), str(round(orders_df.rrr[orders_df.index.stop-1],2)))

    tickers = list(set(closed_positions_df.ticker.to_list()))
    data_dict = most_recent_data(tickers=tickers)

    for index, row in closed_positions_df.iterrows():
        df = data_dict[row.ticker]
        sri = SupportResistanceIndicator(data=df, window=11, backCandles=5, tickerName=row.ticker)
        
        marker_start_x = df.index[df['DATE'] == pd.to_datetime(row.start_date).date()].tolist()[0]
        marker_start_y = df.LOW[marker_start_x] - (df.LOW[marker_start_x]/100)
        
        marker_end_x = df.index[df['DATE'] == pd.to_datetime(row.end_date).date()].tolist()[0]
        marker_end_y = df.HIGH[marker_end_x] + (df.HIGH[marker_end_x]/100)
        if row.position == "SHORT":
            marker_start_y = df.HIGH[marker_start_x] + (abs((df.HIGH[marker_start_x]-df.LOW[marker_start_x])/5))
            marker_end_y = df.LOW[marker_end_x] - (abs((df.HIGH[marker_end_x]-df.LOW[marker_end_x])/5))


        chart = sri.getIndicator(marker_end_x+10)
        chart.add_scatter(
            x=[marker_start_x, marker_end_x], 
            y=[marker_start_y, marker_end_y], 
            mode="markers",
            marker=dict(size=8, color="white"), 
            marker_symbol="star")
        
        st.session_state.pnl.append(chart)
        
    chartContainer = st.container()
    for chart in paginate(st.session_state.pnl, limit_per_page=10):
        chartContainer.plotly_chart(chart)