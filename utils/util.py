import pandas as pd
import streamlit as st

def merge_data(ohlc_obj_df, data_obj_df):
    latestData = {}
    for stock in data_obj_df:
        try:
            if stock not in ohlc_obj_df:
                continue
            
            recent_db_date = ohlc_obj_df[stock]['DATE'][len(ohlc_obj_df[stock].index)-1]
            recent_live_date = data_obj_df[stock]['DATE'][len(data_obj_df[stock].index)-1]
            if  recent_db_date == recent_live_date:
                latestData[stock] = ohlc_obj_df[stock]
            else:
                dfA = ohlc_obj_df[stock]
                dfB = data_obj_df[stock]
                dfC = pd.concat([dfA, dfB], ignore_index=True)
                latestData[stock] = dfC
        except:
            st.toast(f'failed to merge {stock} data')

    return latestData
