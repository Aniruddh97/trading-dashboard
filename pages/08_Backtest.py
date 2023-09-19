import random
import streamlit as st

from utils import *

if useWideLayout():
	st.set_page_config(layout="wide")

with st.form("Indice Selection"):
	meta = readJSON(METADATA_FILE_PATH)
	ticker = st.selectbox('Select Ticker', meta['LIST']['NIFTY 500'])
	onlyResult = st.checkbox('Only result')
	submitted = st.form_submit_button("Backtest")
	if submitted:
		st.session_state['backtest_result'] = 0

		olhc_df_dict = load_db_data(tickers=[ticker])
		df = olhc_df_dict[ticker]
		
		sri = SupportResistanceIndicator(df, 11, 5, ticker)
		if not onlyResult:
			fig = sri.getCandleChart()
		
		pbar = st.progress(0, text=f"Backtesting {ticker}")
		for candleIndex, row in df[getCandleCount():-1].iterrows():
			
			pbar.progress(int((candleIndex)*(100/(df.index.stop-1))), text=f"Backtesting {ticker}")

			new_order = sri.getOrder(candleIndex=candleIndex)

			if 'backtest_order' in st.session_state:
				curr_order = st.session_state['backtest_order']

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
					del st.session_state['backtest_order']
					st.session_state['backtest_result'] += result

				if new_order['valid']:
					if result == 0:
						new_position = 'LONG' if new_order['target'] > new_order['strike_price'] else 'SHORT'
						if curr_position == new_position:
							pass
						else:
							# square-off current position
							if curr_position == 'LONG':
								result = df.CLOSE[candleIndex]-curr_order['strike_price']
								st.session_state['backtest_result'] += result 
							else:
								result = (curr_order['strike_price']-df.CLOSE[candleIndex])
								st.session_state['backtest_result'] += result
							
							# take new position
							st.session_state['backtest_order'] = new_order

			elif new_order['valid']:
				st.session_state['backtest_order'] = new_order

		pbar.progress(100, text=f"Backtesting completed")
		
		if not onlyResult:
			st.session_state['backtest_fig'] = fig
		

if 'backtest_fig' in st.session_state:
	st.plotly_chart(st.session_state['backtest_fig'], use_container_width=True)

if 'backtest_result' in st.session_state:
	st.write(st.session_state['backtest_result'])
