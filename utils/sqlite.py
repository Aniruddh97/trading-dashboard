import os
import sqlite3
import pandas as pd
import streamlit as st

from jugaad_data.nse import bhavcopy_save, bhavcopy_index_save
from utils import getDateRange, readJSON, writeJSON, METADATA_FILE_PATH, INDICE_DATABASE_PATH, STOCK_DATABASE_PATH, DATA_DIR_PATH


def create_stock_database(start_date, end_date, database_path=STOCK_DATABASE_PATH):
    if os.path.isfile(database_path):
        os.remove(database_path)
        
    
    conn = sqlite3.connect(database_path)
    stockData = bhavcopy_stock_range(start_date=start_date, end_date=end_date)
    
    i = 0
    my_bar = st.sidebar.progress(0, text="Populating database")
    for stock in stockData:
        i += 1
        df = pd.DataFrame(stockData[stock])
        my_bar.progress(int((i)*(100/len(stockData))), text=f'Populating database : {stock}')
        df.to_sql(name=stock, con=conn, if_exists='replace', index=False)
        
    conn.commit()
    conn.close()
    

def create_indice_database(start_date, end_date, database_path=INDICE_DATABASE_PATH):
    if os.path.isfile(database_path):
        os.remove(database_path)
        
    conn = sqlite3.connect(database_path)
    indiceData = bhavcopy_index_range(start_date=start_date, end_date=end_date)
   
    i = 0
    my_bar = st.sidebar.progress(0, text="Populating indice database")
    for index in indiceData:
        i += 1
        df = pd.DataFrame(indiceData[index])
        my_bar.progress(int((i)*(100/len(indiceData))), text=f'Populating indice database : {index}')
        df.to_sql(name=index, con=conn, if_exists='replace', index=False)
        
    conn.commit()
    conn.close()
    

def bhavcopy_stock_range(start_date, end_date):
    i = 0
    stockData = {}
    size = int((end_date - start_date).days)+1
    my_bar = st.sidebar.progress(0, text="Downloading stock data")
    
    for current_date in getDateRange(start_date, end_date):
        i += 1
        my_bar.progress(int((i)*(100/size)), text='Downloading stock data')

        try:
            path = bhavcopy_save(current_date, DATA_DIR_PATH)
            data = pd.read_csv(path, encoding='latin-1')
            data = data[data['SERIES'] == 'EQ']
            os.remove(path)

            for index, row in data.iterrows():
                if row.SYMBOL not in stockData:
                    stockData[row.SYMBOL] = []
                
                stockData[row.SYMBOL].append({
                    "DATE": current_date,
                    "OPEN": row.OPEN,
                    "HIGH": row.HIGH,
                    "LOW": row.LOW,
                    "CLOSE": row.CLOSE,
                    "VOLUME": row.TOTTRDQTY,
                })
        except:
            continue
    
    return stockData


def bhavcopy_index_range(start_date, end_date):
    i = 0
    indiceData = {}
    size = int((end_date - start_date).days)+1
    my_bar = st.sidebar.progress(0, text="Downloading index data")

    for current_date in getDateRange(start_date, end_date):
        i += 1
        my_bar.progress(int((i)*(100/size)), text='Downloading index data')

        try:
            path = bhavcopy_index_save(current_date, DATA_DIR_PATH)
            data = pd.read_csv(path, encoding='latin-1')
            os.remove(path)

            for index, row in data.iterrows():
                # whitelist
                # if row['Index Name'] not in ['Nifty 50', 'Nifty Bank']:
                #     continue

                if row['Index Name'] not in indiceData:
                    indiceData[row['Index Name']] = []
                
                indiceData[row['Index Name']].append({
                    "DATE": current_date,
                    "OPEN": row['Open Index Value'],
                    "HIGH": row['High Index Value'],
                    "LOW": row['Low Index Value'],
                    "CLOSE": row['Closing Index Value'],
                    "VOLUME": row['Volume'],
                })
        except:
            continue

    return indiceData


def update_db_data(start_date, end_date):
    stockData = bhavcopy_stock_range(start_date=start_date, end_date=end_date)
    indiceData = bhavcopy_index_range(start_date=start_date, end_date=end_date)

    i = 0
    conn = sqlite3.connect(STOCK_DATABASE_PATH)
    my_bar = st.sidebar.progress(0, text="Populating stock database")
    for stock in stockData:
        i += 1
        query=f'''
            INSERT INTO `{stock}` VALUES (:DATE,:OPEN,:HIGH,:LOW,:CLOSE,:VOLUME)
        '''
        for entry in stockData[stock]:
            try:
                my_bar.progress(int((i)*(100/len(stockData.keys()))), text=f'Populating stock database : {stock}')
                conn.execute(query, entry)
            except Exception as e:
                st.toast(str(e))
        conn.commit()
    conn.close()

    i = 0
    conn = sqlite3.connect(INDICE_DATABASE_PATH)
    my_bar = st.sidebar.progress(0, text="Populating stock database")
    for indice in indiceData:
        i += 1
        query=f'''
            INSERT INTO `{indice}` VALUES (:DATE,:OPEN,:HIGH,:LOW,:CLOSE,:VOLUME)
        '''
        for entry in indiceData[indice]:
            try:
                my_bar.progress(int((i)*(100/len(indiceData.keys()))), text=f'Populating index database : {indice}')
                conn.execute(query, entry)
            except Exception as e:
                st.toast(str(e))
        conn.commit()
    conn.close()
    
    meta = readJSON(METADATA_FILE_PATH)
    meta['last_sync_date'] = end_date
    writeJSON(meta, METADATA_FILE_PATH)
    
    st.toast("Data update completed")

def load_db_data(tickers):
    ohlcData = {}
    for ticker in tickers:
        df = execute_query(
            database_path=STOCK_DATABASE_PATH, 
            query=f"SELECT * FROM `{ticker}`"
        )
        if df is not None:
            df['DATE'] = pd.to_datetime(df.DATE).dt.date
            ohlcData[ticker] = df
        else:
            df = execute_query(
                database_path=INDICE_DATABASE_PATH, 
                query=f"SELECT * FROM `{ticker}`"
            )
            if df is not None:
                df['DATE'] = pd.to_datetime(df.DATE).dt.date
                ohlcData[ticker] = df
                
    return ohlcData
                    

def execute_query(database_path, query):
    df = None
    try :
        conn = sqlite3.connect(database_path)
        df = pd.read_sql_query(query, conn)
    except sqlite3.OperationalError:
        st.toast(f"No such table: {query} for {database_path}")
    except:
        st.toast(f"Error: {query} for {database_path}")
    finally:
        conn.commit()
        conn.close()
    return df