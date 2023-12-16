import streamlit as st

from algo import *
from utils import *

if useWideLayout():
    st.set_page_config(layout="wide")

meta = readJSON()
with st.form('Configure settings'):
    col1, col2, col3 = st.columns(3)

    sldr = useSlider()
    slider = col1.checkbox('Slider', value=sldr)
    
    layout = useWideLayout()
    wide_layout = col2.checkbox('Wide Layout', value=layout)
    
    patternRecognition = doPatternRecognition()
    doPatternRecognition = col3.checkbox('Pattern Recognition', value=patternRecognition)

    cheight = getChartHeight()
    chart_height = st.number_input("Chart Height", value=cheight, min_value=250, max_value=750)
    
    window = getPivotWindow()
    pivot_window = st.number_input("Window", value=window, min_value=11, max_value=200)
    
    emaWindow = getEMAWindow()
    ema_window = st.number_input("EMA Window", value=emaWindow, min_value=5, max_value=200)
    
    candles = getCandleCount()
    candle_count = st.number_input("Candle Count", value=candles, min_value=50, max_value=240)
    
    patterns = getFilterBySetting()
    patternFilter = st.multiselect('Pattern Filter', options=candle_rankings.keys(), default=patterns)
    
    indArray = ['EMA', 'S&R', 'Experimental', 'Trendline', 'CandlestickPattern']
    inds = getIndicatorSetting()
    indicator = st.multiselect('Indicator', options=indArray, default=inds)
    
    sortArray = ['None', 'Proximity %', 'Pattern Rank', 'Volume Up %', 'Signal']
    sortby, _ = getSortBySetting()
    sortby = st.selectbox('Sort By', sortArray, index=sortArray.index(sortby))

    
    submitted = st.form_submit_button("Save")
    if submitted:
        if 'settings' not in meta:
            meta['settings'] = {}

        meta['settings']['slider'] = slider
        meta['settings']['wide_layout'] = wide_layout
        meta['settings']['chart_height'] = chart_height

        meta['settings']['sort_by'] = sortby
        meta['settings']['candle_count'] = candle_count
        meta['settings']['pivot_window'] = int(pivot_window)
        meta['settings']['ema_window'] = int(ema_window)
        meta['settings']['pattern_filter'] = patternFilter
        meta['settings']['indicator'] = indicator
        meta['settings']['pattern_recognition'] = doPatternRecognition
        writeJSON(obj=meta)