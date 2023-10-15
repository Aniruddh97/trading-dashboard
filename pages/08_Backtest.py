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
            result = get_trade_result(
                df, 
                curr_position,
                candleIndex, 
                curr_order['stop_loss'], 
                curr_order['target'], 
                curr_order['strike_price']
            )

            if result != 0:
                curr_order = {}
                total_result += result
                total_trades += 1

            if new_order['valid']:
                if result == 0:
                    new_position = 'LONG' if new_order['target'] > new_order['strike_price'] else 'SHORT'
                    if curr_position == new_position:
                        pass
                    else:
                        # square-off current position
                        if curr_position == 'LONG':
                            result = df.CLOSE[candleIndex]-curr_order['strike_price']
                            total_result += result 
                            total_trades += 1
                        else:
                            result = (curr_order['strike_price']-df.CLOSE[candleIndex])
                            total_result += result
                            total_trades += 1
                        
                        # take new position
                        curr_order = new_order

        elif new_order['valid']:
            curr_order = new_order

    return ind.tickerName, total_result, total_trades, fig


with st.form("Indice Selection"):
    meta = readJSON(METADATA_FILE_PATH)
    category = st.selectbox('Select Ticker', meta['LIST'])
    onlyResult = st.checkbox('Only result', value=True)
    submitted = st.form_submit_button("Backtest")
    if submitted:
        
        olhc_df_dict = load_db_data(tickers=meta['LIST'][category])

        with concurrent.futures.ThreadPoolExecutor() as executor:
            
            futures = [executor.submit(getIndicators, olhc_df_dict[ticker], ticker) for ticker in meta['LIST'][category]]
            indicatorArray = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            indicators = [arr[0] for arr in indicatorArray]


        with concurrent.futures.ThreadPoolExecutor() as executor:
            shortlisted = []
            for pattern in candle_rankings.keys():
                for ind in indicators:
                    ind.patterns = [pattern]
                
                futures = [executor.submit(backtest, ind, onlyResult) for ind in indicators]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
                final_result = []
                wins = 0
                loss = 0
                for result in results:
                    final_result.append({
                        'Ticker': result[0],
                        'PnL': result[1],
                        'Trades': result[2],
                        'Pattern': pattern
                    })
                    if result[1] < 0:
                        loss += 1
                    elif result[1] > 0:
                        wins += 1
                    
                if (wins > 0 or loss > 0) and wins*100/(loss+wins) >= 67:
                    shortlisted.append({
                        "Pattern": pattern,
                        "Wins": wins,
                        "Loss": loss
                    })

                st.write(f"{pattern} | Wins : {wins} | Loss : {loss}")
                # st.write(pd.DataFrame(final_result))
                # st.divider()
        meta = readJSON()
        meta['Backtest Result'] = shortlisted
        writeJSON(meta)
        st.write(shortlisted)