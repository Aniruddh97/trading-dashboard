import os
import sqlite3
import datetime
import pandas as pd
import streamlit as st

from .live import *
from .metadata import *
from .constants import *
from .datemodule import *
from jugaad_data.nse import bhavcopy_save, bhavcopy_index_save

def create_stock_database(start_date, end_date, database_path=STOCK_DATABASE_PATH):
    if os.path.isfile(database_path):
        os.remove(database_path)
        
    
    conn = sqlite3.connect(database_path)
    stockData = bhavcopy_stock_range(start_date=start_date, end_date=end_date)
    
    i = 0
    my_bar = st.progress(0, text="Populating database")
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
    my_bar = st.progress(0, text="Populating indice database")
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
    my_bar = st.progress(0, text="Downloading stock data")
    
    meta = readJSON(METADATA_FILE_PATH)
    tickerList = []
    if 'LIST' in meta:
        tickerList = list(set([ticker for indice in meta['LIST'] for ticker in meta['LIST'][indice]]))
    
    if len(tickerList) == 0:
        st.error("No stocks found in metadata file")
        return {}
    
    for current_date in getDateRange(start_date, end_date):
        i += 1
        my_bar.progress(int((i)*(100/size)), text='Downloading stock data')
        
        if current_date.weekday() == 5 or current_date.weekday() == 6:
            continue

        try:
            path = bhavcopy_save(current_date, DATA_DIR_PATH)
            data = pd.read_csv(path, encoding='latin-1')
            data = data[data['SERIES'] == 'EQ']
            os.remove(path)

            for index, row in data.iterrows():
                if row['SYMBOL'] not in tickerList:
                    continue

                if row['SYMBOL'] not in stockData:
                    stockData[row['SYMBOL']] = []
                
                stockData[row['SYMBOL']].append({
                    "DATE": current_date,
                    "OPEN": row['OPEN'],
                    "HIGH": row['HIGH'],
                    "LOW": row['LOW'],
                    "CLOSE": row['CLOSE'],
                    "VOLUME": row['TOTTRDQTY'],
                })
        except Exception as e:
            st.toast(str(e))
            continue
    
    return stockData


def bhavcopy_index_range(start_date, end_date):
    i = 0
    indiceData = {}
    size = int((end_date - start_date).days)+1
    my_bar = st.progress(0, text="Downloading index data")

    for current_date in getDateRange(start_date, end_date):
        i += 1
        my_bar.progress(int((i)*(100/size)), text='Downloading index data')

        if current_date.weekday() == 5 or current_date.weekday() == 6:
            continue

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
        except Exception as e:
            st.toast(str(e))
            continue

    return indiceData


def update_db_data(start_date, end_date):
    meta = readJSON()
    newStockData = bhavcopy_stock_range(start_date=start_date, end_date=end_date)
    dbStockData = load_db_data(tickers=meta['LIST']['NIFTY 500'])

    if len(newStockData.keys()) == 0:
        st.warning('Failed to fetch from NSE, trying with yfinance for NIFTY 50')
        tickerList = meta['LIST']['NIFTY 500']
        delta = end_date - start_date
        newStockData = get_live_data_collection(tickers=tickerList, period=f'{delta.days}d')
        # convert df to dict
        for stock in newStockData:
            newStockData[stock] = newStockData[stock].to_dict('records')

    i = 0
    my_bar = st.progress(0, text="Syncing DB")
    for ticker in dbStockData:
        i += 1
        my_bar.progress(int((i)*(100/len(dbStockData.keys()))), text=f"Syncing {ticker}")
        if ticker not in newStockData:
            continue

        db_df = dbStockData[ticker]
        ticker_dict_array = newStockData[ticker]

        append_list = []
        for row in ticker_dict_array:
            index_list = db_df.index[db_df.DATE == row['DATE']].tolist()
            
            if len(index_list) == 1:
                db_index = index_list[0]
                db_df.loc[db_index, ['OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME']] = [row['OPEN'], row['HIGH'], row['LOW'], row['CLOSE'], row['VOLUME']]
            elif len(index_list) == 0:
                append_list.append({
                    "DATE": row['DATE'],
                    "OPEN": row['OPEN'],
                    "HIGH": row['HIGH'],
                    "LOW": row['LOW'],
                    "CLOSE": row['CLOSE'],
                    "VOLUME": row['VOLUME'],
                })

        if len(append_list) > 0:
            db_df = pd.concat([db_df, pd.DataFrame(append_list)], ignore_index=True)

        db_df = db_df.sort_values(by="DATE", ascending=True).reset_index(drop=True)
        replace_olhc_table(table=ticker, df=db_df)

    my_bar.progress(100, text=f"DB Sync complete")


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


def replace_olhc_table(table, df):
    if df.empty:
        return
    
    if does_exist(table=table, db_path=STOCK_DATABASE_PATH):
        replace_table(table=table, df=df, db_path=STOCK_DATABASE_PATH)
    elif does_exist(table=table, db_path=INDICE_DATABASE_PATH):
        replace_table(table=table, df=df, db_path=INDICE_DATABASE_PATH)
    else:
        st.toast(f'{table} does not exist')


def replace_table(table, df, db_path):
    if df.empty:
        return
    
    query = f'''
        DROP TABLE IF EXISTS `{table}`
    '''
    conn = sqlite3.connect(db_path)
    try:
        df.to_sql(name=table, con=conn, if_exists='replace', index=False)
    except:
        execute_query(database_path=db_path, query=query)
        df.to_sql(name=table, con=conn, if_exists='replace', index=False)

    conn.commit()
    conn.close()


def does_exist(table, db_path):
    exists = False

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
                
    #get the count of tables with the name
    c.execute(f'''SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table}' ''')

    #if the count is 1, then table exists
    if c.fetchone()[0] == 1:
        exists = True
    
    conn.commit()
    conn.close()

    return exists


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


def update_query(database_path, query, data):
    try :
        conn = sqlite3.connect(database_path)
        conn.execute(query, data)
    except sqlite3.OperationalError:
        st.toast(f"No such table: {query} for {database_path}")
    except:
        st.toast(f"Error: {query} for {database_path}")
    finally:
        conn.commit()
        conn.close()


def save_order(ticker, start_date, strike_price, target, stoploss, units):
    rrr = abs(target - strike_price)/abs(stoploss - strike_price)
    position = 'LONG' if target > strike_price else 'SHORT'

    order = pd.DataFrame([{
        'ticker': ticker,
        'start_date': start_date,
        'end_date': None,
        'position': position,
        'result': None,
        'target': target,
        'strike_price': strike_price,
        'stoploss': stoploss,
        'units': int(units),
        'rrr': rrr,
    }])

    conn = sqlite3.connect(ORDER_DATABASE_PATH)
    if does_exist("orders", ORDER_DATABASE_PATH):
        query = """
            SELECT * FROM orders;
        """
        orders_df = execute_query(database_path=ORDER_DATABASE_PATH, query=query)
        orders_df = pd.concat([orders_df, order], ignore_index=True)
        
        orders_df.to_sql(name='orders', con=conn, if_exists='replace', index=False)
    else:
        order.to_sql(name='orders', con=conn, if_exists='replace', index=False)

    conn.commit()
    conn.close()
