import streamlit as st

from utils import *


with st.form("Indice Selection"):
	try:
		meta = readJSON(METADATA_FILE_PATH)
		selected_indice = st.selectbox('Select Index', meta['LIST']['INDICES'])
		submitted = st.form_submit_button("Analyze")
		if submitted:
			st.session_state['analysis'] = {}
			if selected_indice in meta['LIST']:
				tickers = meta['LIST'][selected_indice]
				
				live_data = {}
				if is_market_open() == 1:
					live_data = get_live_data_collection(tickers=tickers)

				ohlcData = load_db_data(tickers=tickers)
				ohlcLiveData = append_data(ohlc_obj_df=ohlcData, data_obj_df=live_data)
				
				i = 0
				analysis = {}
				analysis['data'] = {}
				analysis['rank'] = []
				pbar = st.progress(0, text=f"Analyzing data")
				for ticker in ohlcLiveData:
					i += 1
					pbar.progress(int((i)*(100/len(tickers))), text=f"Analyzing {ticker}")

					df = ohlcLiveData[ticker]
					pattern, rank = getLatestCandlePattern(df, all=True)
					sri = SupportResistanceIndicator(data=df, window=11, backCandles=5, tickerName=ticker, patternTitle=pattern)

					candleIndex = df.index.stop-1
					analysis['data'][ticker] = sri.getIndicator(candleIndex)
					analysis['rank'].append({
						'Ticker': ticker,
						'Pattern': pattern,
						'Pattern Rank': rank
					})

				pbar.progress(100, text=f"Analysis complete")
				st.session_state['analysis'] = analysis
			else:
				st.toast(f'Company list for \'{selected_indice}\' not available')
	except Exception as e:
		st.toast(str(e))

if 'analysis' in st.session_state and 'rank' in st.session_state['analysis']:
	rank = pd.DataFrame(st.session_state['analysis']['rank'])
	rank = rank.sort_values(by='Pattern Rank', ascending=True)
	rank_for_display = rank[rank.Pattern != 'NO_PATTERN']
	if not rank_for_display.empty:
		st.dataframe(rank_for_display)

	indicator_obj = st.session_state['analysis']['data']

	chartContainer = st.container()
	for ticker in paginate(datalist=rank.Ticker.to_list(), limit_per_page=10):
		chartContainer.plotly_chart(indicator_obj[ticker])
		if chartContainer.button(f'Add `{ticker}` to watchlist'):
			addToWatchlist(ticker=ticker)