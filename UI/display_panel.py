#
# Mario Torre - 04/20/2023
#
import asyncio
from datetime import datetime, timedelta
from io import BytesIO
import os
from pathlib import Path
import webbrowser
from build_upload_file import build_upload_file
from fill_data_frame import fill_data_frame
from histdata_read import histdata_read
import numpy as np
import panel as pn
import pandas as pd
from UI.alerts import set_alert_message, show_alert_general
from classes.api_classes import AvalonAssets, AvalonCustomerDetails, AvalonCustomers, AvalonCustomerDetails, AvalonEngUnits, AvalonEvents, AvalonOrgUnits, AvalonTags, AvalonTagsDetails, AvalonValues, AvalonSetpoint, CurrentSelection, TagBackfillFullInfo, TagFullInfo
from classes.connection import Credentials
#from classes.db_classes import ColumnData, DBConnection

from classes.displaypanelcomponents import DynaPanelComponents
from bokeh.models.widgets.tables import DateFormatter
from classes.exception_classes import BackupFileError, ConfigFileReadError, ConfigFileWriteError
#from lib.dbfuncs import add_customer_and_asset, adjust_data_types, merge_dataframes, remove_last_row, round_datetime
#from lib.fill_data_frame import fill_data_frame_type_1, fill_data_frame_type_2
#from lib.fill_event_frame import fill_event_frame_type_1
from lib.miscfuncs import add_column_prefix, convert_array_to_dict, convert_bool_text, convert_deltat_symbol_to_seconds, convert_text_to_bool, convertLocalDateTimetoUTC, copyFile, generate_random_string, get_extension_from_filename, get_file_name_no_ext, get_names_only, removeTimezoneDateTime

pitems = DynaPanelComponents()

# ----------------------------------------------------------------------------- #
# Startup Initialization
# ----------------------------------------------------------------------------- #
def init():
    api_test_button_callback(None) # fire the API test
    #db_test_button_callback(None)  # fire the DB test
    select_assets() # do the asset selection
    return
# ----------------------------------------------------------------------------- #
# Callbacks 
# ----------------------------------------------------------------------------- #
def api_update_button_callback(event):
    global api_connection, db_connection, token_connection, connection
    #
    # Let's check if new parameters are valid
    #
    test_basic_url = pitems.api_url.value
    test_user_name = pitems.user_name.value
    test_password = pitems.password.value
    cr = Credentials(test_user_name, test_password)
    connection_valid = cr.Validate() and Credentials.validateUrl(test_basic_url)
    
    if (connection_valid == False):
        logger.error("Provided credentials are invalid. Please check.")
        show_alert(6, None)
        #
        # Restore old values in screen
        #
        pitems.api_url.value = api_connection.basic_url
        pitems.user_name.value = api_connection.credentials.user_name
        pitems.password.value = api_connection.credentials.password
        return
    #
    # Check if any changes were done at the connection parameters
    #
    if (pitems.api_url.value == api_connection.basic_url) and \
        (pitems.user_name.value == api_connection.credentials.user_name) and \
            (pitems.password.value == api_connection.credentials.password):
            #
            # no changes were detected. Warn the user anyway
            #
            logger.debug("No configuration changes were detected.")
            show_alert(1, None)
    else:
        #
        # Changes were detected. 
        # Update the connection file then
        #
        api_connection.basic_url = pitems.api_url.value
        api_connection.credentials.user_name = pitems.user_name.value
        api_connection.credentials.password = pitems.password.value

        StoreCurrentConnection(True)
        logger.debug("New configuration parameters were succesfully stored.")
        #
        # Refresh the token right away
        #
        api_test_button_callback(None)
    return

