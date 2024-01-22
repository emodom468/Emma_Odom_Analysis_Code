#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  4 16:21:17 2023

@author: emmaodom

#rewritten version of batch_concat imageJ macro
#applies TSeries concat or TZseries concat based on metadata about imaging session
    #hence it requires that you have xml metadata file accessible in that folder
#updated to search through subdirectories.
#updated to handle ZSeries, same function as TSeries but seperate to allow for easy selective manipulation in future 
#implemented conditions to select only indiviudal ome.tif files before manipulating (concat + delete)
#I added log lines to record the directory processed, the file saved, and the files deleted. 
"""

import os
import glob
import time
import tifffile
import logging
import xml.etree.ElementTree as ET 

from src import helper_functions as hf

def process_dir(input_dir):
    '''
    input_dir should be a parent directory with a subdirectory for each imaging session 
    ie there is one level of nesting from input_dir to imaging session folder
    the code checks the sequence type and only runs process_folder() if the seq type is TSeries 
    
    it will need to be expanded to handle TZ Series, but I need to look
    into the ordering and naming of files to do this
    '''
    # Set up logging for each directory
    logfile = os.path.join(input_dir, 'logfile.txt')
    logging.basicConfig(filename=logfile, level=logging.INFO)
    for root, dirs, files in os.walk(input_dir):
        for dir in dirs:
            directory = os.path.join(root,dir)            
            logging.info(f"Processing: {directory}") #record to log
            print(f"Processing: {directory}") #print to console
            seq_type = hf.get_sequence_type(directory)
            if seq_type is not None:#sometimes there is no metadata
                #select ONLY TSeries for batch concat by the process_folder() function
                if "TSeries" in seq_type and "ZSeries" not in seq_type:
                    start_time = time.time()
                    batch_concat_TSeries(directory)
                    elapsed_time = time.time() - start_time
                    print(f"batch_concat_TSeries({directory}) took {elapsed_time} seconds to run.")
                if "ZSeries" in seq_type and "TSeries" not in seq_type:
                    start_time = time.time()
                    batch_concat_ZSeries(directory)
                    elapsed_time = time.time() - start_time
                    print(f"batch_concat_ZSeries({directory}) took {elapsed_time} seconds to run.")
                if "TSeries" in seq_type and "ZSeries" in seq_type:
                    start_time = time.time()
                    batch_concat_TZSeries(directory)
                    elapsed_time = time.time() - start_time
                    print(f"batch_concat_TZSeries({directory}) took {elapsed_time} seconds to run.")
    return

def batch_concat_TSeries(directory):
    '''
    directory: should be the folder containing all individual tifs from a single imaging session
    '''
    dir_name = os.path.basename(directory)
    #list all tiff files with 6 digit identifier '######.ome.tif' -> this allows for specificity of which tif files are selected, concatenated and deleted. 
    file_list = glob.glob(os.path.join(directory, '*[0-9][0-9][0-9][0-9][0-9][0-9].ome.tif')) 
    n = len(file_list)  # Record number of tifs
    print("number of files: " + str(n))
    ch1_files = [f for f in file_list if 'Ch1' in f] #get list of ch1 files
    ch2_files = [f for f in file_list if 'Ch2' in f] #get list of ch2 files
    #this is used to select for if concat has  run or not. I should update this! #could also use the logfile maybe to see if concat was run on this data
    if n > 10: #if there are more than 10 tif files in the directory 
        # Run for Ch1...
        if len(ch1_files) > 1:  
            ch1_files.sort() #check ordering of ch1_files.sort() output
            with tifffile.TiffWriter(os.path.join(directory, f"{dir_name}-Ch1.tif"), bigtiff=True) as tif:
                for x in ch1_files:
                    tif.save(tifffile.imread(x, is_ome=False))
                    logging.info(f"Saved {os.path.join(directory, f'/{dir_name}-Ch1.tif')}") 
            print(f"Saved {os.path.join(directory, f'/{dir_name}-Ch1.tif')}")
        else:
            logging.info("No Channel 1 files.")
        # Run for Ch2...
        if len(ch2_files) > 1:  
            ch2_files.sort()
            with tifffile.TiffWriter(os.path.join(directory, f"{dir_name}-Ch2.tif"), bigtiff=True) as tif:
                for x in ch2_files:
                    tif.save(tifffile.imread(x, is_ome=False))
                    logging.info(f"Saved {os.path.join(directory, f'/{dir_name}-Ch2.tif')}") 
            print(f"Saved {os.path.join(directory, f'/{dir_name}-Ch2.tif')}")
        else:
            logging.info("No Channel 2 files.")
        # Delete individual tif files
        for file in file_list:
            logging.info(f"Deleting {file}")
            os.remove(file)
    else:
        logging.info(f"Not enough images to concatenate in {directory}")
    return
  
def batch_concat_ZSeries(directory):        
    '''
    batch_concat_ZSeries function is exactly the same as batch_concat_TSeries rn
    but will be maintained as a seperate function in case there are different  
    batch concat processes to be selectively apply to TSeries or ZSeries
    '''
    dir_name = os.path.basename(directory)
    #list all tiff files with 6 digit identifier '######.ome.tif' -> this allows for specificity of which tif files are selected, concatenated and deleted. 
    file_list = glob.glob(os.path.join(directory, '*[0-9][0-9][0-9][0-9][0-9][0-9].ome.tif')) 
    n = len(file_list)  # Record number of tifs
    print("number of files: " + str(n))
    ch1_files = [f for f in file_list if 'Ch1' in f] #get list of ch1 files
    ch2_files = [f for f in file_list if 'Ch2' in f] #get list of ch2 files
    #this is used to select for if concat has  run or not. I should update this! #could also use the logfile maybe to see if concat was run on this data
    if n > 10: #if there are more than 10 tif files in the directory 
        # Run for Ch1...
        if len(ch1_files) > 1:  
            ch1_files.sort() #check ordering of ch1_files.sort() output
            with tifffile.TiffWriter(os.path.join(directory, f"{dir_name}-Ch1.tif"), bigtiff=True) as tif:
                for x in ch1_files:
                    tif.save(tifffile.imread(x, is_ome=False))
                    logging.info(f"Saved {os.path.join(directory, f'/{dir_name}-Ch1.tif')}") 
            print(f"Saved {os.path.join(directory, f'/{dir_name}-Ch1.tif')}")
        else:
            logging.info("No Channel 1 files.")
        # Run for Ch2...
        if len(ch2_files) > 1:  
            ch2_files.sort()
            with tifffile.TiffWriter(os.path.join(directory, f"{dir_name}-Ch2.tif"), bigtiff=True) as tif:
                for x in ch2_files:
                    tif.save(tifffile.imread(x, is_ome=False))
                    logging.info(f"Saved {os.path.join(directory, f'/{dir_name}-Ch2.tif')}") 
            print(f"Saved {os.path.join(directory, f'/{dir_name}-Ch2.tif')}")
        else:
            logging.info("No Channel 2 files.")
        # Delete individual tif files
        for file in file_list:
            logging.info(f"Deleting {file}")
            os.remove(file)
    else:
        logging.info(f"Not enough images to concatenate in {directory}")
    return

def batch_concat_TZSeries(directory):
    '''
    directory: should be the folder containing all individual tifs from a single imaging session
    this code assumes all the information included in file name is incldued in the directory. 
    this is the default from Bruker unless you rename your directories independently
    if you ever lose filename info , it should always exist in the metadata! 
    '''
    #list all tiff files with 6 digit identifier '######.ome.tif' -> this allows for specificity of which tif files are selected, concatenated and deleted. 
    file_list = glob.glob(os.path.join(directory, '*[0-9][0-9][0-9][0-9][0-9][0-9].ome.tif')) 
    n = len(file_list)  # Record number of tifs
    print("number of files: " + str(n))
    max_Z_index = hf.get_max_Z_index(directory)
    dir_name = os.path.basename(directory)
    ch1_files = [f for f in file_list if 'Ch1' in f] #get list of ch1 files
    ch2_files = [f for f in file_list if 'Ch2' in f] #get list of ch2 files
    if n > 10: #if there are more than 10 tif files in the directory
        for i in range(1,max_Z_index+1): #iterate through each ID (specific to z plane)
            ID = str(i).zfill(6) 
            if len(ch1_files) > 1: 
                ch1_split_by_ID = [f for f in ch1_files if ID in f] #get all files at z plane specified by 6 digit ID
                ch1_split_by_ID.sort() #makes sure the images are in order (this will order by cycle no.)
                with tifffile.TiffWriter(os.path.join(directory, f"{dir_name}-{ID}-Ch1.tif"), bigtiff=True) as tif:
                    for x in ch1_split_by_ID:
                        tif.save(tifffile.imread(x,is_ome=False))
                        logging.info(f"Saved {os.path.join(directory, f'/{dir_name}-{ID}-Ch1.tif')}") 
                print(f"Saved {os.path.join(directory, f'/{dir_name}-{ID}-Ch1.tif')}")
            else:
                logging.info("No Channel 1 files.")
            if len(ch2_files) > 1: 
                ch2_split_by_ID = [f for f in ch2_files if ID in f]
                ch2_split_by_ID.sort()
                with tifffile.TiffWriter(os.path.join(directory, f"{dir_name}-{ID}-Ch2.tif"), bigtiff=True) as tif:
                    for x in ch2_split_by_ID:
                        tif.save(tifffile.imread(x,is_ome=False))
                        logging.info(f"Saved {os.path.join(directory, f'/{dir_name}-{ID}-Ch2.tif')}") 
                print(f"Saved {os.path.join(directory, f'/{dir_name}-{ID}-Ch2.tif')}")
            else:
                logging.info("No Channel 2 files.")
        # Delete individual tif files
        for file in file_list:
            logging.info(f"Deleting {file}")
            os.remove(file)
    else:
        logging.info(f"Not enough images to concatenate in {directory}")   
    return       
  
    
#CALL FUNCTIONS BELOW 
input_dir = '/Volumes/T7/First_Pilot_Data/S15742_gregg'
process_dir(input_dir)


'''
notes for TZ series
the file name has this ending Cycle00002_Ch2_000001
where 000001 will always refer to the same z plane / depth 
Cycle00002 tells you the T iteration that you are on for the whole z stack
'''