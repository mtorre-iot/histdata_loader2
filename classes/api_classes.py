#
# Mario Torre - 04/20/2023
#
from datetime import datetime as dt
import datetime
from fileinput import close
import json
import requests
from UI.alerts import set_alert_message

from lib.miscfuncs import base64ToString

class AvalonAPIBase(object):
    def __init__(self):
        self.url = None
        self.headers = None
        self.payload = None
        self.headers = None
        self.operation = None
    
    def Build_url(self, prefix, url, suffix):
        url_array = url.split("://")
        self.url = url_array[0] + "://" + prefix + url_array[1] + suffix

class AvalonAPIToken(AvalonAPIBase):
    def __init__(self):
        AvalonAPIBase.__init__(self)
        self.token = None
        self.token_response = None
        self.refresh_token = None
        self.expiration = None
        self.refresh_expiration = None
        self.issue_date = None
    
    def Build_payload(self, payload_format, user_name, password):
        decoded_password = password # base64ToString(password)
        self.payload = payload_format.format(user_name, decoded_password)

    def Build_refresh_payload (self, payload_format, refresh_token):
        self.payload = payload_format.format(refresh_token)

    def Build_headers(self, content_type, headers):
        self.headers = { content_type: headers }

    def Check_token_freshness(self):
        #
        # Check if token has expired
        #
        try:
            time_change = datetime.timedelta(seconds=self.expiration)
            return  (dt.now() < self.issue_date + time_change)
        except Exception as e:
            return False
        
    def Check_refresh_token_freshness(self):    
        #
        # Now check if the refresh token is also expired:
        # 
        try:
            time_change = datetime.timedelta(seconds=self.refresh_expiration)
            return (dt.now() < self.issue_date + time_change)
        except Exception as e:
            return False

    def Request(self):
        self.token_response  = requests.request(self.operation, self.url, headers=self.headers, data=self.payload)
        if self.token_response.ok == True:
            data=json.loads(self.token_response.text)
            self.token=data['access_token']
            self.expiration = data['expires_in']
            self.refresh_expiration = data['refresh_expires_in']
            self.refresh_token = data['refresh_token']
            self.issue_date = dt.now()
        return self.token_response.ok
    
    def Request_token(self, api_connection, config):
        #
        # fill the object   
        #
        self.Build_url(config['api']['token']['url_prefix'], api_connection.basic_url, config['api']['token']['url_suffix'])
        self.Build_payload(config['api']['token']['payload_format'],api_connection.credentials.user_name, api_connection.credentials.password)
        self.Build_headers(config['api']['token']['content_type'], config['api']['token']['headers'])
        self.operation = config['api']['token']['operation']
        status = self.Request()
        if status == False:
            raise Exception("Token Request failed. Message: HTTP %i - %s, Message %s" % (self.token_response.status_code, self.token_response.reason, self.token_response.text))

    def Refresh_token(self, api_connection, config):
        self.Build_url(config['api']['token']['url_prefix'], api_connection.basic_url, config['api']['token']['url_suffix'])
        self.Build_refresh_payload (config['api']['token']['refresh_payload_format'], self.refresh_token)
        self.Build_headers(config['api']['token']['refresh_content_type'], config['api']['token']['refresh_headers'])
        status = self.Request()
        if status == False:
            raise Exception("Token Refresh Request failed. Message: HTTP %i - %s, Message %s" % (self.token_response.status_code, self.token_response.reason, self.token_response.text))
        return

    def Refresh(self, api_connection, config):
        #
        # Check if we need to refresh the token
        #
        if (self.Check_token_freshness() == False):
            #
            # maybe the refresh token is also expired...
            #
            if (self.Check_refresh_token_freshness() == False):
                #
                # New token must be requested
                #
                self.Request_token(api_connection, config)
            else: 
                #
                # Request a refresh token
                #
                self.Refresh_token(api_connection, config)
        return

class AvalonCustomers(AvalonAPIBase):
    def __init__(self):
        AvalonAPIBase.__init__(self)
        self.data_response = None
        self.customers = []

    def Build_customer_headers(self, content_type, headers, authorization_type, authorization, token):
        self.headers = { content_type: headers, authorization_type:  authorization.format(token) }

    def Request(self):
            self.data_response  = requests.request(self.operation, self.url, headers=self.headers)
            if self.data_response.ok == True:
                data=json.loads(self.data_response.text)
                for d in data:
                    customer = Customer()
                    customer.from_json(d)
                    self.customers.append(customer)    
            return self.data_response.ok

    def Request_customers(self, api_connection, token, config):
        #
        # empty the asset array
        # 
        self.customers = []
        #
        # fill the object   
        #
        self.Build_url(config['api']['customer']['url_prefix'], api_connection.basic_url, config['api']['customer']['url_suffix'])
        self.Build_customer_headers(config['api']['customer']['content_type'], config['api']['customer']['headers'], config['api']['customer']['authorization_type'], \
            config['api']['customer']['authorization'], token)
        self.operation = config['api']['customer']['operation']
        status = self.Request()
        if status == False:
            raise Exception("Customer Request failed. Message: HTTP %i - %s, Message %s" % (self.data_response.status_code, self.data_response.reason, self.data_response.text))

    def Get_Customer_names(self):
        rtn = {}
        for c in self.customers:
            rtn[c.name]= c.id 
        return rtn

