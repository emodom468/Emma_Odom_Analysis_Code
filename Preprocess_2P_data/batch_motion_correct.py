#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  9 21:35:41 2024

@author: emmaodom

BATCH_MOTION_CORRECT.PY AUTOMATES CALLS TO THE IMAGEJ MACRO FOR MOTION CORRECTION.
this is the first succesful implementation of calls to imagej from python
This allows the script to handle the directory searching, metadata based decision making 
and file pattern identification all in python which is better optimized to this task. 
Yet, FIJI still has some useful legacy functions, so this allows you to integrate them into
batch preprocessing. 
"""

import os
import re
import logging
import time
import subprocess

from src import helper_functions as hf

#CHECK STATUS OF MOTION CORRECTION BEFORE RUNNING BATCH
#uncomment call to batch_motion_correction, when ready.
results = hf.record_motion_correct_status('/Volumes/T7/Motor_Spines_Pilot_Data/289N')

# Replace this with the path you got from `/usr/libexec/java_home -v 21`
java_home_path = "/Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home"
os.environ['JAVA_HOME'] = java_home_path

def motion_correct_TSeries(fiji_path, macro_path, file_path):
    '''
    important macro information:
        there is a specific structure at beginning and end of macro to be able to 
        run without user input and to accept inputs from command line call. 
        
    Parameters
    ----------
    fiji_path : string
        DESCRIPTION.
    macro_path : string
        full path to motion_correct_single_TSeries.ijm macro 
    file_path : string
        full path to tiff stack to be motion corrected. selection criteria must
        be implemented before calling macro from commandline. 

    Returns
    -------
    None.

    '''
    # Construct the command without '--headless' for macros that require GUI
    cmd = [fiji_path, '-macro', macro_path, file_path]
    # Run the command as a subprocess
    subprocess.run(cmd)
    return

###TEST ALL ABOVE BEFORE INTEGRATING BATCH
def batch_motion_correction(input_dir, fiji_path, macro_path):
    '''
    checks for TSeries type, tiff file pattern, and that stab 1.csv, stab 2.csv, dont already exist
    before making command line call to motion_correct_single_TSeries.ijm macro
    UPGRADE: once the TZSeries motion correction macro is updated for double pass and batch processing
    include a call to this macro under the TZSeries condition. 
    '''
    ###THIS NEEDS TO BE RUN ONCE AT START OF BATCH PROCESS. 
    # Path to the macro file #13.5GB
    macro_setMemory = "/Volumes/T7/Analysis_code/macros/set_memory_and_quit.ijm"
    #Construct the command
    cmd = [fiji_path, '--headless', '-macro', macro_setMemory]
    # Run the command as a subprocess
    subprocess.run(cmd)
    ###END
    
    # Regular expression pattern to match specific file format
        #selection criteria could be more extensive
    patterns_ = [r'^\d{3}.*Ch2\.tif$',r'^\d{3}.*Ch2\.ome.tif$']
    patterns = '|'.join(patterns_)
    # Set up logging for each directory
    logfile = os.path.join(input_dir, 'logfile.txt')
    logging.basicConfig(filename=logfile, level=logging.INFO)
    for root, dirs, files in os.walk(input_dir):
        for dir in dirs:
            #update this bc you are looking for file tiff list, and just need directory of tiff to save respective results
            #file_list = glob.glob(os.path.join(directory, '*[0-9][0-9][0-9][0-9][0-9][0-9].ome.tif')) 
            directory = os.path.join(root,dir)            
            logging.info(f"Processing: {directory}") #record to log
            print(f"Processing: {directory}") #print to console
            seq_type = hf.get_sequence_type(directory)
            if seq_type is not None:#sometimes there is no metadata
                if "TSeries" in seq_type and "ZSeries" not in seq_type:
                    file1_exists, file2_exists, both_exist = hf.check_double_motion_correct(directory)
                    if both_exist == False:
                        tiff_files = [f for f in os.listdir(directory) if re.match(patterns, f)] 
                        if len(tiff_files) == 1:
                            file_path = os.path.join(directory, tiff_files[0])
                            print("conditions met: "+file_path)
                            start_time = time.time() 
                            #comment out below to check file processing. 
                            motion_correct_TSeries(fiji_path, macro_path, file_path)
                            elapsed_time = time.time() - start_time
                            print(f"motion_correction_TSeries({directory}) took {elapsed_time} seconds to run.")
                if "ZSeries" in seq_type and "TSeries" not in seq_type:
                    print(f"ZSeries ({directory}) do not need to be motion corrected")
                if "TSeries" in seq_type and "ZSeries" in seq_type:
                    file1_exists, file2_exists, both_exist = hf.check_double_motion_correct(directory)
                    if both_exist == False:
                        #start_time = time.time()
                        #motion_correct_TZSeries(directory)
                        #elapsed_time = time.time() - start_time
                        print("TZSeries skip")
                        #print(f"motion_correction_TZSeries({directory}) took {elapsed_time} seconds to run.")
    return

fiji_path = "/Applications/Fiji.app/Contents/MacOS/ImageJ-macosx"
macro_path = '/Volumes/T7/Analysis_code/macros/motion_correct_single_TSeries.ijm'
input_dir = '/Volumes/T7/First_Pilot_Data/S15742_gregg/230928'
#batch_motion_correction(input_dir, fiji_path, macro_path)


'''###MEM CAP NEEDS TO BE RUN ONCE AT START OF BATCH PROCESS. 
# Path to the macro file #13.5GB
macro_setMemory = "/Volumes/T7/Analysis_code/macros/set_memory_and_quit.ijm"
# Construct the command
cmd = [fiji_path, '--headless', '-macro', macro_setMemory]
# Run the command as a subprocess
subprocess.run(cmd)
###END
'''

''' EXAMPLE: SEND MACRO COMMAND TO TERMINAL 
# Now construct your Fiji command
fiji_path = "/Applications/Fiji.app/Contents/MacOS/ImageJ-macosx"
macro_path = '/Volumes/T7/Analysis_code/macros/test_function.ijm'
file_path1 = '/Volumes/T7/Motor_Spines_Pilot_Data/293L/231103/293L_231103_Cell1_dend1_920nm_20x_20xd_Tseries_115.08um_512px_0Avg-069/293L_231103_Cell1_dend1_920nm_20x_20xd_Tseries_115.08um_512px_0Avg-069-Ch2.tif'
file_path2 = '/Volumes/T7/Motor_Spines_Pilot_Data/293L/231105/293L_231105_Cell2_dend1_920nm_20x_20xd_Tseries_78um_512px_0Avg-083/293L_231105_Cell2_dend1_920nm_20x_20xd_Tseries_78um_512px_0Avg-083-Ch2.tif'

cmd = [fiji_path, '-macro', macro_path, file_path1]
subprocess.run(cmd)
cmd = [fiji_path, '-macro', macro_path, file_path2]
subprocess.run(cmd)
'''

'''EXAMPLE: INDIVIDUAL RUN OF MOTION_CORRECT_TSERIES_MACRO (NOT BATCH PROCESSING)
fiji_path = "/Applications/Fiji.app/Contents/MacOS/ImageJ-macosx"
macro_path = '/Volumes/T7/Analysis_code/macros/motion_correct_single_TSeries.ijm'
input_dir = '/Volumes/T7/Motor_Spines_Pilot_Data/293L/231103'
file_path1 = '/Volumes/T7/Motor_Spines_Pilot_Data/293L/231109/231109_293L_cell4_dend1_20x_15xd_920nm_176um_TSeries_0avg-012/231109_293L_cell4_dend1_20x_15xd_920nm_176um_TSeries_0avg-012-Ch2.tif'
#'/Volumes/T7/Motor_Spines_Pilot_Data/293L/231103/293L_231103_Cell1_dend1_920nm_20x_20xd_Tseries_115.08um_512px_0Avg-069/293L_231103_Cell1_dend1_920nm_20x_20xd_Tseries_115.08um_512px_0Avg-069-Ch2.tif'
file_path2 = '/Volumes/T7/Motor_Spines_Pilot_Data/293L/231105/293L_231105_Cell2_dend1_920nm_20x_20xd_Tseries_78um_512px_0Avg-083/293L_231105_Cell2_dend1_920nm_20x_20xd_Tseries_78um_512px_0Avg-083-Ch2.tif'
#reference_slice = '10'  # Example reference slice number

motion_correct_TSeries(fiji_path, macro_path, file_path1)
motion_correct_TSeries(fiji_path, macro_path, file_path2)
'''

'''if reviving pyimagej:
#import imagej
#imagej library path: /Users/emmaodom/opt/miniconda3/lib/python3.10/site-packages
'''