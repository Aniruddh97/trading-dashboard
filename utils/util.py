import requests
import datetime
import pandas as pd
import streamlit as st

from zoneinfo import ZoneInfo

def merge_data(ohlc_obj_df, data_obj_df):
    latestData = {}
    if len(data_obj_df.keys()) == 0:
        return ohlc_obj_df

    for stock in data_obj_df:
        try:
            if stock not in ohlc_obj_df:
                continue
            
            stock_dict = data_obj_df[stock].to_dict('records')
            for row in stock_dict:
                recent_db_date = ohlc_obj_df[stock]['DATE'][len(ohlc_obj_df[stock].index)-1]
                recent_live_date = row['DATE']
                if  recent_live_date > recent_db_date:
                    ohlc_obj_df[stock] = pd.concat([ohlc_obj_df[stock], pd.DataFrame([row])], ignore_index=True)
                
            latestData[stock] = ohlc_obj_df[stock]
        except:
            latestData[stock] = ohlc_obj_df[stock]
            st.toast(f'failed to merge {stock} data')

    return latestData


def is_market_open():
    try:
        market_json = requests.get("https://www.isthemarketopen.com/static/markets.json").json()
        nse = [market for market in market_json if market['id'] == 'NSE' and market['country'] == 'India']
        if len(nse) == 0:
            return -1
        
        nse = nse[0]
        now_time = datetime.datetime.now(tz=ZoneInfo(nse['tz'])).strftime("%H:%M")
        if now_time <= nse['close'] and now_time >= nse['open']:
            return 1

    except Exception as e:
        st.toast(str(e))
        return 0
    
    return -1