class AvalonCustomerDetails(AvalonAPIBase):
    def __init__(self):
        AvalonAPIBase.__init__(self)
        self.data_response = None
        self.customer_detail = None

    def Build_detail_customer_headers(self, content_type, headers, authorization_type, authorization, token):
        self.headers = { content_type: headers, authorization_type:  authorization.format(token) }

    def Request(self):
            self.data_response  = requests.request(self.operation, self.url, headers=self.headers)
            if self.data_response.ok == True:
                data=json.loads(self.data_response.text)
                customer_detail = CustomerDetail()
                customer_detail.from_json(data)
                self.customer_detail = customer_detail
            return self.data_response.ok

    def Request_customer_details(self, api_connection, customer_id, token, config):
        #
        # fill the object   
        #
        self.Build_url(config['api']['customer']['url_prefix'], api_connection.basic_url, config['api']['customer']['url_suffix_detailed'].format(customer_id))
        self.Build_detail_customer_headers(config['api']['customer']['content_type'], config['api']['customer']['headers'], config['api']['customer']['authorization_type'], \
            config['api']['customer']['authorization'], token)
        self.operation = config['api']['customer']['operation']
        status = self.Request()
        if status == False:
            raise Exception("Customer Request failed. Message: HTTP %i - %s, Message %s" % (self.data_response.status_code, self.data_response.reason, self.data_response.text))

class AvalonOrgUnits(AvalonAPIBase):
    def __init__(self):
        AvalonAPIBase.__init__(self)
        self.data_response = None
        self.customer_id = None
        self.customer_name = None
        self.org_units = []

    def Build_org_unit_headers(self, content_type, headers, authorization_type, authorization, token):
        self.headers = { content_type: headers, authorization_type:  authorization.format(token) }


    def Request(self, customer_id):
        self.data_response  = requests.request(self.operation, self.url, headers=self.headers)
        if self.data_response.ok == True:
            data=json.loads(self.data_response.text)
            for d in data:
                org_unit = OrgUnit()
                org_unit.from_json(d, customer_id)
                self.org_units.append(org_unit)    
        return self.data_response.ok

    def Request_org_units(self, api_connection, customer_id, token, config):
            #
            # empty the asset array
            # 
            self.org_units = []
            #
            # fill the object   
            #
            self.Build_url(config['api']['org-unit']['url_prefix'], api_connection.basic_url, config['api']['org-unit']['url_suffix'].format(customer_id))
            self.Build_org_unit_headers(config['api']['org-unit']['content_type'], config['api']['org-unit']['headers'], config['api']['org-unit']['authorization_type'], \
                config['api']['org-unit']['authorization'], token)
            self.operation = config['api']['org-unit']['operation']
            status = self.Request(customer_id)
            if status == False:
                raise Exception("OrgUnit Request failed. Message: HTTP %i - %s, Message %s" % (self.data_response.status_code, self.data_response.reason, self.data_response.text))

    def Fill_parents_name(self, api_customers):
        for c in self.org_units:
            if c.parent_id == c.customer_id:
                for x in api_customers.customers:
                    if x.id == c.customer_id:
                        c.parent_name = x.name
                        break
            else:
                for d in self.org_units:
                    if c.parent_id == d.id:
                        c.parent_name = d.name
                        break
        return

def Set_Parents_names(self, api_connection, customer_name, customer_id):
    for c in self.org_units:
        if c.parent_id == c.customer_id:
            c.parent_name = customer_name
            break
        else:
            for d in self.org_units:
                if c.parent_id == d.id:
                    c.parent_name = d.name
                    break
    return

class AvalonAssets(AvalonAPIBase):
    def __init__(self):
        AvalonAPIBase.__init__(self)
        self.data_response = None
        self.assets = []

    def Build_asset_headers(self, content_type, headers, authorization_type, authorization, token):
        self.headers = { content_type: headers, authorization_type:  authorization.format(token) }


    def Request(self):
        self.data_response  = requests.request(self.operation, self.url, headers=self.headers)
        if self.data_response.ok == True:
            data=json.loads(self.data_response.text)
            for d in data:
                asset = Asset()
                asset.from_json(d)
                self.assets.append(asset)    
        return self.data_response.ok

    def Request_assets(self, api_connection, customer_id, token, config):
            #
            # empty the asset array
            # 
            self.assets = []
            #
            # fill the object   
            #
            self.Build_url(config['api']['asset']['url_prefix'], api_connection.basic_url, config['api']['asset']['url_suffix'].format(customer_id))
            self.Build_asset_headers(config['api']['asset']['content_type'], config['api']['asset']['headers'], config['api']['asset']['authorization_type'], \
                config['api']['asset']['authorization'], token)
            self.operation = config['api']['asset']['operation']
            status = self.Request()
            if status == False:
                raise Exception("Asset Request failed. Message: HTTP %i - %s, Message %s" % (self.data_response.status_code, self.data_response.reason, self.data_response.text))

    def Get_Asset_names(self):
        rtn = {}
        for c in self.assets:
            rtn[c.name]= c.id 
        return rtn
    
    def Get_Asset_full_names(self):
        rtn = {}
        for c in self.assets:
            rtn[c.fullTreeName]= c.id 
        return rtn

    def Find_name_from_id(self, asset_id):
        for c in self.assets:
            if c.id == asset_id:
                return c.name
        return None

    def Find_assets(self, api_org_units):
        new_items = []
        for a in self.assets:
            # check if belongs to one of the org_units:
            for ou in api_org_units.org_units:
                if a.parentId == ou.id:
                    a.parent_name = ou.name
                    break
        return

    def Find_full_tree_name(self, customer_id, api_org_units):
        for a in self.assets:   
            pid = a.parentId
            rtn = ""
            while True:
                for ou in api_org_units.org_units:
                    if pid == ou.id:
                        rtn = " / " + ou.name + rtn
                        break
                if (pid == customer_id):
                    break
                pid = ou.parent_id
            a.fullTreeName = rtn + " / " + a.name
        return

