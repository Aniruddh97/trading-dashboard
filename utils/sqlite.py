import os
import time
import sqlite3
import pandas as pd
import streamlit as st

from utils import getStartEndDate, getDateRange
from jugaad_data.nse import bhavcopy_save, bhavcopy_index_save


def create_stock_database(database_path="./data/stock_database.sqlite", duration='1y'):
    os.remove(database_path)
    conn = sqlite3.connect(database_path)
    
    start_date, end_date = getStartEndDate(duration)
    stockData = bhavcopy_stock_range(start_date=start_date, end_date=end_date)

    i = 0
    my_bar = st.sidebar.progress(0, text="Populating database")
    for stock in stockData:
        i += 1
        df = pd.DataFrame(stockData[stock])
        df.to_sql(name=stock, con=conn, if_exists='replace', index=False)
        my_bar.progress(int((i)*(100/len(stockData))), text=f'Populating database : {stock}')
        
    conn.commit()
    conn.close()
    

def create_indice_database(database_path="./data/indice_database.sqlite",duration='1y'):
    os.remove(database_path)
    conn = sqlite3.connect(database_path)
    
    start_date, end_date = getStartEndDate(duration)
    indiceData = bhavcopy_index_range(start_date=start_date, end_date=end_date)
    
    i = 0
    my_bar = st.sidebar.progress(0, text="Populating indice database")
    for index in indiceData:
        i += 1
        df = pd.DataFrame(indiceData[index])
        df.to_sql(name=index, con=conn, if_exists='replace', index=False)
        my_bar.progress(int((i)*(100/len(indiceData))), text=f'Populating indice database : {index}')
        
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
            path = bhavcopy_save(current_date, "./data")
            data = pd.read_csv(path, encoding='latin-1')
            data = data[data['SERIES'] == 'EQ']

            # remove csv files
            dir_name = "./data"
            directoryItems = os.listdir(dir_name)
            for item in directoryItems:
                if item.endswith(".csv"):
                    os.remove(os.path.join(dir_name, item))


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
            path = bhavcopy_index_save(current_date, "./data")
            data = pd.read_csv(path, encoding='latin-1')

            # remove csv files
            dir_name = "./data"
            directoryItems = os.listdir(dir_name)
            for item in directoryItems:
                if item.endswith(".csv"):
                    os.remove(os.path.join(dir_name, item))
        

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
    st.write(pd.DataFrame(stockData['TCS']).to_records(index=False))

    conn = sqlite3.connect("./data/stock_database.sqlite")
    for stock in stockData:
        df = pd.DataFrame(stockData[stock])

        # query=f'''
        #     INSERT INTO `{stock}` (`DATE`, `OPEN`, `HIGH`, `LOW`, `CLOSE`, `VOLUME`) VALUES (?,?,?,?,?,?)
        # '''
        # conn.executemany(query, df.to_records(index=False))
        query=f'''
            INSERT INTO `{stock}` VALUES (:DATE,:OPEN,:HIGH,:LOW,:CLOSE,:VOLUME)
        '''
        for entry in stockData[stock]:
            conn.execute(query, entry)
        conn.commit()
    conn.close()

    conn = sqlite3.connect("./data/indice_database.sqlite")
    for indice in indiceData:
        df = pd.DataFrame(indiceData[indice])

        # query=f'''
        #     INSERT INTO `{indice}` (`DATE`, `OPEN`, `HIGH`, `LOW`, `CLOSE`, `VOLUME`) VALUES (?,?,?,?,?,?)
        # '''
        # conn.executemany(query, df.to_records(index=False))
        query=f'''
            INSERT INTO `{indice}` VALUES (:DATE,:OPEN,:HIGH,:LOW,:CLOSE,:VOLUME)
        '''
        for entry in indiceData[indice]:
            conn.execute(query, entry)
        conn.commit()
    conn.close()
    
    st.toast("Data update completed")

def load_db_data(stockList):
    ohlcData = {}
    for ticker in stockList:
        df = execute_query(
            database_path='./data/stock_database.sqlite', 
            query=f"SELECT * FROM `{ticker}`"
        )
        if df is not None:
            df['DATE'] = pd.to_datetime(df.DATE).dt.date
            ohlcData[ticker] = df
        else:
            df = execute_query(
                database_path='./data/indice_database.sqlite', 
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