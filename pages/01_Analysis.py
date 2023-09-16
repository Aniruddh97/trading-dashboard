import streamlit as st

from utils import *

if useWideLayout():
	st.set_page_config(layout="wide")

with st.form("Indice Selection"):
    try:
        meta = readJSON(METADATA_FILE_PATH)
        selected_indice = st.selectbox('Select Index', meta['LIST']['INDICES'])
        submitted = st.form_submit_button("Analyze")
        if submitted:
            st.session_state['analysis'] = {}
            if selected_indice in meta['LIST']:
                tickers = meta['LIST'][selected_indice]
                ohlcLiveData = most_recent_data(tickers=tickers)
                
                i = 0
                analysis = {}
                analysis['data'] = {}
                analysis['rank'] = []
                patternRecognition = doPatternRecognition()
                pbar = st.progress(0, text=f"Analyzing data")
                for ticker in ohlcLiveData:
                    i += 1
                    pbar.progress(int((i)*(100/len(tickers))), text=f"Analyzing {ticker}")
                    pattern = "NO_PATTERN"
                    rank = 999
                    df = ohlcLiveData[ticker]
                    
                    if patternRecognition:
                        pattern, rank = getLatestCandlePattern(df, all=True)
                        
                    sri = SupportResistanceIndicator(data=df, tickerName=ticker, patternTitle=pattern)

                    candleIndex = df.index.stop-1
                    analysis['data'][ticker] = sri.getIndicator(candleIndex)
                    analysis['rank'].append({
                        'Ticker': ticker,
                        'Pattern': pattern,
                        'Pattern Rank': rank,
                        'Volume Up %': round((df.VOLUME[candleIndex]-df.VOLUME[candleIndex-1])/df.VOLUME[candleIndex-1], 2)*100,
                    })

                pbar.progress(100, text=f"Analysis complete")
                st.session_state['analysis'] = analysis
            else:
                st.toast(f'Company list for \'{selected_indice}\' not available')
    except Exception as e:
        st.toast(str(e))

if 'analysis' in st.session_state and 'rank' in st.session_state['analysis']:
    rank = pd.DataFrame(st.session_state['analysis']['rank'])
    
    sort, order = getSortBySetting()
    rank = rank.sort_values(by=sort, ascending=order)
    
    filter = getFilterBySetting()
    if len(filter) > 0:
        rank = rank[rank.Pattern.isin(filter)]

    st.dataframe(rank)

    indicator_obj = st.session_state['analysis']['data']

    chartContainer = st.container()
    for ticker in paginate(datalist=rank.Ticker.to_list(), limit_per_page=10):
        chartContainer.plotly_chart(indicator_obj[ticker], use_container_width=True)
        if chartContainer.button(f'Add `{ticker}` to watchlist'):
            addToWatchlist(ticker=ticker)