class AvalonTags(AvalonAPIBase):
    def __init__(self):
        AvalonAPIBase.__init__(self)
        self.data_response = None
        self.tags = []

    def Build_tag_headers(self, content_type, headers, authorization_type, authorization, token):
        self.headers = { content_type: headers, authorization_type:  authorization.format(token) }


    def Request(self, asset_id, filters):
        self.data_response  = requests.request(self.operation, self.url, headers=self.headers)
        if self.data_response.ok == True:
            data=json.loads(self.data_response.text)
            for d in data:
                tag = Tag()
                tag.from_json(d, asset_id)
                status = tag.filter(filters)
                if status == True:
                    self.tags.append(tag)    
        return self.data_response.ok

    def Request_tags(self, api_connection, customer_id, asset_id, token, config):
            #
            # empty the tags array
            # 
            self.tags = []
            #
            # fill the object   
            #
            self.Build_url(config['api']['tag']['url_prefix'], api_connection.basic_url, config['api']['tag']['url_suffix'].format(customer_id, asset_id))
            self.Build_tag_headers(config['api']['tag']['content_type'], config['api']['tag']['headers'], config['api']['tag']['authorization_type'], \
                config['api']['tag']['authorization'], token)
            self.operation = config['api']['tag']['operation']
            status = self.Request(asset_id, config['api']['tag']['filters'])
            if status == False:
                raise Exception("Tags Request failed. Message: HTTP %i - %s, Message %s" % (self.data_response.status_code, self.data_response.reason, self.data_response.text))

    def Get_tag_names(self):
        rtn = {}
        for c in self.tags:
            rtn[c.name]= c.tagId 
        return rtn

    def Get_Tag_names_manual(self, is_manual):
        rtn = {}
        for c in self.tags:
            if c.resolvedTag.manual == is_manual:
                rtn[c.name]= c.tagId 
        return rtn

    def Get_tag_name_from_Id(self, tag_id):
        for c in self.tags:
            if c.tagId == tag_id:
                return c.name
        return None

    def getEngUnitFromTagId(self, api_eng_units, tagId):
        for tag in self.tags:
            if tag.tagId == tagId:
                eng_unit_cat_id = tag.resolvedTag.engineeringUnitCategoryId
                eng_unit_id = tag.resolvedTag.incomingEngineeringUnitId
                return EngUnitGroup.get_eng_unit_from_id (api_eng_units.eng_units_groups, eng_unit_cat_id, eng_unit_id)
        return None

    def FindTagName(self, tagName):
        for tag in self.tags:
            if tag.name == tagName:
                return tag
        return None

class AvalonTagsDetails(AvalonAPIBase):
    def __init__(self):
        AvalonAPIBase.__init__(self)
        self.data_response = None
        self.tags_details = []

    def Build_tag_headers(self, content_type, headers, authorization_type, authorization, token):
        self.headers = { content_type: headers, authorization_type:  authorization.format(token) }

    def Request(self):
        self.data_response  = requests.request(self.operation, self.url, headers=self.headers)
        if self.data_response.ok == True:
            data=json.loads(self.data_response.text)
            for d in data:
                tagd = TagDetail()
                tagd.from_json(d)
                self.tags_details.append(tagd)    
        return self.data_response.ok

    def Request_tags_details(self, api_connection, customer_id, token, config):
            #
            # empty the tags array
            # 
            self.tags_details = []
            #
            # fill the object   
            #
            self.Build_url(config['api']['tag']['url_prefix'], api_connection.basic_url, config['api']['tag']['url_suffix_all_tags'].format(customer_id))
            self.Build_tag_headers(config['api']['tag']['content_type'], config['api']['tag']['headers'], config['api']['tag']['authorization_type'], \
                config['api']['tag']['authorization'], token)
            self.operation = config['api']['tag']['operation']
            status = self.Request()
            if status == False:
                raise Exception("Tags Request failed. Message: HTTP %i - %s, Message %s" % (self.data_response.status_code, self.data_response.reason, self.data_response.text))

