import pandas as pd
import streamlit as st

from utils import *
from algo import *

if useWideLayout():
    st.set_page_config(layout="wide")

if 'study_result' not in st.session_state:
    st.session_state['study_result'] = 0

with st.form("Study form"):
    meta = readJSON(METADATA_FILE_PATH)
    ticker = st.selectbox('Select Ticker', meta['LIST']['NIFTY 500'])
    submitted = st.form_submit_button("Study")
    if submitted:
        st.session_state['study_ticker'] = ticker
        st.session_state['study_ticker_data'] = load_db_data(tickers=[ticker])[ticker]
        st.session_state['study_ticker_indicators'] = getIndicators(
            data=st.session_state['study_ticker_data'],
            ticker=ticker
        )
        
        st.session_state['study_result'] = 0
        if 'study_order' in st.session_state:
            del st.session_state['study_order']

container = st.container()
if 'study_ticker' in st.session_state:
    df = st.session_state['study_ticker_data']
    candleIndex = st.slider('', min_value=df.index.start+getCandleCount(), max_value=df.index.stop-1)

    indicator = st.session_state['study_ticker_indicators'][0]
    fig = indicator.getIndicator(candleIndex)

    new_order = indicator.getOrder(candleIndex=candleIndex)

    col1, col2 = st.columns(2)
    col2.write(new_order)

    if 'study_order' in st.session_state:
        curr_order = st.session_state['study_order']
        col1.write(curr_order)

        fig = decorate_pnl_chart(
            chart=fig,
            start_x=curr_order['candleIndex'],
            end_x=candleIndex,
            stoploss=curr_order['stop_loss'],
            target=curr_order['target'],
            strike_price=curr_order['strike_price']
        )

        curr_position = 'LONG' if curr_order['target'] > curr_order['strike_price'] else 'SHORT'
        result = get_trade_result(
            df, 
            curr_position,
            candleIndex, 
            curr_order['stop_loss'], 
            curr_order['target'], 
            curr_order['strike_price']
        )

        if result != 0:
            del st.session_state['study_order']
            st.session_state['study_result'] += result
            if result > 0:
                st.balloons()
            else:
                st.snow()

        if new_order['valid']:
            if result == 0:
                new_position = 'LONG' if new_order['target'] > new_order['strike_price'] else 'SHORT'
                if curr_position == new_position:
                    pass
                else:
                    # square-off current position
                    if curr_position == 'LONG':
                        result = df.CLOSE[candleIndex]-curr_order['strike_price']
                        st.session_state['study_result'] += result 
                    else:
                        result = (curr_order['strike_price']-df.CLOSE[candleIndex])
                        st.session_state['study_result'] += result
                    
                    # take new position
                    st.session_state['study_order'] = new_order

                    if result > 0:
                        st.balloons()
                    else:
                        st.snow()

    elif new_order['valid']:
        st.session_state['study_order'] = new_order

    container.plotly_chart(fig, use_container_width=True)

    st.write(f"P&L : {round(st.session_state['study_result'], 2)}")