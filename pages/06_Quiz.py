import random
import streamlit as st

from algo import *
from utils import *

if useWideLayout():
	st.set_page_config(layout="wide")

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
	try:
		randomTicker = tickers[random.randint(0, len(tickers)-1)]
		df = most_recent_data(tickers=[randomTicker], progress=False)[randomTicker]
		randomIndex = random.randint(df.index.start+getCandleCount(), df.index.stop-50)
		ind = getIndicators(data=df, ticker=randomTicker)[0]
		while not ind.getOrder(randomIndex)["valid"] and randomIndex < df.index.stop - 50:
			randomIndex += 1
	except:
		st.experimental_rerun()

	st.session_state['quiz']['ticker'] = randomTicker
	st.session_state['quiz']['randomIndex'] = randomIndex
else:
	randomTicker = st.session_state['quiz']['ticker']
	df = most_recent_data(tickers=[randomTicker], progress=False)[randomTicker]
	randomIndex = st.session_state['quiz']['randomIndex']

# pattern, rank = getLatestCandlePattern(df[0:randomIndex+1], all=True)
pattern = ' '.join(getCandlestickPatterns(df[0:randomIndex+1], candleIndex=randomIndex))
ind = getIndicators(data=df, ticker=randomTicker, pattern=pattern)[0]
st.plotly_chart(ind.getIndicator(randomIndex), use_container_width=True)

if st.button("Next"):
	del st.session_state['quiz']['ticker']
	del st.session_state['quiz']['randomIndex']
	st.experimental_rerun()

if st.button("Next Candle"):
	st.session_state['quiz']['randomIndex'] = st.session_state['quiz']['randomIndex'] + 1

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
		
		start = df.index[df['DATE'] == pd.to_datetime(df.DATE[randomIndex]).date()].tolist()[0]
		chart = ind.getIndicator(result_idx+25)
		chart = decorate_pnl_chart(
			chart=chart, 
			start_x=start, 
			end_x=result_idx, 
			strike_price=df.CLOSE[randomIndex],
			target=target,
			stoploss=stop_loss,
		)
		st.plotly_chart(chart, use_container_width=True)

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