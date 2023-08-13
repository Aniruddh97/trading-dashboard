import requests
import pandas as pd
import streamlit as st

from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


class NSE:
	session = None

	def __init__(self):
		self.session = requests.Session()
		retry = Retry(connect=3, backoff_factor=0.5)
		adapter = HTTPAdapter(max_retries=retry)
		self.session.mount('http://', adapter)
		self.session.mount('https://', adapter)
		# self.session.headers.update({"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"})
		self.session.headers.update(
			{
				'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36', 
				'Host': 'www.nseindia.com'
			}
		)
		self.session.get("https://www.nseindia.com/")
    

	def fetchIndices(self):
		jsonData = self.session.get("https://www.nseindia.com/api/allIndices").json()
		
		indexList = []
		indexData = {}
		currentDate = pd.to_datetime(jsonData['timestamp']).date()
		
		for idx in jsonData['data']:
			indexList.append(idx['indexSymbol'])
			indexData[idx['indexSymbol']] = {
				'DATE': currentDate,
				'OPEN': idx['open'],
				'HIGH': idx['high'],
				'LOW': idx['low'],
				'COLSE': idx['last'],
				'VOLUME': 0,
			}

		return { 'raw': jsonData, 'list': indexList, 'data': indexData}


	def fetchIndexStocks(self, indiceName):
		params = {'index': indiceName}
		jsonData = self.session.get(url="https://www.nseindia.com/api/equity-stockIndices", params=params).json()
		
		tickerList = []
		tickerData = {}
		for stock in jsonData['data']:
			tickerList.append(stock['symbol'])
			tickerData[stock['symbol']] = {
				'DATE': pd.to_datetime(stock['lastUpdateTime']).date(),
				'OPEN': stock['open'],
				'HIGH': stock['dayHigh'],
				'LOW': stock['dayLow'],
				'CLOSE': stock['lastPrice'],
				'VOLUME': stock['totalTradedVolume'],
			}

		return { 'raw': jsonData, 'list': tickerList, 'data': tickerData}
