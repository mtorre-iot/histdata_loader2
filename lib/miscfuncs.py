#
# Mario Torre - 04/20/2023
#
# --------------------------------------------------------------------------- #
import base64
from datetime import tzinfo
import logging
import os
import random
import shutil
import string
from dateutil import tz
import numpy as np
import pytz
import pandas as pd

def text_to_log_level (str):
    if str=="INFO":
        return logging.INFO
    if str=="DEBUG":
        return logging.DEBUG
    if str=="WARN":
        return logging.WARN
    if str=="ERROR":
        return logging.ERROR
    return logging.DEBUG

def stringToBase64(s):
    return base64.b64encode(s.encode('utf-8'))

def base64ToString(b):
    return base64.b64decode(b).decode('utf-8')

def copyFile(src, dst):
    shutil.copyfile(src, dst)

def add_column_prefix(prefix, str):
    return (prefix + str)

def convertUTCtoLocalDateTime (dt):
    rtn = None
    if dt != None:
        rtn = dt.astimezone(tz.tzlocal())
    return rtn

def convertLocalDateTimetoUTC(dt):
    return dt.astimezone(pytz.UTC)

def removeTimezoneDateTime(dt):
    rtn = None
    if dt != None:
        rtn = dt.replace(tzinfo=None)
    return rtn

def convert_array_to_dict(dict_array, name, id):
    rtn = {}
    for pair in dict_array:
        rtn[pair[name]]= pair[id]
    return rtn
 
def convert_deltat_symbol_to_seconds(symbol, dict):
    for item in dict:
        if item['freq'] == symbol:
            return item['seconds']
    return None
    
def generate_random_string(size):
    return (''.join(random.choice(string.ascii_lowercase) for i in range (size)))

def get_names_only(dict_array):
    rtn = []
    for dc in dict_array:
        rtn.append(dc.name)
    return rtn

def get_file_name_no_ext(full_file_name):
    return os.path.splitext(os.path.basename(full_file_name))[0]

def get_extension_from_filename(full_file_name):
    name = get_file_name_with_ext(full_file_name)
    _, ext =os.path.splitext(name)
    return ext

def get_file_name_with_ext(full_file_name):
    return os.path.basename(full_file_name)

def convert_none_to_nan(v):
    rtn = v
    if v == None:
        rtn = np.nan
    return rtn

def convert_none_to_int(v):
    rtn = v
    if v == None:
        rtn = 0
    return rtn

def convert_text_to_bool(v):
    if v == "YES":
        return True
    if v == "NO":
        return False
    return None

def convert_bool_text(v):
    if v == True:
        return "YES"
    if v == False:
        return "NO"
    return "X"