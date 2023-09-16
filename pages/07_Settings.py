import streamlit as st

from utils import *

if useWideLayout():
	st.set_page_config(layout="wide")

meta = readJSON()
with st.form('Configure settings'):
    layout = useWideLayout()
    window = getPivotWindow()
    candles = getCandleCount()
    patternRecognition = doPatternRecognition()
    filters = getFilterBySetting()

    wide_layout = st.checkbox('Wide Layout', value=layout)

    pivot_window = st.number_input("Pivot Window", value=window, min_value=11, max_value=61)
    candle_count = st.number_input("Candle Count", value=candles, min_value=50, max_value=120)
    doPatternRecognition = st.checkbox('Pattern Recognition', value=patternRecognition)
    sortby = st.selectbox('Sort By', ['Pattern Rank', 'Volume Up %'])
    filterby = st.multiselect('Filter By', options=candle_rankings.keys(), default=filters)
    
    submitted = st.form_submit_button("Save")
    if submitted:
        if 'settings' not in meta:
            meta['settings'] = {}

        meta['settings']['wide_layout'] = wide_layout

        meta['settings']['pivot_window'] = int(pivot_window)
        meta['settings']['pattern_recognition'] = doPatternRecognition
        meta['settings']['sort_by'] = sortby
        meta['settings']['filter_by'] = filterby
        meta['settings']['candle_count'] = candle_count
        writeJSON(obj=meta)