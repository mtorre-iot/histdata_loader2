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
    df = pd.read_csv(fullFileName, header=None)
    # 
    # read successful - 1st row are the tag names. 
    #
    tagNames = df.iloc[0]
    #
    # check that the first header is correct
    
    if tagNames[0] != cfg['file']['time_column']:
        raise ConfigFileReadError("First column of file " + fullFileName + " must be " + cfg['file']['time_column'] + " Please check.")
    #
    # Check all tags - avoud duplicates
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
    # Tags checked. Return the dataFrame
    #
    return df