def api_test_button_callback(event):
    # 
    # this tests the API connection by requiring a token.
    # token is stored for future API request until refresh is needed.
    #
    global api_connection, token_connection
    enable_controls = True
    try:
        logger.debug("Trying to get Token...")
        session_token.Request_token(api_connection, config)
        pitems.api_connection_ok.value = True
        pitems.api_token_ok.value = True
        logger.debug("Token succesfully obtained.")
        show_alert(4, None)
        #
        # Store in connection.json file
        #
        token_connection.full_url = session_token.url
        token_connection.headers = session_token.headers
        token_connection.payload = session_token.payload
        token_connection.operation = session_token.operation
        StoreCurrentConnection()

        logger.debug("API Token successfully received.")
    except Exception as e:
        pitems.api_connection_ok.value = False
        pitems.api_token_ok.value = False
        enable_controls = False
        logger.error("Error trying to obtain token from API Service. Error: " + str(e))
        show_alert(5, e)
    #
    # Enable / Disable controls accordingly
    #
    enableControls(enable_controls)
    #
    # Populate the selectors of next tab
    #
    if (pitems.api_connection_ok.value == True) and (pitems.api_token_ok.value == True):
        api_update_selection()
    ###     api_get_eng_units()

def upload_data_file_button_callback(event):
    # pitems.modal_component_1[:] = [pn.Row(pitems.file_dialog_1)]
    # pitems.modal_component_2[:] = [pn.Row(pn.Column(pitems.file_dialog_1_ok), pn.Column(pitems.file_dialog_1_cancel))]
    # tpl.open_modal()
    #
    # Get full file name from text input ant try to open it
    #
    df = pd.DataFrame()
    fullFileName = pitems.upload_data_file_textbox.value
    pitems.api_create_backfill_file_button.disabled = True
    pitems.api_initiate_backfill_button.disabled = True
    
    if len(fullFileName) > 0:
            try:
                df = histdata_read(logger, config, api_tags, fullFileName)
            except Exception as e:
                show_alert(17, e)
                logger.error(str(e))
                return         
    else:
        show_alert(17, fullFileName)       

    if (df.empty == False):
        #
        # Present data in Tabular 
        #
        try:
            df = fill_data_frame(logger, df)
        except Exception as e:
            show_alert(17, e)
            logger.error(str(e))
            return
        
        pitems.total_rows.value = df.shape[0]

        file_connection.full_name = fullFileName
        backfill_connection.customer_name = selection.selected_customer.name
        backfill_connection.customer_id = selection.selected_customer.id
        backfill_connection.asset_name = selection.selected_asset.name
        backfill_connection.asset_full_tree_name = selection.selected_asset.fullTreeName
        backfill_connection.asset_id = selection.selected_asset.id
        StoreCurrentConnection()
        #
        # try to show it on screen
        #
        pitems.data_table_widget.value = df
        pitems.api_create_backfill_file_button.disabled = False
        pitems.api_initiate_backfill_button.disabled = True
        show_alert(18, fullFileName)
        logger.info ("Data File " + fullFileName + " successfully loaded.")
    return

def api_initiate_backfill_callback(event):
    #
    # Check if we need to refresh the token
    #
    try:
        session_token.Refresh(api_connection, config)
    except Exception as e:
        logger.error("Error trying to refresh the API token. Error: " + str(e))
        show_alert(7, e)
        return
    #
    return
    
def api_create_backfill_file_callback(event):
    #
    # get the created data frame
    df = pitems.data_table_widget.value
    #
    # save the tag list of all tags identified from the file
    #
    tagNames = df.columns
    tag_backfill_full_info_array = []
    for i in range(1, len(tagNames)):
        tagData = api_tags.FindTagName(tagNames[i])
        tag_backfill_full_info_array.append(TagBackfillFullInfo(tagData.name, tagData.tagId, tagData.resolvedTag.dataSourceId, tagData.resolvedTag.physicalTagId)) 
    #
    # save filename into the connection information
    #
    backfill_connection.tag_backfill_full_info_array = tag_backfill_full_info_array
    StoreCurrentConnection()
    #
    # Create the upload csv file
    #
    try: 
        initial_time = pitems.start_datetime.value
        upload_df = build_upload_file(logger, initial_time, df, backfill_connection, config)
        logger.info("Upload file created successfully.")
    except Exception as e:
        show_alert(19, e)
        logger.error(str(e))
        return
    pitems.api_initiate_backfill_button.disabled = False
    pitems.update_table_widget.value = upload_df
    pitems.total_upload_rows.value = upload_df.shape[0]
    csvFile = os.path.join(config['dirs']['upload_dir'], config['dirs']['upload_file'])
    show_alert(21, csvFile)
    logger.info ("Upload File " + csvFile + " successfully created.")
