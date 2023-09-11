import random
import streamlit as st

from utils import *

if 'quiz' not in st.session_state:
	st.session_state['quiz'] = {}
	st.session_state['quiz']['last_result'] = 0
	st.session_state['quiz']['total_result'] = 0
	st.session_state['quiz']['total_rrr'] = 0
	st.session_state['quiz']['last_rrr'] = 0

col1, col2 = st.columns(2)

col1.metric(
	label="P&L", 
	value=str(st.session_state['quiz']['total_result']), 
	delta=str(st.session_state['quiz']['last_result']),
)
col2.metric(
	label="Avg. RRR", 
	value=str(st.session_state['quiz']['total_rrr']), 
	delta=str(st.session_state['quiz']['last_rrr']),
)

meta = readJSON(METADATA_FILE_PATH)
tickers = meta['LIST']['NIFTY 500']

if 'ticker' not in st.session_state['quiz']:
	randomTicker = tickers[random.randint(0, len(tickers))]
	df = most_recent_data(tickers=[randomTicker], progress=False)[randomTicker]
	randomIndex = random.randint(df.index.start+50, df.index.stop-50)
	st.session_state['quiz']['ticker'] = randomTicker
	st.session_state['quiz']['randomIndex'] = randomIndex
else:
	randomTicker = st.session_state['quiz']['ticker']
	df = most_recent_data(tickers=[randomTicker], progress=False)[randomTicker]
	randomIndex = st.session_state['quiz']['randomIndex']

sri = SupportResistanceIndicator(data=df, tickerName=randomTicker)
st.plotly_chart(sri.getIndicator(randomIndex))

if st.button("Skip"):
	del st.session_state['quiz']['ticker']
	del st.session_state['quiz']['randomIndex']
	st.experimental_rerun()

with st.form("Quiz Order Form"):
	stop_loss = st.number_input("Stoploss")
	target = st.number_input("Target")
	units = st.number_input("Units", 1)
	submitted = st.form_submit_button("Place Order")
	if submitted:
		result, result_idx = evaluate_trade(
            data=df, 
            date=df.DATE[randomIndex], 
            strike_price=df.CLOSE[randomIndex],
            target=target,
            stop_loss=stop_loss)
		
		st.plotly_chart(sri.getIndicator(result_idx))

		# P&L metric
		result = round(result*units, 2)
		st.session_state['quiz']['last_result'] = result
		st.session_state['quiz']['total_result'] += result

		# RRR metric
		rrr = round(abs(target - df.CLOSE[randomIndex])/abs(stop_loss - df.CLOSE[randomIndex]), 2)
		if st.session_state['quiz']['total_rrr'] == 0:
			st.session_state['quiz']['total_rrr'] = rrr
		else:
			st.session_state['quiz']['total_rrr'] = round((st.session_state['quiz']['total_rrr'] + rrr)/2, 2)

		if rrr < st.session_state['quiz']['total_rrr']:
			st.session_state['quiz']['last_rrr'] = -rrr
		else:
			st.session_state['quiz']['last_rrr'] = rrr

		
		if result > 0:
			st.balloons()
		elif result < 0:
			st.snow()

		del st.session_state['quiz']['ticker']
		del st.session_state['quiz']['randomIndex']