class AvalonValues(AvalonAPIBase):
    def __init__(self):
        AvalonAPIBase.__init__(self)
        self.data_response = None
        self.time_series = None

    def Build_value_payload(self, payload_format, asset_id, tag_ids, sampling_type, slice_count, delta_t, start, end):
        # let's pack the tags
        vbt = []
        for tag_id in tag_ids:
            vt = ValueTag(asset_id,tag_id)
            vbt.append(vt)
        # Pack the time period
        tp = ValueTimePeriod(start, end)
        # pack the sampling definition
        spd = SamplingDefinition(sampling_type, slice_count, delta_t)
        # Put all together
        payload = ValuePayload(vbt, tp, spd)
        # convert it to json and return in payload
        self.payload = json.dumps(payload, cls=ValuePayloadEncoder)

    def Build_value_headers(self, content_type, headers, authorization_type, authorization, token):
        self.headers = { content_type: headers, authorization_type:  authorization.format(token) }

    def Request(self):
        self.data_response  = requests.request(self.operation, self.url, headers=self.headers, data=self.payload)
        if self.data_response.ok == True:
            data=json.loads(self.data_response.text)
            self.time_series = Timeseries()
            self.time_series.from_json(data)
        return self.data_response.ok

    def Request_values(self, api_connection, customer_id, asset_id, tag_ids, sampling_type, slice_count, delta_t, start, end, token, config):
            #
            # empty the values array
            # 
            self.time_series = []
            #
            # fill the object   
            #
            self.Build_url(config['api']['value']['url_prefix'], api_connection.basic_url, config['api']['value']['url_suffix'].format(customer_id, asset_id))
            self.Build_value_headers(config['api']['value']['content_type'], config['api']['value']['headers'], config['api']['value']['authorization_type'], \
                config['api']['value']['authorization'], token)
            self.Build_value_payload (config['api']['value']['payload_format'], asset_id, tag_ids, sampling_type, slice_count, delta_t, start, end)
            self.operation = config['api']['value']['operation']
            status = self.Request()
            if status == False:
                raise Exception("Timeseries values Request failed. Message: HTTP %i - %s, Message %s" % (self.data_response.status_code, self.data_response.reason, self.data_response.text))

class AvalonSetpoint(AvalonAPIBase):
    def __init__(self):
        AvalonAPIBase.__init__(self)
        self.data_response = None
        self.setpoint = None
  
    def Build_setpoint_headers(self, content_type, headers, authorization_type, authorization, token):
        self.headers = { content_type: headers, authorization_type:  authorization.format(token) }

    def Build_setpoint_payload(self, config, asset_id, tag_id, dataType, value):
        # let's correct the new value based on the expected data type
        if dataType == config['api']['tag']['data_types']['float']: 
            val = value
        elif dataType == config['api']['tag']['data_types']['integer']:
            val = int(value)
        elif dataType == config['api']['tag']['data_types']['boolean']:
            val = value != 0
        else:
            raise Exception ("Target of type  " + dataType + " cannot be written. Operation aborted")
        # let's pack the setup target and value
        payload = SetPoint(asset_id, tag_id, str(val))
        # convert it to json and return in payload
        self.payload = json.dumps(payload, cls=SetpointPayloadEncoder)

    def Request(self):
            self.data_response  = requests.request(self.operation, self.url, headers=self.headers, data=self.payload)
            return self.data_response.ok

    def Request_setpoint(self, api_connection, customer_id, asset_id, tag_id, dataType, value, token, config):
        #
        # fill the object   
        #
        self.Build_url(config['api']['setpoint']['url_prefix'], api_connection.basic_url, config['api']['setpoint']['url_suffix'].format(customer_id))
        self.Build_setpoint_headers(config['api']['setpoint']['content_type'], config['api']['setpoint']['headers'], config['api']['setpoint']['authorization_type'], \
            config['api']['setpoint']['authorization'], token)
        self.Build_setpoint_payload (config, asset_id, tag_id, dataType, value)
        self.operation = config['api']['setpoint']['operation']
        status = self.Request()
        if status == False:
            raise Exception("Setpoint Request failed. Message: HTTP %i - %s, Message %s" % (self.data_response.status_code, self.data_response.reason, self.data_response.text))

class SetPoint(object):
    def __init__(self, logical_entity_id, logical_tag_id, value):
        self.logicalEntityId =logical_entity_id
        self.logicalTagId = logical_tag_id
        self.value = value

class SetpointPayloadEncoder(json.JSONEncoder):
        def default(self, o):
            return o.__dict__

