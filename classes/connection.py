#
# Mario Torre - 04/20/2023
#
from json import JSONEncoder
import re
import os
import json

from UI.alerts import set_alert_message
from classes.exception_classes import BackupFileError, ConfigFileReadError, ConfigFileWriteError
from lib.miscfuncs import copyFile

class Connection(object):
        
    def __init__(self, dict):
        vars(self).update(dict)

    def StoreConnection(self, config):
        
        connection_dir = config['dirs']['connection_dir']
        connection_file = config['dirs']['connection_file']
        connection_file_bck = config['dirs']['connection_file_bck']
        #
        # Backup the old json file
        #
        ok = True
        try:
            copyFile(os.path.join(connection_dir, connection_file), os.path.join(connection_dir, connection_file_bck))
        except Exception as e:
            raise BackupFileError (e)

        if ok == True:
            try:
                with open(os.path.join(connection_dir, connection_file), 'w') as json_file:
                    json.dump(self, json_file, indent=4, cls=ConnectionEncoder)
            except Exception as e:
                try:
                    copyFile(os.path.join(connection_dir, connection_file_bck), os.path.join(connection_dir, connection_file))
                    with open(os.path.join(connection_dir, connection_file)) as json_file:
                        j = json.loads(json_file)
                        self = Connection(**j)
                except Exception as e:
                    raise ConfigFileReadError(e)
                raise ConfigFileWriteError(e)

        return

#####################################################################################
class ConnectionEncoder(JSONEncoder):
    def default(self, o):
            return o.__dict__

class Credentials(object):
    def __init__(self, user_name, password):
        self.user_name = user_name
        self.password = password

    def Validate(self):
        return not ((self.user_name == "") or (self.password == ""))

    @staticmethod
    def validateUrl(url):
        regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return (re.match(regex, url) is not None)
    
    @staticmethod
    def validateServer(server):
        return (server != "") 

    @staticmethod
    def validateDB(db):
        return (db != "") 