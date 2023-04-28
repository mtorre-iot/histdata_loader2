#
# Mario Torre - 04/20/2023
#
from datetime import timedelta
import math
import os
import pandas as pd
from lib.miscfuncs import convertLocalDateTimetoUTC, formatDateTimeToISO8601_UTC

def build_upload_file(logger, initial_time, input_df, backfill_connection, config):
    upload_df = pd.DataFrame(columns = config['misc']['backfill_data_cols'])
    # Get customer_id 
    customer_id = backfill_connection.customer_id
    quality = config['misc']['quality']['good']
    #
    # Get the initial time as selected by customer
    #
    date_time_0 = convertLocalDateTimetoUTC(initial_time)
    #
    # Reindex the dataframe
    #
    ##input_df = input_df.reset_index()  # make sure indexes pair with number of rows
    numRows = input_df.shape[0]
    numCols = input_df.shape[1]
    numNewRows = numRows*(numCols-1)
    #
    # Get all column names, they are the tag names!
    #
    tagsArray = backfill_connection.tag_backfill_full_info_array
    #
    # Get the first original timestamp
    #
    time_col = input_df.columns[0]
    first_time = input_df[time_col].iloc[0]
    curr_time = first_time
    rowNum = 0
    for index, row in input_df.iterrows():
        prev_time = curr_time
        curr_time = input_df[time_col].iloc[index]
        diff = (curr_time - first_time).total_seconds()
        interv = (curr_time - prev_time).total_seconds()
        if (interv == 0) and (index > 0):
            logger.warning("Data Error - time stamp duplication at time: " + str(curr_time) + ". Please check data. Record skipped.")
            continue
 
        time = date_time_0 + timedelta(seconds=diff)
        for tag in tagsArray:
            value = row[tag.name]
            try:
                float_val = float(value)
            except ValueError:
                logger.warning ("build_upload_file() - time: " + str(time) + " tagname: " + tag.name + " value is invalid (" + str(value) + "). Record skipped")
                continue

            if (math.isnan(float_val) == True):
                logger.warning ("build_upload_file() - time: " + str(time) + " tagname: " + tag.name + " value is NaN or empty. Record skipped.")
                continue

            timeStampStr = formatDateTimeToISO8601_UTC(time)
            ## print(customer_id + "," + tag.dataSourceId + "," + tag.physicalTagId + "," + str(value) + "," + str(quality) + "," + timeStampStr)
            upload_df.loc[rowNum] = [customer_id, tag.dataSourceId, tag.physicalTagId, value, quality, timeStampStr]
            rowNum += 1
            if (rowNum % 1000 == 0):
                logger.debug("build_upload_file() - processing row: " + str(rowNum) + " - " + str(round(rowNum/numNewRows*100.0,1)) + "%")
    #
    # new dataframe created. Save it into a csv file.
    #
    csvFile = os.path.join(config['dirs']['upload_dir'], config['dirs']['upload_file'])
    upload_df.to_csv(csvFile, index=False, header=False)
    return upload_df