# ----------------------------------------------------------------------------- #
# Misc Functions 
# ----------------------------------------------------------------------------- #
def enableControls(enable):
    pitems.upload_data_file_button.disabled = not enable
    pitems.customer_selector.disabled = not enable
    pitems.asset_selector.disabled = not enable
    pitems.upload_data_file_textbox.disabled = not enable
    return

def show_alert(alert, e):
    show_alert_general(alert, e, pitems, panel_config)
    return

def StoreCurrentConnection(positive_message_requested = False):
    try:
        ok = True 
        connection.StoreConnection(config)
    except (BackupFileError, ConfigFileReadError, ConfigFileWriteError) as e:
        logger.error('Configuration backup file could not be created. Error: %s', str(e))
        show_alert(3, e)
        ok = False 
    if (ok == True) and (positive_message_requested == True):
        logger.debug("Changes were updated and saved.")
        show_alert(2, None)
    return

def api_update_selection():
    #
    # Check if we need to refresh the token
    #
    try:
        session_token.Refresh(api_connection, config)
    except Exception as e:
        logger.error("Error trying to refresh the token. Error: " + str(e))
        show_alert(7, e)
        return
    #
    # Let's get the customer's list
    #
    try:
        api_customers.Request_customers(api_connection, session_token.token, config)
        logger.debug("System Customer data succesfully retrieved.")
    except Exception as e:
        logger.error("Error trying to refresh get the Avalon customers list. Error: " + str(e))
        show_alert(8, e)
        return
    # 
    # fill the customer selector
    #
    pitems.customer_selector.options = api_customers.Get_Customer_names()
    return

def query_hierarchy(customer_id, asset_id):
    if customer_id is not None:
        #
        # Check if we need to refresh the token
        #
        try:
            session_token.Refresh(api_connection, config)
        except Exception as e:
            logger.error("Error trying to refresh the API token")
            show_alert(7, e)
            return        
        #
        #  Get org unit hierarchy for this customer
        #
        try:
            api_org_units.Request_org_units(api_connection, customer_id, session_token.token, config)
            api_org_units.Fill_parents_name(api_customers)
        except Exception as e:
            logger.error("Error trying to get the Org Units for customer {0}. Error: {1}", customer_id, str(e))
            show_alert(31, e)
            return
        #
        # Bring up also all assets assigned to Customer or org unit
        #
        try:
            api_assets.Find_assets(api_org_units)
            api_assets.Find_full_tree_name(customer_id, api_org_units)
        except Exception as e:
            logger.error("Error trying to get the Assets - Org Units relationdship for customer {0}. Error: {1}", customer_id, str(e))
            show_alert(32, e)
            return
        # #
        # # fill the tabulator on screen 
        # df = pd.DataFrame(columns = config['model']['table_columns'])
        # #
        # #  get the selected customer info
        # #
        # root = api_customer_details.customer_detail
        # df.loc[0] = [root.id, root.name, np.nan, np.nan, config['model']['record_types']['customer'], \
        #      pd.to_datetime(root.created_time, utc=True), pd.to_datetime(root.edited_time, utc=True)]
        # #
        # off = df.shape[0]
        # #
        # # Now add the Org Units
        # #
        # for i, ou in enumerate(api_org_units.org_units):
        #     df.loc[off+i] = [ou.id, ou.name, ou.parent_id, ou.parent_name, config['model']['record_types']['hierarchy'], \
        #         pd.to_datetime(ou.created_time, utc=True), pd.to_datetime(ou.edited_time, utc=True)]
        # #
        # # Now add the assets as well
        # #
        # off = df.shape[0]
        # for j, a in enumerate(api_assets.assets):
        #     df.loc[off+j] = [a.id, a.name, a.parentId, a.parent_name, config['model']['record_types']['asset'], \
        #         pd.to_datetime(a.created_time, utc=True), pd.to_datetime(a.edited_time, utc=True)]
        # #
        # # Get ALL tags belonging to to all assets of this customer
        # #
        # #
        # # loop trough all assets
        # #
        # for ast in api_assets.assets:
        #     asset_id = ast.id
        #     api_all_tags = AvalonTags()
        #     try:
        #         api_all_tags.Request_tags(api_connection, customer_id, asset_id, session_token.token, config)
        #     except Exception as e:
        #         logger.error("Error trying to get the Tags for customer {0}. Error: {1}", customer_id, str(e))
        #         show_alert(35, e)
        #         return
        #     #
        #     # Now add the tags for selected customer and asset
        #     #
        #     off = df.shape[0]
        #     for j, t in enumerate(api_all_tags.tags):
        #         created_time, edited_time = t.Get_times(api_tags_details)
        #         asset_name = api_assets.Find_name_from_id(t.assetId)
        #         combined_id = t.tagId + "-" + t.assetId # make it unique
        #         df.loc[off+j] = [combined_id, t.name, t.assetId, asset_name, config['model']['record_types']['tag'], \
        #             pd.to_datetime(created_time, utc=True), pd.to_datetime(edited_time, utc=True)]
        # #
        # # Got it! now show it to screen! and the number of rows too
        # #
        # pitems.model_table_widget.value = df
        # pitems.model_total_rows.value = df.shape[0]
        # #
        # # Save into the main pitems object.
        # pitems.model_export_dataframe = df
    return

