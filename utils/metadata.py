import os
import json
import streamlit as st

from .constants import *

def writeJSON(obj, file_path=METADATA_FILE_PATH):
	with open(file_path, 'w+') as outfile:
		json.dump(obj, fp=outfile, indent=4, sort_keys=True, default=str)
    

def readJSON(file_path=METADATA_FILE_PATH):
	if os.path.isfile(file_path):
		with open(file_path) as json_file:
			return json.load(json_file)
	return {}


def addToWatchlist(ticker, file_path=METADATA_FILE_PATH):
	meta = readJSON()
	if 'watchlist' not in meta:
		return
	
	if ticker in meta['watchlist']:
		st.toast(f'`{ticker}` already in watchlist')
		return
	
	meta['watchlist'].append(ticker)
	writeJSON(meta)
	st.session_state['watchlist'] = []
	st.toast(f'Added `{ticker}` to watchlist')


def removeFromWatchlist(ticker, file_path=METADATA_FILE_PATH):
	meta = readJSON()
	if 'watchlist' not in meta:
		return
	
	meta['watchlist'].remove(ticker)
	writeJSON(meta)
	st.session_state['watchlist'] = []
	st.toast(f'Removed `{ticker}` from watchlist')
	st.experimental_rerun()


def getPivotWindow():
	meta = readJSON()
	if 'settings' not in meta:
		return 11
	
	if 'pivot_window' not in meta['settings']:
		return 11
	
	return int(meta['settings']['pivot_window'])


def getChartHeight():
	meta = readJSON()
	if 'settings' not in meta:
		return 500
	
	if 'chart_height' not in meta['settings']:
		return 500
	
	return int(meta['settings']['chart_height'])


def getCandleCount():
	meta = readJSON()
	if 'settings' not in meta:
		return 50
	
	if 'candle_count' not in meta['settings']:
		return 50
	
	return int(meta['settings']['candle_count'])


def doPatternRecognition():
	meta = readJSON()
	if 'settings' not in meta:
		return True
	
	if 'pattern_recognition' not in meta['settings']:
		return True
	
	return meta['settings']['pattern_recognition']


def getSortBySetting():
	meta = readJSON()
	if 'settings' not in meta:
		return 'Pattern Rank', True
	
	if 'sort_by' not in meta['settings']:
		return 'Pattern Rank', True
	
	if meta['settings']['sort_by'] == 'Pattern Rank':
		return 'Pattern Rank', True
	
	if meta['settings']['sort_by'] == 'Proximity %':
		return 'Proximity %', True
	
	return 'Volume Up %', False


def getFilterBySetting():
	meta = readJSON()
	if 'settings' not in meta:
		return []
	
	if 'pattern_filter' not in meta['settings']:
		return []
	
	return meta['settings']['pattern_filter']


def getIndicatorSetting():
	meta = readJSON()
	if 'settings' not in meta:
		return []
	
	if 'indicator' not in meta['settings']:
		return []
	
	return meta['settings']['indicator']


def useWideLayout():
	meta = readJSON()
	if 'settings' not in meta:
		return False
	
	if 'wide_layout' not in meta['settings']:
		return False
	
	return meta['settings']['wide_layout']


def useSlider():
	meta = readJSON()
	if 'settings' not in meta:
		return False
	
	if 'slider' not in meta['settings']:
		return False
	
	return meta['settings']['slider']