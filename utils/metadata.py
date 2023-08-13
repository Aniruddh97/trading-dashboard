import os
import json

from utils import METADATA_FILE_PATH

def writeJSON(obj, file_path=METADATA_FILE_PATH):
	with open(file_path, 'w+') as outfile:
		json.dump(obj, fp=outfile, indent=4, sort_keys=True, default=str)
    

def readJSON(file_path=METADATA_FILE_PATH):
	if os.path.isfile(file_path):
		with open(file_path) as json_file:
			return json.load(json_file)
	return {}