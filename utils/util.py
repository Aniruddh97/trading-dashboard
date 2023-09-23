import requests
import datetime
import pandas as pd
import streamlit as st

from .live import *
from .sqlite import *
from zoneinfo import ZoneInfo

def append_data(ohlc_obj_df, data_obj_df):
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
                elif recent_live_date == recent_db_date:
                    db_index = ohlc_obj_df[stock].index[ohlc_obj_df[stock]['DATE'] == recent_db_date].tolist()[0]
                    ohlc_obj_df[stock].loc[db_index, ['OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME']] = [row.OPEN, row.HIGH, row.LOW, row.CLOSE, row.VOLUME]
            latestData[stock] = ohlc_obj_df[stock]
        except:
            latestData[stock] = ohlc_obj_df[stock]
            st.toast(f'failed to merge {stock} data')

    return latestData


def reconcile_data(df_dict, period):
    pbar = st.progress(0, text=f"Analyzing data")

    i = 0
    for ticker in df_dict:
        i += 1
        pbar.progress(int((i)*(100/len(df_dict.keys()))), text=f"Reconciling {ticker}")

        db_df = df_dict[ticker]
        new_df = get_live_data(ticker=ticker, period=period)

        append_list = []
        for _, row in new_df.iterrows():
            index_list = db_df.index[db_df.DATE == row.DATE].tolist()
            
            if len(index_list) == 1:
                db_index = index_list[0]
                db_df.loc[db_index, ['OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME']] = [row.OPEN, row.HIGH, row.LOW, row.CLOSE, row.VOLUME]
            elif len(index_list) == 0:
                append_list.append({
                    "DATE": row.DATE,
                    "OPEN": row.OPEN,
                    "HIGH": row.HIGH,
                    "LOW": row.LOW,
                    "CLOSE": row.CLOSE,
                    "VOLUME": row.VOLUME,
                })

        if len(append_list) > 0:
            db_df = pd.concat([db_df, pd.DataFrame(append_list)], ignore_index=True)

        replace_olhc_table(table=ticker, df=db_df)

    pbar.progress(100, text=f"Reconciliation complete")


def is_market_open():
    try:
        meta = readJSON(METADATA_FILE_PATH)
        if 'Holidays' in meta:
            holidays = meta['Holidays']
            for holiday in holidays:
                hdate = datetime.datetime.strptime(holiday, DATE_FORMAT).date()
                if hdate == datetime.date.today():
                    return -1

        date_today = datetime.datetime.today()
        if date_today.weekday() == 5 or date_today.weekday() == 6:
            return -1

        now_time = datetime.datetime.now(tz=ZoneInfo('Asia/Kolkata')).strftime("%H:%M")
        if now_time < '15:30' and now_time >= '09:15':
            return 1

    except Exception as e:
        st.toast(str(e))
        return 0
    
    return -1


def most_recent_data(tickers, progress=True):
    live_data = {}
    if is_market_open() == 1:
        live_data = get_live_data_collection(tickers=tickers, progress=progress)

    ohlc_obj_df = load_db_data(tickers=tickers)
    ohlc_obj_df = append_data(ohlc_obj_df=ohlc_obj_df, data_obj_df=live_data)

    return ohlc_obj_df
