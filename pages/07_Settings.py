import streamlit as st

from utils import *

meta = readJSON()

with st.form('Configure settings'):
    window = getPivotWindow()
    patternRecognition = doPatternRecognition()

    pivot_window = st.number_input("Pivot Window", value=window, min_value=11, max_value=61)
    doPatternRecognition = st.checkbox('Pattern Recognition', value=patternRecognition)
    sortby = st.selectbox('Sort By', ['Pattern Rank', 'Volume Up %'])
    
    submitted = st.form_submit_button("Save")
    if submitted:
        if 'settings' not in meta:
            meta['settings'] = {}

        meta['settings']['pivot_window'] = int(pivot_window)
        meta['settings']['pattern_recognition'] = doPatternRecognition
        meta['settings']['sort_by'] = sortby
        writeJSON(obj=meta)