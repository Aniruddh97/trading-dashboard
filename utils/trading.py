import math
import pandas as pd
import streamlit as st

from .util import *
from .paginate import *
from algo import getIndicators

def evaluate_trade(data, date, strike_price, target, stop_loss):
    end = data.index.stop - 1
    start = data.index[data['DATE'] == pd.to_datetime(date).date()].tolist()[0] + 1
    if start > end:
        return 0, 0

    result = 0
    result_index = start
    position = 'LONG' if target > strike_price else 'SHORT'

    for i in range(start, end+1):
        result = get_trade_result(data, position, i, stop_loss, target, strike_price)
        result_index = i

        if result != 0:
            break
    
    return result, result_index


def get_trade_result(data, position, candleIndex, stop_loss, target, strike_price):
    result = 0

    if position == 'LONG':
        if data.LOW[candleIndex] <= stop_loss:
            result = stop_loss - strike_price
        elif data.HIGH[candleIndex] >= target:
            result = target - strike_price
    else:
        if data.LOW[candleIndex] <= target:
            result = strike_price - target
        elif data.HIGH[candleIndex] >= stop_loss:
            result = strike_price - stop_loss

    if result != 0:
        result = round(float(result),2)

    return result


def normalize_result(cost_price, result): 
    return round(((result*100)/cost_price), 2)


def process_open_trades():
    open_position_df = execute_query(ORDER_DATABASE_PATH, query="SELECT * FROM orders WHERE result IS NULL")
    if open_position_df is None or open_position_df.empty:
        return
    
    tickers = open_position_df.ticker.to_list()
    data_dict = most_recent_data(tickers=tickers, progress=False)

    for index, row in open_position_df.iterrows():
        data = data_dict[row.ticker]
        result, result_idx = evaluate_trade(
            data=data, 
            date=row.start_date, 
            strike_price=row.strike_price,
            target=row.target,
            stop_loss=row.stoploss)
        
        if result != 0:
            result *= row.units
            query = """
                UPDATE orders SET result = ?, end_date = ? WHERE ticker = ? and target = ?
            """
            update_query(ORDER_DATABASE_PATH, query, (result, data.DATE[result_idx], row.ticker, row.target))


def display_pnl():
    orders_df = execute_query(ORDER_DATABASE_PATH, query="SELECT * FROM orders")

    if orders_df is None or orders_df.empty:
        st.info('No data available')
        return

    if "pnl" not in st.session_state:
        st.session_state.pnl = []
    
    rrr = orders_df.rrr.mean()
    closed_positions_df = orders_df[orders_df.result.notnull()]
    pnl = round(closed_positions_df.result.astype(float).sum(), 2)

    last_pnl = ''
    if not closed_positions_df.empty:
        last_pnl = round(float(closed_positions_df.result[closed_positions_df.index.to_list()[-1]]), 2)

    col1, col2 = st.columns(2)
    col1.metric("P&L", str(pnl), str(last_pnl))
    col2.metric("Avg. RRR", str(round(rrr,2)), str(round(orders_df.rrr.astype(float)[orders_df.index.stop-1],2)))

    # Diplay open positions
    open_positions = orders_df[orders_df.result.isnull()]
    if not open_positions.empty:
        st.divider()
        st.dataframe(open_positions)

    closed_positions_df = closed_positions_df.iloc[::-1]
    tickers = list(set(closed_positions_df.ticker.to_list()))
    data_dict = most_recent_data(tickers=tickers, progress=False)

    if len(st.session_state.pnl) == 0:
        for index, row in closed_positions_df.iterrows():
            df = data_dict[row.ticker]
            ind = getIndicators(data=df, ticker=row.ticker)[0]
            
            marker_start_x = df.index[df['DATE'] == pd.to_datetime(row.start_date).date()].tolist()[0]
            marker_start_y = df.LOW[marker_start_x] - (df.LOW[marker_start_x]/100)
            
            marker_end_x = df.index[df['DATE'] == pd.to_datetime(row.end_date).date()].tolist()[0]
            marker_end_y = df.HIGH[marker_end_x] + (df.HIGH[marker_end_x]/100)
            if row.position == "SHORT":
                marker_start_y = df.HIGH[marker_start_x] + (abs((df.HIGH[marker_start_x]-df.LOW[marker_start_x])/5))
                marker_end_y = df.LOW[marker_end_x] - (abs((df.HIGH[marker_end_x]-df.LOW[marker_end_x])/5))


            chart = ind.getIndicator(marker_end_x+25)
            chart = decorate_pnl_chart(
                chart=chart, 
                start_x=marker_start_x, 
                end_x=marker_end_x, 
                strike_price=row.strike_price,
                target=row.target,
                stoploss=row.stoploss,
            )
            
            st.session_state.pnl.append(chart)
        
    chartContainer = st.container()

    if useSlider():
        chartIndex = st.slider('', min_value=0, max_value=len(st.session_state.pnl)-1)
        chart = st.session_state['pnl'][chartIndex]
        chartContainer.plotly_chart(chart, use_container_width=True)
    else:
        for chart in paginate(st.session_state.pnl, limit_per_page=10):
            chartContainer.plotly_chart(chart, use_container_width=True)


def decorate_pnl_chart(chart, start_x, end_x, strike_price, target, stoploss):
    # chart.add_scatter(
    # x=[marker_start_x, marker_end_x], 
    # y=[marker_start_y, marker_end_y], 
    # mode="markers",
    # marker=dict(size=8, color="white"), 
    # marker_symbol="star")

    # strike price line
    chart.add_shape(
            type='line',
            x0=start_x,
            y0=strike_price,
            x1=end_x,
            y1=strike_price,
            line=dict(color="yellow", width=3),
            xref='x',
            yref='y',
            row= 1,
            col=1
        )

    # target line
    chart.add_shape(
            type='line',
            x0=start_x,
            y0=target,
            x1=end_x,
            y1=target,
            line=dict(color="lightgreen", width=3),
            xref='x',
            yref='y',
            row= 1,
            col=1
        )

    # stoploss line
    chart.add_shape(
            type='line',
            x0=start_x,
            y0=stoploss,
            x1=end_x,
            y1=stoploss,
            line=dict(color="orangered", width=3),
            xref='x',
            yref='y',
            row= 1,
            col=1
        )

    return chart