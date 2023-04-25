#
# Mario Torre - 04/20/2023
#
from optparse import OptionParser
from threading import Event
import os
import json
from classes.api_classes import AvalonAPIToken
from classes.connection import Connection
from lib.logs import Logs, get_logger

from lib.miscfuncs import text_to_log_level
from UI.display_panel import display_panel
#
# Load config file
#
config_dir = 'config/'
config_file = 'config.json'
try:
    with open(os.path.join(config_dir, config_file)) as json_file:
        config = json.load(json_file)
except Exception as e:
    print('Cannot read System configuration file. Program ABORTED. Error: %s', str(e))
    exit()
#
# configure the service logging
#
stream = Logs()
logger = get_logger(__name__, stream, config['log']['format'])
logger.info('Histdata-loader Panel INITIATED')
logger.setLevel (text_to_log_level(config['log']['level']))
logger.debug("Configuration file " + os.path.join(config_dir, config_file) + " successfully read.")
#
# Load panel config file
#
panel_config_dir = config['dirs']['panel_config_dir']
panel_config_file = config['dirs']['panel_config_file']
try:
    with open(os.path.join(panel_config_dir, panel_config_file)) as json_file:
        panel_config = json.load(json_file)
except Exception as e:
    print('Cannot read Panel configuration file. Program ABORTED. Error: %s', str(e))
    exit()

logger.debug("Panel Configuration file " + os.path.join(panel_config_dir, panel_config_file) + " successfully read.")
#
# Load connection file
#
connection_dir = config['dirs']['connection_dir']
connection_file = config['dirs']['connection_file']
try:
    with open(os.path.join(connection_dir, connection_file)) as json_file:
        connection = json.load(json_file, object_hook=Connection)
except Exception as e:
    print('Cannot read Connection configuration file. Program ABORTED. Error: %s', str(e))
    exit()
logger.debug("Connection file " + os.path.join(connection_dir, connection_file) + " successfully read.")
#
# Read command line parameters
# 
parser = OptionParser()
try:
    parser.add_option ("-v", "--version", dest="version", action="store_true", help=config['opts']['version_help'], default=False)
    parser.add_option ("-w", "--webport", dest="web_port", action="store", help=config['opts']['webport_help'], default=config['app']['web_default_port'])
    (options, args) = parser.parse_args()
except Exception as e:
    logger.error("Invalid parameters. Try again. Error: " + str(e) + ". Program ABORTED.")
    exit()
#
# check parameters
# also Check if Environment variables were defined
# Note: Environment variables takes precedence over arguments.
#
if (options.version == True):
    print("version: " + config['version'])
    exit()
try:
    web_port = int(options.web_port)
    web_port = int(os.environ.get(config['env']['web_port'], web_port))
except Exception as e:
    logger.error("Found invalid web port Number, either on command line or env variable. Try again. Error: " + str(e) + ". Program ABORTED.")
    exit()
#
# Print version
#
logger.info('Version: ' + config['version'])
#
# Create an event to end the application
#     
event = Event()
session_token = AvalonAPIToken()
#
# ----------------------------------------------------------------------- #
# run the displayer (only if valid web port is configured)
# ----------------------------------------------------------------------- #
if web_port > 0:
        try: 
            logger.info('Listening on port ' + str(web_port)) 
            #thread2 = Thread(target=display_panel, args=(logger, config, panel_config, con_config, web_port, event))
            display_panel(logger, config, panel_config, connection, web_port, session_token, stream, event)
            #thread2.start()
        except Exception as e:
            logger.error("Exception trying to start Displayer. Error: " + str(e) + ". Program ABORTED.")
            exit()
        logger.debug("Display code has been initiated successfully.")
else:
    logger.info('Web access is disabled') 