def select_assets():
#
# Pre-select the customer that was saved on any previous run
# 
    if backfill_connection.customer_name != "":
        pitems.customer_selector.value = backfill_connection.customer_id
#
# Pre fill with saved options
    if backfill_connection.asset_name != "":
        pitems.asset_selector.value = backfill_connection.asset_id
		
# # Pre fill with saved options
#     if len(query_connection.tag_full_info_array) > 0:
#         pitems.tag_selector.value = query_connection.tag_ids
        
    return

# ----------------------------------------------------------------------------- #
# Main Code 
# ----------------------------------------------------------------------------- #

def display_panel(l_logger, c_config, p_config, n_connection, web_port, s_token, stream, event):
    #
    # Get panel configuration
    #
    global config, panel_config, connection, api_connection, token_connection, \
        api_customers, api_org_units, api_assets, api_tags, selection, \
        file_connection, backfill_connection, session_token, logger, \
        tpl
    
    logger = l_logger
    config = c_config
    panel_config = p_config
    connection = n_connection
    api_connection = n_connection.api
    ##query_connection = n_connection.query
    token_connection = n_connection.token
    session_token = s_token
    file_connection = n_connection.file
    backfill_connection = n_connection.backfill
    #
    # Validate the data from connection file
    #
    logger.debug("Validating credentials...")
    cr = Credentials(api_connection.credentials.user_name, api_connection.credentials.password)
    connection_valid = cr.Validate() and Credentials.validateUrl(api_connection.basic_url)
    if (connection_valid == True):
        logger.debug("API and DB credentials are valid.")
    else:
        logger.debug("No valid API credentials were found. Loading with defaults.")
    #
    # Create objects that holds all selections
    #
    selection = CurrentSelection()
    ##wb_selection = CurrentSelection()
    api_customers = AvalonCustomers()
    ##api_customer_details = AvalonCustomerDetails()
    api_tags = AvalonTags()
    api_org_units = AvalonOrgUnits()
    api_assets = AvalonAssets()
    # ----------------------------------------------------------------------------- #
    # Basic Display building components 
    # ----------------------------------------------------------------------------- #
    
    logger.debug("Creating all UI panels....")
    pn.extension()
    pn.extension('terminal')
    tpl = pn.template.VanillaTemplate(title=panel_config['template']['name'] + " - Version: " + config['version'], header_background = panel_config['template']['header_background'])
    #
    # Create the main alert panel component
    # 
    pitems.main_alert = pn.pane.Alert(panel_config["alerts"]["main_alert"]["initial_text"], visible = False, alert_type = panel_config["alerts"]["main_alert"]["default_type"])
    #
    # Create UI Gadgets
    #
    #
    # Widget 1a
    #
    pitems.widget1a_title = pn.pane.Markdown(panel_config['widgetboxes']['1a']['name'])
    pitems.api_url = pn.widgets.TextInput(name=panel_config["labels"]['label2_name'], value=api_connection.basic_url)
    pitems.password = pn.widgets.PasswordInput(name=panel_config["labels"]['label4_name'], value=api_connection.credentials.password)
    pitems.user_name = pn.widgets.TextInput(name=panel_config["labels"]['label3_name'], value=api_connection.credentials.user_name)
    pitems.api_connection_ok_label = pn.pane.Markdown(panel_config["boolean_status"]['1']['name'])
    pitems.api_token_ok_label = pn.pane.Markdown(panel_config["boolean_status"]['2']['name'])
    pitems.api_connection_ok = pn.widgets.BooleanStatus(color=panel_config["boolean_status"]['1']['color'], value = False)
    pitems.api_token_ok = pn.widgets.BooleanStatus(color=panel_config["boolean_status"]['2']['color'], value = False)
    #
    # Widget 1 Buttons
    #
    pitems.api_update_button = pn.widgets.Button(name=panel_config['buttons']['api_update_button']['name'], 
        width=panel_config['buttons']['api_update_button']['size'], button_type=panel_config['buttons']['api_update_button']['type'], disabled=False)
    pitems.api_update_button.on_click(api_update_button_callback)
    pitems.api_test_button = pn.widgets.Button(name=panel_config['buttons']['api_test_button']['name'], 
        width=panel_config['buttons']['api_test_button']['size'], button_type=panel_config['buttons']['api_test_button']['type'], disabled=not connection_valid)
    pitems.api_test_button.on_click(api_test_button_callback)
    #
    # Widget 2a
    #
    pitems.widget2a_title = pn.pane.Markdown(panel_config['widgetboxes']['2a']['name'])
    pitems.customer_selector = pn.widgets.Select(name=panel_config['selectors']['1']['name'], options=[])
    pitems.asset_selector = pn.widgets.Select(name=panel_config['selectors']['2']['name'],  width=panel_config['selectors']['2']['width'], options=[])
    pitems.tag_selector = pn.widgets.MultiSelect(name=panel_config['selectors']['3']['name'], options=[], size=panel_config['selectors']['3']['size'])
    #
    # Widget 2b
    #
    pitems.data_table1 = None
    pitems.widget2b_title = pn.pane.Markdown(panel_config['widgetboxes']['2b']['name'])
    pitems.upload_data_file_button = pn.widgets.Button(name=panel_config['buttons']['upload_data_file_button']['name'], 
        width=panel_config['buttons']['upload_data_file_button']['size'], button_type=panel_config['buttons']['upload_data_file_button']['type'], disabled=not connection_valid)
    pitems.upload_data_file_button.on_click(upload_data_file_button_callback)
    pitems.total_rows = pn.widgets.StaticText(name=panel_config['labels']["label8_name"], value=0)
    pitems.data_table_widget = pn.widgets.Tabulator(pitems.data_table1,layout='fit_data', width=panel_config['tables']['1']['width'], pagination='local', show_index=False, selectable=False, page_size=panel_config['tables']['1']['page_size'], disabled=True)
    #
    # Data File textbox
    #
    pitems.upload_data_file_textbox = pn.widgets.TextInput(name=panel_config["labels"]['label5_name'], value=file_connection.full_name)
    #
    # Widget 3
    #
    pitems.update_table2 = None
    pitems.widget3_title = pn.pane.Markdown(panel_config['widgetboxes']['3']['name'])
    pitems.start_datetime = pn.widgets.DatetimePicker(name=panel_config['date_pickers']['1']['name'], value=datetime.now()-timedelta(hours=panel_config['date_pickers']['1']['back_hours']))
    pitems.total_upload_rows = pn.widgets.StaticText(name=panel_config['labels']["label8_name"], value=0)
    pitems.update_table_widget = pn.widgets.Tabulator(pitems.update_table2,layout='fit_data', width=panel_config['tables']['2']['width'], pagination='local', show_index=False, selectable=False, page_size=panel_config['tables']['2']['page_size'], disabled=True)    
    #
    # Widget 3 Buttons
    #
    pitems.api_create_backfill_file_button = pn.widgets.Button(name=panel_config['buttons']['api_create_backfill_file_button']['name'], 
        width=panel_config['buttons']['api_create_backfill_file_button']['size'], button_type=panel_config['buttons']['api_create_backfill_file_button']['type'], disabled=True)
    pitems.api_create_backfill_file_button.on_click(api_create_backfill_file_callback)
    
    pitems.api_initiate_backfill_button = pn.widgets.Button(name=panel_config['buttons']['api_initiate_backfill_button']['name'], 
        width=panel_config['buttons']['api_initiate_backfill_button']['size'], button_type=panel_config['buttons']['api_initiate_backfill_button']['type'], disabled=True)
    pitems.api_initiate_backfill_button.on_click(api_initiate_backfill_callback)
    # 
    # Create the Tab Object
    #
    tabs = pn.Tabs()
    #
    #
    # Selector controls 
    # -------------- CUSTOMER SELECTOR ---------------------------------------------------
    @pn.depends(customer_id=pitems.customer_selector, watch=True)
    def selfunc(customer_id):
        if customer_id is not None:
            #
            # A customer was selected. Get all assets from that customer
            # Check if we need to refresh the token
            #
            try:
                session_token.Refresh(api_connection, config)
            except Exception as e:
                logger.error("Error trying to refresh the API token")
                show_alert(7, e)
                return
            #
            # Get the customer name as well
            #
            pitems.asset_selector.options = []
            ##pitems.tag_selector.options = []
            #
            # Save the selected customer
            #
            status = selection.GetSelectedCustomer(customer_id, api_customers)
            if (status == False):
                logger.error("Error trying to obtain full customer info from Id:  {0}.", customer_id)
                return
            # #
            # # Get details about the newly selected customer
            # #
            # status = api_customer_details.Request_customer_details(api_connection, customer_id, session_token.token, config)
            # if (status == False):
            #     logger.error("Error trying to obtain full customer detailed info from Id:  {0}.", customer_id)
            #     return
            #
            #  Get org unit hierarchy for this customer
            #
            try:
                api_org_units.Request_org_units(api_connection, customer_id, session_token.token, config)
            except Exception as e:
                logger.error("Error trying to get the Org Units for customer {0}. Error: {1}", customer_id, str(e))
                show_alert(31, e)
                return
            #
            # Let's get the assets list for this customer
            #
            try:
                api_assets.Request_assets(api_connection, customer_id, session_token.token, config)
            except Exception as e:
                logger.error("Error trying to get the Avalon asset list for customer {0}. Error: {1} ", customer_id, str(e))
                show_alert(9, e)
                return
            ###
            ### Get all tags assigned to this customer
            ###
            ##try:
            ##    api_tags_details.Request_tags_details(api_connection, customer_id, session_token.token, config)
            ##except Exception as e:
            ##    logger.error("Error trying to get the Tags for customer {0}. Error: {1}", customer_id, str(e))
            ##    show_alert(35, e)
            ##    return
            ##
            ##  Now get org unit hierarchy for this customer
            ##
            query_hierarchy(customer_id, None)
            #
            # fill the asset selector
            #
            ############pitems.asset_selector.options = api_assets.Get_Asset_names()
            pitems.asset_selector.options = api_assets.Get_Asset_full_names()
        return
    # -------------- ASSET SELECTOR ---------------------------------------------------
    @pn.depends(asset_id=pitems.asset_selector, watch=True)
    def selfunc(asset_id):
        if asset_id is not None:
            # 
            # An asset was selected. Get all tags from that customer
            # Check if we need to refresh the token
            #
            try:
                session_token.Refresh(api_connection, config)
            except Exception as e:
                logger.error("Error trying to refresh the API token")
                show_alert(7, e)
                return
            #
            # Save the selected asset
            #
            status = selection.GetSelectedAsset(asset_id, api_assets)
            if (status == False):
                logger.error("Error trying to obtain full asset info from Id: {0}.", asset_id)
                return
            
            customer_id = selection.selected_customer.id
            #
            # Let's get the tags list for this asset/customer
            #
            try:
                customer_id = selection.selected_customer.id
                api_tags.Request_tags(api_connection, customer_id, asset_id, session_token.token, config)
            except Exception as e:
                logger.error("Error trying to refresh get the Avalon tag list for customer {0}, asset {1}. Error: {2} ".format(customer_id, asset_id, str(e)))
                show_alert(10, e)
                return
            ###
            ### fill the tags selectors
            ###
            ##pitems.tag_selector.options = api_tags.Get_tag_names()
            ####
            ####  Now get org unit hierarchy for this customer
            ####
            query_hierarchy(customer_id, asset_id)
        return

    #############################################################################################
    #
    # TOP COMMON 
    #
    #############################################################################################
    #
    # Main alert is at the top
    #
    tpl.main.append(pitems.main_alert)
    #
    # Configuration Info
    #
    # WIDGET 1 a, 1b ----------------------------------------------------------------------------

    widgetbox_1 = pn.WidgetBox (name=panel_config['widgetboxes']['1']['tab_name'], width=panel_config['widgetboxes']['1']['width'])
    widgetbox_1a = pn.WidgetBox (name=panel_config['widgetboxes']['1a']['tab_name'], width=panel_config['widgetboxes']['1a']['width'])
    widgetbox_1a.append(pitems.widget1a_title)
    widgetbox_1a.append(pitems.api_url)
    widgetbox_1a.append(pn.Row(pn.Column(pitems.user_name), pn.Column(pitems.password), pn.Column(pitems.api_connection_ok_label), pn.Column(pitems.api_connection_ok), pn.Column(pitems.api_token_ok_label), pn.Column(pitems.api_token_ok), pn.Column(pitems.api_test_button)))

    widgetbox_1a.append(pn.Row(pn.Column(pitems.api_update_button)))


    widgetbox_1.append(widgetbox_1a)

    tabs.append(widgetbox_1)
    
    # WIDGET 2 -----------------------------------------------------------------------------------
    widgetbox_2 = pn.WidgetBox (name=panel_config['widgetboxes']['2']['tab_name'], width=panel_config['widgetboxes']['2']['width'], sizing_mode='stretch_height')    

    # WIDGET 2a -----------------------------------------------------------------------------------
    widgetbox_2a = pn.WidgetBox (name=panel_config['widgetboxes']['2a']['tab_name'], width=panel_config['widgetboxes']['2a']['width'])
    widgetbox_2a.append(pitems.widget2a_title)
    widgetbox_2a.append(pn.Row(pn.Column(pitems.customer_selector), pn.Column(pitems.asset_selector)))
    widgetbox_2.append(widgetbox_2a)

    # WIDGET 2b -----------------------------------------------------------------------------------
    widgetbox_2b = pn.WidgetBox (name=panel_config['widgetboxes']['2b']['tab_name'], width=panel_config['widgetboxes']['2b']['width'], height=panel_config['widgetboxes']['2b']['height'])
    widgetbox_2b.append(pitems.widget2b_title)
    widgetbox_2b.append(
        pn.Row(
            pn.Column(pitems.upload_data_file_textbox),
            pn.Column(pitems.upload_data_file_button),
            pn.Column(pitems.total_rows)
        )
    )
    widgetbox_2b.append(pn.Row(pitems.data_table_widget))
    widgetbox_2.append(widgetbox_2b)
    tabs.append(widgetbox_2)
    # WIDGET 3 -----------------------------------------------------------------------------------
    widgetbox_3 = pn.WidgetBox (name=panel_config['widgetboxes']['3']['tab_name'], width=panel_config['widgetboxes']['3']['width'], height=panel_config['widgetboxes']['3']['height'])
    widgetbox_3.append(pitems.widget3_title)
    
    widgetbox_3.append(
        pn.Row(
            pn.Column(
                pn.Column(pitems.start_datetime)
            ),
            pn.Column(
                pn.Column(pitems.api_create_backfill_file_button),
                pn.Column(pitems.api_initiate_backfill_button),
                pn.Column(pitems.total_upload_rows)
            )
        )
    )
    widgetbox_3.append(pn.Row(pitems.update_table_widget))
    tabs.append(widgetbox_3)

    # COMMON WIDGET -----------------------------------------------------------------------------------
    tpl.main.append(tabs)
    ##tpl.modal.append(pn.Row(modal_widgetbox))
    tpl.main.append(pn.Row(pn.Param(stream, sizing_mode="stretch_width", widgets={
        "value": {"widget_type": pn.widgets.TextAreaInput, "width": panel_config["common"]["log1_width"], "height": panel_config['common']['log1_height']}
    }))) 
    #
    # Run any initialization routine 
    #
    init()
    logger.debug("Panel Initialization completed.")
    #
    # Fire the async event loop
    #
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    try:
        tpl.show(title=panel_config['template']['name'], port=web_port)
    except Exception as e:
        logger.error("Exception trying to start Panel thread. Error: " + str(e) + ". Program ABORTED.")
        event.set()
        exit()
    return