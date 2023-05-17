#
# Mario Torre - 05/16/2023
#
import csv
import os
import shutil

from classes.exception_classes import DirectoryError


def split_upload_csv_file(logger, config):
    #
    # Get big upload file name
    #
    big_file = os.path.join(config['dirs']['upload_dir'], config['dirs']['upload_file'])
    #
    # determine split directory
    #
    split_dir = os.path.join(config['dirs']['upload_dir'], config['dirs']['split_dir'])
    #
    # remove - recreate split directory
    #
    if os.path.exists (split_dir):
        try:
            shutil.rmtree(split_dir)
        except Exception as e:
            raise DirectoryError ('split_upload_csv_file() - Error trying to remove ' + split_dir + ' directory. Error: ' + str(e) + '.')
    
    os.makedirs(split_dir)
    #
    # Read big file
    #
    try:
        bf = open(big_file, 'r')
        reader = csv.reader(bf, delimiter=',')
    except Exception as e:
        raise DirectoryError("split_upload_csv_file() - File: (." + big_file + ") cannot be created.")
    #
    # Start creating split files
    #
    split_file_counter = 0
    split_line_counter = 0
    spltf = None
    for line in reader:
        #
        # if it is the first line of the split file, close previous file and open a new one
        #
        if split_line_counter == 0:
            
            split_file = os.path.join(split_dir, config['dirs']['split_file'].format(split_file_counter))
            try:
                logger.info("split_upload_csv_file() - Creating split file " + str(split_file_counter + 1) + " File Name: " + split_file) 
                spltf = open(split_file, 'w', newline='')
                writer = csv.writer(spltf, delimiter=',')
            except Exception as e:
                raise DirectoryError("split_upload_csv_file() - File: (." + big_file + ") cannot be created.")
        #
        # Store read line into split file
        #
        writer.writerow(line)
        
        split_line_counter += 1
        if split_line_counter == config['file']['split_size']:
            split_file_counter += 1
            split_line_counter = 0
            if spltf != None:
                spltf.close()
    #
    # close last opened files
    #
    spltf.close()
    bf.close()
    return

    

    