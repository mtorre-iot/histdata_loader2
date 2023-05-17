#
# Mario Torre - 04/20/2023
#
import os
import pandas as pd

from classes.exception_classes import ConfigFileReadError


def histdata_read(logger, cfg, api_tags, fullFileName):
    #
    # Check if file exists
    #
    if os.path.isfile(fullFileName) == False:
        raise Exception("File " + fullFileName + " does not exist. Please check.")
        
    logger.debug("File: " + fullFileName + " exists.")
    #
    # Try to read file it as csv
    #
    logger.debug ("Reading csv file: " + fullFileName)
    df = pd.read_csv(fullFileName, comment="#")
    # 
    # read successful - 1st row are the tag names. 
    #
    tagNames = df.columns
    #
    # check that the first header is correct
    
    if tagNames[0] != cfg['file']['time_column']:
        raise ConfigFileReadError("First column of file " + fullFileName + " must be " + cfg['file']['time_column'] + " Please check.")
    #
    # Check all tags - avoid duplicates
    #
    checked_tags = []
    for i in range (1, len(tagNames)): 
        if (api_tags.FindTagName(tagNames[i]) == None):
            raise ConfigFileReadError("Tag " + tagNames[i] + " not found in tags of this customer / asset. Please Check configuration.")
        try:
            idx = checked_tags.index(tagNames[i])
            raise ConfigFileReadError ("Duplicated tag names in file. Duplicated tagname: " + tagNames[i] + ". Please check data.")
        except ValueError:
            checked_tags.append(tagNames[i])    
    #
    # Tags checked. Now place all data in their correct data types
    #
    # convert time column to datetime
    df[cfg['file']['time_column']] = pd.to_datetime(df[cfg['file']['time_column']])
    # convert all other data to float
    for i in range (1, len(df.columns)):
        try:
            df[df.columns[i]] = df[df.columns[i]].astype(float)
        except Exception as e:
            raise Exception("Invalid number found on column " + df.columns[i] + " Error: " + str(e))
    #
    #  Return the dataFrame
    #
    return df