import streamlit as st
import concurrent.futures

from algo import *
from utils import *

if useWideLayout():
    st.set_page_config(layout="wide")

def backtest(ind, onlyResult = True):
    total_result = 0
    total_trades = 0
    curr_order   = {}
    fig = None
    df = ind.df

    if not onlyResult:
        fig = ind.getFullCandleChart()
    
    for candleIndex, row in df[getCandleCount():-1].iterrows():
        new_order = ind.getOrder(candleIndex=candleIndex)

        if len(curr_order) != 0:

            if not onlyResult:
                fig = decorate_pnl_chart(
                    chart=fig,
                    start_x=curr_order['candleIndex'],
                    end_x=candleIndex,
                    stoploss=curr_order['stop_loss'],
                    target=curr_order['target'],
                    strike_price=curr_order['strike_price']
                )

            curr_position = 'LONG' if curr_order['target'] > curr_order['strike_price'] else 'SHORT'
            result = normalize_result(curr_order['strike_price'], get_trade_result(
                df, 
                curr_position,
                candleIndex, 
                curr_order['stop_loss'], 
                curr_order['target'], 
                curr_order['strike_price']
            ))

            if result != 0:
                curr_order = {}
                total_result += result
                total_trades += 1

            if new_order['valid']:
                if result == 0:
                    new_position = 'LONG' if new_order['target'] > new_order['strike_price'] else 'SHORT'
                    if curr_position == new_position:
                        pass
                    # else:
                    #     # square-off current position
                    #     if curr_position == 'LONG':
                    #         result = df.CLOSE[candleIndex]-curr_order['strike_price']
                    #         total_result += result 
                    #         total_trades += 1
                    #     else:
                    #         result = (curr_order['strike_price']-df.CLOSE[candleIndex])
                    #         total_result += result
                    #         total_trades += 1
                        
                    #     # take new position
                    #     curr_order = new_order

        elif new_order['valid']:
            curr_order = new_order

    return {
        'Ticker': ind.tickerName,
        'Total' : total_result,
        'Trades': total_trades,
        'Fig': fig
    }

with st.form("Indice Selection"):
    meta = readJSON(METADATA_FILE_PATH)
    category = st.selectbox('Select Ticker', meta['LIST']['INDICES'])
    onlyResult = st.checkbox('Only result', value=True)
    submitted = st.form_submit_button("Backtest")
    if submitted:
        
        olhc_df_dict = load_db_data(tickers=meta['LIST'][category])
        results = []

        i = 0
        pbar = st.progress(0, text=f"Backtesting...")
        for ticker in meta['LIST'][category]:
            pbar.progress(int((i)*(100/len(meta['LIST'][category]))), text=f"Backtesting {ticker}")
            i += 1
            
            ind = getIndicators(data=olhc_df_dict[ticker], ticker=ticker)

            result = backtest(ind[0], onlyResult)
            results.append(result)
        pbar.progress(100, text=f"Backtesting complete")
    
        df = pd.DataFrame(results)
        st.write(df)
        st.write(f"Net Total : {round(df['Total'].sum(), 2)}")