class AvalonEngUnits(AvalonAPIBase):
    def __init__(self):
        AvalonAPIBase.__init__(self)
        self.data_response = None
        self.eng_units_groups = []

    def Build_eng_units_headers(self, content_type, headers, authorization_type, authorization, token):
        self.headers = { content_type: headers, authorization_type:  authorization.format(token) }

    def Request(self):
            self.data_response  = requests.request(self.operation, self.url, headers=self.headers)
            if self.data_response.ok == True:
                data=json.loads(self.data_response.text)
                for d in data:
                    engUnitGroup = EngUnitGroup()
                    engUnitGroup.from_json(d)
                    self.eng_units_groups.append(engUnitGroup)
            return self.data_response.ok

    def Request_eng_units(self, api_connection, token, config):
        #
        # fill the object   
        #
        self.Build_url(config['api']['eng-units']['url_prefix'], api_connection.basic_url, config['api']['eng-units']['url_suffix'])
        self.Build_eng_units_headers(config['api']['eng-units']['content_type'], config['api']['eng-units']['headers'], config['api']['eng-units']['authorization_type'], \
            config['api']['eng-units']['authorization'], token)
        self.operation = config['api']['eng-units']['operation']
        status = self.Request()
        if status == False:
            raise Exception("Eng Units Request failed. Message: HTTP %i - %s, Message %s" % (self.data_response.status_code, self.data_response.reason, self.data_response.text))

class AvalonEvents(AvalonAPIBase):
    def __init__(self):
        AvalonAPIBase.__init__(self)
        self.data_response = None
        self.events = []

    def Build_event_url (self, prefix, url, suffix, filter_options, customer_id, asset_id, start_time, end_time, bits):
        url_array = url.split("://")
        self.url = url_array[0] + "://" + prefix + url_array[1] + suffix.format(customer_id, asset_id, start_time, end_time)
        for i, f in enumerate(bits):
            if f == None:
                continue
            self.url = self.url + filter_options[i].format(f)

    def Build_event_headers(self, content_type, headers, authorization_type, authorization, token):
        self.headers = { content_type: headers, authorization_type:  authorization.format(token) }

    def Request(self):
            self.data_response  = requests.request(self.operation, self.url, headers=self.headers)
            if self.data_response.ok == True:
                data=json.loads(self.data_response.text).get('results')
                for d in data:
                    event = Event()
                    event.from_json(d)
                    self.events.append(event)
            return self.data_response.ok


    def Request_events(self, api_connection, customer_id, asset_id, start_time, end_time, is_active, is_suppressed, is_in_maintenance, is_shelved, token, config):
        #
        # empty the events array
        # 
        self.events = []
        #
        # fill the object   
        #
        self.Build_event_url(config['api']['event']['url_prefix'], api_connection.basic_url, config['api']['event']['url_suffix'], config['api']['event']['filter_options'], customer_id, asset_id, start_time, end_time, \
            [is_active, is_suppressed, is_in_maintenance, is_shelved])
            
        self.Build_event_headers(config['api']['event']['content_type'], config['api']['event']['headers'], config['api']['event']['authorization_type'], \
            config['api']['event']['authorization'], token)
        self.operation = config['api']['event']['operation']
        status = self.Request()
        if status == False:
            raise Exception("Eng Units Request failed. Message: HTTP %i - %s, Message %s" % (self.data_response.status_code, self.data_response.reason, self.data_response.text))

class AvalonBackFill(AvalonAPIBase):
    def __init__(self):
        AvalonAPIBase.__init__(self)
        self.files = None

    def Build_backfill_headers(self, content_type, headers, authorization_type, authorization, token):
        #self.headers = { content_type: headers, authorization_type:  authorization.format(token) }
        self.headers = { authorization_type:  authorization.format(token) }

    def Build_backfill_files(self, fullFileName):
        
        fh = open(fullFileName, 'rb')
        self.files = {
            'incfile': fh
        }
        return fh

    def Request(self):
        self.data_response  = requests.request(self.operation, self.url, headers=self.headers, files=self.files)
        return self.data_response.ok

    def Request_backfill(self, api_connection, fullFileName, token, config):
            #
            # fill the object   
            #
            self.Build_url(config['api']['backfill']['url_prefix'], api_connection.basic_url, config['api']['backfill']['url_suffix'])
            self.Build_backfill_headers(config['api']['backfill']['content_type'], config['api']['backfill']['headers'], config['api']['backfill']['authorization_type'], \
                config['api']['backfill']['authorization'], token)
            fh = self.Build_backfill_files(fullFileName)
            self.operation = config['api']['backfill']['operation']
            status = self.Request()
            fh.close()
            if status == False:
                raise Exception("Asset Request failed. Message: HTTP %i - %s, Message %s" % (self.data_response.status_code, self.data_response.reason, self.data_response.text))

class EngUnitGroup(object):
    def __init__(self):
        self.id = None
        self.name = None
        self.units = None
    
    def from_json(self, json):
        self.id = json.get('id')
        self.name = json.get('name')
        self.units = []
        for u in json.get('units'):
            unit = EngUnit()
            unit.get_units(u)
            self.units.append(unit)
    
    @staticmethod
    def get_eng_unit_from_id (eng_unit_collection, eng_unit_cat_id, eng_unit_id):
        for unit_cat in eng_unit_collection:
            if unit_cat.id == eng_unit_cat_id:
                for unit in unit_cat.units:
                    if unit.id == eng_unit_id:
                        return unit
        return EngUnit.DefaultUnit()

