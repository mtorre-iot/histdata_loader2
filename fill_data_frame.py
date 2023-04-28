#
# Mario Torre - 04/20/2023
#
import math
import pandas as pd

from classes.exception_classes import ConfigFileReadError

def fill_data_frame(logger, df):
    columns_collection = []
    # # 
    # # Convert 1st row to dataFrame headers
    # # 
    # columns_collection = df.iloc[0]                                 # get the tag names as column headers                              
    # df2 = df.rename(columns_collection, axis='columns')             # rename columns
    # df2 = df2.drop(labels=0, axis=0)                                # delete the 1st row
    #
    # Make sure to sort all rows ascending on time
    #
    time_col = df.columns[0]
    sorted_df = df.sort_values(time_col)
    #sorted_df = sorted_df.reset_index()  
    #
    #  Change from absolute to relative to 1st datatime
    #
    first_datetime = sorted_df[time_col].iloc[0]                # get very first timestamp
    ###sorted_df.iloc[0, sorted_df.columns.get_loc(time_col)] = 0.0    # set first record at 0
    #
    curr_time = first_datetime
    rowNum = 0
    for i in range (sorted_df.shape[0]):
        curr_time = sorted_df[time_col].iloc[i]
        ### if i > 0:
        ###     prev_time = curr_time
        ###     curr_time = pd.to_datetime(sorted_df[time_col].iloc[i])
        ###     diff = (curr_time - first_datetime).total_seconds()
        ###     interv = (curr_time - prev_time).total_seconds()
        ###     if (interv == 0):
        ###         logger.warning("Data Error - time stamp duplication at time: " + str(curr_time) + ". Please check data. Record skipped.")
        ###         continue
        ###     sorted_df.iloc[rowNum, sorted_df.columns.get_loc(time_col)] = diff
        #
        # Check if any of the values is invalid or NaN
        #
        values = sorted_df.iloc[rowNum]
        for i  in range(1, len(values)):
            try:
                float_val = float(values[i])
            except ValueError:
                logger.warning ("fill_data_frame() - time: " + str(curr_time) + " tagname: " + sorted_df.columns[i] + " value is invalid (" + str(values[i]) + ")")

            if (math.isnan(float_val) == True):
                logger.warning ("fill_data_frame() - time: " + str(curr_time) + " tagname: " + sorted_df.columns[i] + " value is NaN or empty.")

        rowNum += 1
    
    return sorted_df