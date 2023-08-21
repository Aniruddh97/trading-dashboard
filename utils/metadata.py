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
	if 'watchlist' in meta:
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
	if 'watchlist' in meta:
		meta['watchlist'].remove(ticker)
		writeJSON(meta)
		st.session_state['watchlist'] = []