class EngUnit(object):
    def __init__(self):
        self.id = None
        self.name = None
        self.conversionFactor = None
        self.conversionOffset = None
        self.symbol = None
        self.isBaseUnit = None
    
    @staticmethod
    def DefaultUnit():
        rtn = EngUnit()
        rtn.id = 0
        rtn.name= "No Units"
        rtn.conversionFactor = 1.0
        rtn.conversionOffset = 0.0
        rtn.symbol = "-"
        rtn.isBaseUnit = False
        return rtn


    def get_units(self, json):
        self.id = json.get('id')
        self.name = json.get('name')
        self.conversionFactor = json.get('conversionFactor')
        self.conversionOffset = json.get('conversionOffset')
        self.symbol = json.get('symbol')
        self.isBaseUnit = json.get('isBaseunit')        
        
class CurrentSelection(object):
    def __init__(self):
        self.selected_customer = None
        self.selected_asset = None
        self.selected_tags = []

    def GetSelectedCustomer(self, customer_id, api_customers):
        for cs in api_customers.customers:
            if (cs.id == customer_id):
                self.selected_customer = cs
                return True
        return False

    def GetSelectedAsset(self, asset_id, api_assets):
        for cs in api_assets.assets:
            if (cs.id == asset_id):
                self.selected_asset = cs
                return True
        return False

    def GetSelectedTags(self, tag_ids, api_tags):
        count = len(tag_ids)
        self.selected_tags = []
        for ti in tag_ids:
            if count == 0:
                break
            for at in api_tags.tags:
                if (ti == at.tagId):
                    self.selected_tags.append(at)
                    count -= 1
                    break
        return (count == 0)

class Customer(object):
    def __init__(self):
        self.id = None
        self.name = None
        self.dbName = None


    def from_json(self, json):
        self.id = json.get('id')
        self.name = json.get('name')
        self.dbName = json.get('dbName')

class CustomerDetail(Customer):
    def __init__(self):
        Customer.__init__(self)
        self.created_time = None
        self.edited_time = None

    def from_json(self, json):
        self.id = json.get('id')
        self.name = json.get('name')
        self.dbName = json.get('dbName')
        self.created_time = json.get('createdTime')
        self.edited_time = json.get('editedTime')

class OrgUnit(object):
    def __init__(self, id=None, name=None, parent_id=None, parent_name=None, customer_id=None, created_time=None, edited_time=None):
        self.id = id
        self.name = name
        self.parent_id = parent_id
        self.parent_name = parent_name
        self.customer_id = customer_id
        self.created_time = created_time
        self.edited_time = edited_time

    def from_json(self, json, customer_id):
        self.id = json.get('id')
        self.parent_id = json.get('parentId')
        self.name = json.get('name')
        self.customer_id = customer_id
        self.parent_name = ""
        self.created_time = json.get('createdTime')
        self.edited_time = json.get('editedTime')
        return

class Asset (object):
    def __init__(self):
        self.id = None
        self.parentId = None
        self.name = None
        self.parent_name = None
        self.fullTreeName = None
        self.assetTypeId = None
        self.assetTypeName = None
        self.created_time = None
        self.edited_time = None

    def from_json(self, json):
        self.id = json.get('id')
        self.parentId = json.get('parentId')
        self.parent_name = ""
        self.fullTreeName = ""
        self.name =json.get('name')
        self.assetTypeId = json.get('assetTypeId')
        self.assetTypeName = json.get('assetTypeName')
        self.created_time = json.get('createdTime')
        self.edited_time = json.get('editedTime')

class Tag (object):
    def __init__(self): #, assetId, tagId, engineeringUnitCategoryId, name, sourceObjectId, sourceObjectName, sourceObjectType, resolvedTag):
        self.assetId = None
        self.tagId = None
        self.engineeringUnitCategoryId = None
        self.name = None
        self.asourceObjectId = None
        self.sourceObjectName = None
        self.sourceObjectType = None
        self.resolvedTag = None

    def from_json(self, json, asset_id):
        self.assetId = asset_id
        self.tagId = json.get('id')
        self.engineeringUnitCategoryId = json.get('engineeringUnitCategoryId')
        self.name = json.get('name')
        self.sourceObjectId = json.get('sourceObjectId')
        self.sourceObjectName = json.get('sourceObjectName')
        self.sourceObjectType = json.get('sourceObjectType')
        self.resolvedTag = ResolvedTag.get_resolved_tag(json)
        return
    
    def filter(self, filters):
        if self.resolvedTag is None:
            return False
        for f in filters:
            if (self.resolvedTag.dataType == f):
                return False
        return True

    def CreateBodyTag(self):
        return json.dumps(self)

    def Get_times(self, api_tags_details):
        for td in api_tags_details.tags_details:
            if self.tagId == td.tag_id:
                return td.created_time, td.edited_time
        return None, None

    @staticmethod
    def getEngUnitFromTagId(tag_info_array, tag_id, config):
        for tag_info in tag_info_array:
            if tag_info.tag_id == tag_id:
                return tag_info.unit    
        return config['misc']['default_unit']

