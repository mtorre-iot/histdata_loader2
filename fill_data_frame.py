#
# Mario Torre - 04/20/2023
#
import pandas as pd

from classes.exception_classes import ConfigFileReadError

def fill_data_frame(pitems, df):
    columns_collection = []
    # MT
    # Convert 1st row to dataFrame headers
    # 
    columns_collection = df.iloc[0]                                 # get the tag names as column headers                              
    df2 = df.rename(columns_collection, axis='columns')             # rename columns
    df2 = df2.drop(labels=0, axis=0)                                # delete the 1st row
    #
    # Make sure to sort all rows ascending on time
    #
    time_col = df2.columns[0]
    sorted_df = df2.sort_values(df2.columns[0])
    #
    #  Change from absolute to relative to 1st datatime
    #
    first_datetime_str = sorted_df[time_col].iloc[0]                # get very first timestamp
    first_datetime = pd.to_datetime(first_datetime_str)             # convert it ti datetime
    sorted_df.iloc[0, sorted_df.columns.get_loc(time_col)] = 0.0    # set first record at 0
    #
    curr_time = first_datetime
    for i in range (1, sorted_df.shape[0]):
        prev_time = curr_time
        curr_time = pd.to_datetime(sorted_df[time_col].iloc[i])

        diff = (curr_time - first_datetime).total_seconds()
        interv = (curr_time - prev_time).total_seconds()
        if (interv == 0):
            raise ConfigFileReadError("Data Error - time stamp duplication at row " + str(i+1) + ". Please check data.")
        sorted_df.iloc[i, sorted_df.columns.get_loc(time_col)] = diff
    #
    # try to show it on screen
    #
    pitems.data_table_widget.value = sorted_df

    return