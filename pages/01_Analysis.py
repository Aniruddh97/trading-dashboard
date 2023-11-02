import streamlit as st

from algo import *
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
                    try:
                        i += 1
                        pbar.progress(int((i)*(100/len(tickers))), text=f"Analyzing {ticker}")
                        pattern = "NO_PATTERN"
                        rank = 999
                        df = ohlcLiveData[ticker]
                        
                        if patternRecognition:
                            pattern, rank = getLatestCandlePattern(df, all=True)
                            
                        indicatorCollection = getIndicators(data=df, ticker=ticker, pattern=pattern)
                        primaryIndicator = indicatorCollection[0]

                        candleIndex = df.index.stop-1
                        analysis['data'][ticker] = {}
                        analysis['data'][ticker]['indicator'] = primaryIndicator.getIndicator(candleIndex)

                        signalCollection = {}
                        for ind in indicatorCollection:
                            signalCollection[ind.__class__.__name__] = ind.getOrder(candleIndex)["signal"]

                        order = primaryIndicator.getOrder(candleIndex)
                        analysis['rank'].append({
                            'Ticker': ticker,
                            'Signal': order["signal"],
                            'Pattern': pattern,
                            'Pattern Rank': rank,
                            'Proximity %': order["proximity"],
                            'Volume Up %': round((df.VOLUME[candleIndex]-df.VOLUME[candleIndex-1])/df.VOLUME[candleIndex-1], 2)*100,
                            **signalCollection
                        })
                    except Exception as e:
                        print(e)
                        continue

                pbar.progress(100, text=f"Analysis complete")
                st.session_state['analysis'] = analysis
            else:
                st.toast(f'Company list for \'{selected_indice}\' not available')
    except Exception as e:
        st.toast(str(e))

if 'analysis' in st.session_state and 'rank' in st.session_state['analysis']:
    rank = pd.DataFrame(st.session_state['analysis']['rank'])
    
    sort, order = getSortBySetting()
    if sort != 'None':
        rank = rank.sort_values(by=sort, ascending=order).reset_index(drop=True)
    
    filter = getFilterBySetting()
    if len(filter) > 0:
        rank = rank[rank.Pattern.isin(filter)]

    st.dataframe(rank)

    indicator_obj = st.session_state['analysis']['data']
    tickerList = rank.Ticker.to_list()
    
    chartContainer = st.container()
        
    if len(tickerList) > 0:
        if useSlider():
            chartIndex = st.slider('', min_value=0, max_value=len(tickerList)-1)
            ticker = tickerList[chartIndex]
            chartContainer.plotly_chart(indicator_obj[ticker]['indicator'], use_container_width=True)
            if chartContainer.button(f'Add `{ticker}` to watchlist'):
                addToWatchlist(ticker=ticker)
        else:
            for ticker in paginate(datalist=rank.Ticker.to_list(), limit_per_page=10):
                chartContainer.plotly_chart(indicator_obj[ticker], use_container_width=True)
                if chartContainer.button(f'Add `{ticker}` to watchlist'):
                    addToWatchlist(ticker=ticker)
    