class TagDetail (object):
    def __init__(self): #, assetId, tagId, engineeringUnitCategoryId, name, sourceObjectId, sourceObjectName, sourceObjectType, resolvedTag):
        self.tag_id = None
        self.name = None
        self.created_time = None
        self.edited_time = None

    def from_json(self, json):
        self.tag_id = json.get('id')
        self.name = json.get('name')
        self.created_time = json.get('createdTime')
        self.edited_time = json.get('editedTime')
        return

class  TagBackfillFullInfo(object):
    def __init__(self, name, tag_id, data_source_id, physical_tag_id):
        self.name = name
        self.tagId = tag_id
        self.dataSourceId = data_source_id
        self.physicalTagId = physical_tag_id

class TagFullInfo (object):
    def __init__(self, name, unit, tag_id):
        self.name = name
        self.unit = unit
        self.tag_id = tag_id

class ResolvedTag(object):
    def __init__ (self, dataSourceId, logicalTagId, physicalTagId, engineeringUnitCategoryId, incomingEngineeringUnitId, \
        enumId, dataType, mappingId, logicalTagName, physicalTagName, min, max, writable, manual):
        
        self.dataSourceId = dataSourceId
        self.logicalTagId = logicalTagId
        self.physicalTagId = physicalTagId
        self.engineeringUnitCategoryId = engineeringUnitCategoryId
        self.incomingEngineeringUnitId = incomingEngineeringUnitId
        self.enumId = enumId
        self.dataType = dataType
        self.mappingId = mappingId
        self.logicalTagName = logicalTagName
        self.physicalTagName = physicalTagName
        self.min = min
        self.max = max
        self.writable = writable
        self.manual = manual

    @staticmethod
    def get_resolved_tag(json):
        st = json.get('resolvedTag')
        if st is None:
            return None
        return ResolvedTag (st.get('dataSourceId'), st.get('logicalTagId'), st.get('physicalTagId'), st.get('engineeringUnitCategoryId'), \
            st.get('incomingEngineeringUnitId'), st.get('enumId'), st.get('dataType'), st.get('mappingId'), st.get('logicalTagName'), \
                st.get('physicalTagName'), st.get('min'), st.get('max'), st.get('writable'), st.get('manual'))

class ValuePayload(object):
    def __init__(self, tags, timePeriod, samplingDefinition):
        self.tags = tags
        self.timePeriod = timePeriod
        self.samplingDefinition = samplingDefinition

class ValuePayloadEncoder(json.JSONEncoder):
        def default(self, o):
            return o.__dict__

class ValueBodyTags(object):
    def __init__ (self):
        self.tags = []

class ValueTag(object):
    def __init__ (self, logicalEntityId, logicalTagId):
        self.logicalEntityId = logicalEntityId
        self.logicalTagId = logicalTagId

class ValueTimePeriod(object):
    def __init__ (self, start, end):
        self.start = start
        self.end = end

    @staticmethod
    def get_time_period(json):
        tp = json.get('timePeriod')
        return ValueTimePeriod(tp.get('start'), tp.get('end'))

class SamplingDefinition(object):
    def __init__ (self, sampling_type, slice_count, delta_t):
        self.samplingType = sampling_type
        self.sliceCount =slice_count
        self.deltaT = delta_t

class Timeseries(object):
    def __init__(self): #, timeseriesResults, stats, timePeriod):
        self.timeseriesResults = None
        self.stats = None
        self.timePeriod = None

    def from_json(self, json):
        tsr_array = json.get('timeseriesResults')
        tsr_object = []
        for tr in tsr_array:
            stats = TimeseriesResults.get_cass_stats(tr)
            values =  TimeseriesResults.get_values(tr)
            engineeringUnit = tr.get('engineeringUnit')
            logicalEntityId = tr.get('logicalEntityId')
            logicalTagId = tr.get('logicalTagId')
            name = tr.get('name')
            dataType = tr.get('dataType')
            tsr_object.append(TimeseriesResults(engineeringUnit, logicalEntityId, logicalTagId, name, stats, dataType, values))
        self.timeseriesResults = tsr_object
        self.stats = TimeseriesGeneralStats.get_general_stats(json)
        self.timePeriod = ValueTimePeriod.get_time_period(json)
        return

class TimeseriesResults (object):
    def __init__ (self, engineeringUnit, logicalEntityId, logicalTagId, name, stats, dataType, values):
        self.engineeringUnit = engineeringUnit
        self.logicalEntityId = logicalEntityId
        self.logicalTagId = logicalTagId
        self.name = name
        self.stats = stats
        self.dataType = dataType
        self.values = values

    @staticmethod
    def get_cass_stats(json):
        st = json['stats']
        return TimeseriesCassandraStats (st.get('cassandraQueryTimeMs'), st.get('cassandraReadTimeMs'), st.get('queryCount'), st.get('thinningAlg'), st.get('totalRecordsRead'), st.get('totalThinnedRecords'), st.get('source'))
        
    @staticmethod
    def get_values(json):
        rtn = []
        values_array = json['values']
        for v in values_array:
            val = TimeseriesValues(v.get('q'), v.get('t'), v.get('v'))
            rtn.append(val)
        return rtn

class TimeseriesValues(object):
    def __init__ (self, q, t ,v):
        self.q = q
        self.t = t
        self.v = v

class TimeseriesMappingHistory(object):
    def __init__ (self, startTime, endTime, dataSourceId, physicalTagId, engineeringUnitCategoryId, enumId, dataType):
        self.startTime = startTime
        self.endTime = endTime
        self.dataSourceId = dataSourceId
        self.physicalTagId = physicalTagId
        self.engineeringUnitCategoryId = engineeringUnitCategoryId
        self.enumId = enumId
        self.dataType = dataType

class TimeseriesCassandraStats (object):
    def __init__ (self, cassandraQueryTimeMs, cassandraReadTimeMs, queryCount, thinningAlg, totalRecordsRead, totalThinnedRecords, source):
        self.cassandraQueryTimeMs = cassandraQueryTimeMs
        self.cassandraReadTimeMs = cassandraReadTimeMs
        self.queryCount = queryCount
        self.thinningAlg = thinningAlg
        self.totalRecordsRead = totalRecordsRead
        self.totalThinnedRecords = totalThinnedRecords
        self.source = source

class TimeseriesGeneralStats (object):
    def __init__ (self, msTagTime, localRead, totalTime):
        self.msTagTime = msTagTime
        self.localRead = localRead
        self.totalTime = totalTime
    
    @staticmethod
    def get_general_stats(json):
        st = json.get('stats')
        return TimeseriesGeneralStats (st.get('msTagTime'), st.get('localRead'), st.get('totalTime'))

class Event(object):
    def __init__ (self):
        self.association_id = None
        self.customer_id = None 
        self.entity_id = None
        self.event_id = None
        self.event_name = None
        self.event_type = None
        self.sub_type1 = None
        self.event_class = None
        self.event_category = None
        self.is_active = None
        self.active_timestamp = None
        self.inactive_timestamp = None
        self.is_suppressed = None
        self.is_acked = None
        self.ack_timestamp = None
        self.is_in_maintenance = None
        self.is_disabled = None
        self.is_shelved = None
        self.start_time = None
        self.end_time = None
        self.severity = None
        self.priority = None
        self.change_log = []
        self.last_modified_by = None
        self.last_modified_time = None
        self.metadata = None
        self.duration_ms = None
        self.keyspace = None

    def from_json(self, json):
        self.association_id = json.get('associationId')
        self.customer_id = json.get('customerId')
        self.entity_id = json.get('entityId')
        self.event_id = json.get('eventId')
        self.event_name = json.get('eventName')
        self.event_type = json.get('eventType')
        self.sub_type1 = json.get('subType1')
        self.event_class = json.get('eventClass')
        self.event_category = json.get('eventCategory')
        self.is_active = json.get('isActive')
        self.active_timestamp = json.get('activeTimestamp')
        self.inactive_timestamp = json.get('inactiveTimestamp')
        self.is_suppressed = json.get('isSuppressed')
        self.is_acked = json.get('isAcked')
        self.ack_timestamp = json.get('ackTimestamp')
        self.is_in_maintenance = json.get('isInMaintenance')
        self.is_disabled = json.get('isDisabled')
        self.is_shelved = json.get('isShelved')
        self.start_time = json.get('startTime')
        self.end_time = json.get('endTime')
        self.severity = json.get('severity')
        self.priority = json.get('priority')
        self.change_log = EventChangeLog.Get_all_change_logs(json.get('changeLog'))
        self.last_modified_by = json.get('lastModifiedBy')
        self.last_modified_time = json.get('lastModifiedTime')
        self.metadata = EventMetadata.Get_metadata(json.get('metadata'))
        self.duration_ms = json.get('durationMs')
        self.keyspace = json.get('keyspace')

class EventChangeLog(object):
    def __init__(self, state_transition, event_timestamp, modified_time, created_by):
        self.state_transition = state_transition
        self.event_timestamp = event_timestamp
        self.modified_time = modified_time
        self.created_by = created_by

    def from_json(self, json):
        self.state_transition = json.get('stateTransition')
        self.event_timestamp = json.get('eventTimestamp')
        self.modified_time = json.get('modifiedTime')
        self.created_by = json.get('createdBy')
    
    @staticmethod
    def Get_all_change_logs(array):
        rtn = []
        for item in array:
            change_log = EventChangeLog(item.get('stateTransition'), item.get('eventTimestamp'), item.get('modifiedTime'), item.get('createdBy'))
            rtn.append(change_log)
        return rtn


class EventMetadata(object):
    def __init__(self, active_count, comparison, incoming_tag_id, value):
        self.active_count = active_count
        self.comparison = comparison
        self.incoming_tag_id = incoming_tag_id
        self.value = value

    @staticmethod
    def Get_metadata(json):
            return EventMetadata(json.get('activeCount'), json.get('comparison'), json.get('incomingTagId'), json.get('value'))
    