#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 11 23:17:59 2024

@author: emmaodom
#things to record in pandas df
#animal ID, date (can get from xml?), cell id, dend id, tracking day
#preprocess: rois drawn, measured?
#analysis: event_rate/total, total variance, regression coeff (drift metric)
"""

import os
import re
import glob
import pandas as pd
import time
import logging
import xml.etree.ElementTree as ET 

from src import helper_functions as hf
#from plot_dFF import get_event_rate, get_variance

#ADD ANIMAL ID, CAN MOST LIKELY USE THE PARENT DIR
def extract_metadata(directory):
    # Check if 'SingleImage' is in the directory name
    if 'SingleImage' in directory:
        return None 
    if hf.check_if_single_frame(directory):
        return None
    xml = hf.get_xml_image(directory)
    if xml is not None:
        match = re.search(r'(?i)_cell(\d+)_dend(\d+)_', directory)
        if match:
            cell_number = match.group(1)
            dend_number = match.group(2)
        else:
            cell_number = None
            dend_number = None
        match_id = re.search(r'\/(\d{3}[A-Za-z])\/', directory)
        # Extract and return the animal ID if found
        if match_id:
            animal_id = match_id.group(1)
        else:
            animal_id = None
        # Use your helper functions to extract data from the XML file
        date = hf.get_imaging_date(directory)
        seq_type = hf.report_sequence_type(directory) 
        frame_period = hf.get_frame_period(directory) #time per frame
        avg = hf.get_avg(directory) #num averages per scan
        sampling_rate = 1/(avg*frame_period) #units: Hz, number frames per second
        duration = hf.get_imaging_session_duration(directory)
        laser_power = hf.get_laser_power(directory)
        pmt_gain = hf.get_pmt_gain(directory, "Ch 2 GaAsP")#make two calls if need ch1 and ch2
        wavelength = hf.get_wavelength(directory)
        objective = hf.get_objective(directory)
        resolution = hf.get_resolution(directory)
        microns = hf.get_microns_per_pixel(directory)
        batch_concat = hf.check_batch_concat(directory)
        double_motion_corrected = hf.check_double_motion_correct(directory)
        # Construct and return a dictionary of the extracted data
        #return date, seq_type, frame_period, avg, sampling_rate, duration, laser_power, pmt_gain, wavelength, double_motion_corrected,   # other metrics
        return {
            'animal':animal_id,
            'cell':cell_number,
            'dend':dend_number,
            'date':date, 
            'seq_type':seq_type, 
            'frame_period':frame_period, 
            'avg':avg, 
            'sampling_rate':sampling_rate, 
            'duration(sec)':duration, 
            'laser_power':laser_power, 
            'pmt_gain':pmt_gain, 
            'wavelength(nm)':wavelength,
            'objective':objective,
            'resolution':resolution,
            'microns_per_pixel(u^2)': microns,
            'batch_concat':batch_concat,
            '2x_motion_corrected':double_motion_corrected[2]
            # Add other metrics here...
            }
    else:
        return None

def summarize(input_dir):
    #add lines here or in helper function to filter out singleimage folders. 
    data = []
    for root, dirs, files in os.walk(input_dir):
        for dir in dirs:
            directory = os.path.join(root, dir)
            # Extract metadata using helper functions
            metadata = extract_metadata(directory)
            # Check if metadata is extracted, handle cases where it's not
            if metadata:
                # Add directory information
                metadata['Directory'] = dir
                data.append(metadata)
    # Create a DataFrame from the collected data
    df = pd.DataFrame(data)
    #convert cell and dend to integers 
    df['cell'] = pd.to_numeric(df['cell'], errors='coerce')
    df['dend'] = pd.to_numeric(df['dend'], errors='coerce')
    return df

#TEST:
#meta = extract_metadata('/Volumes/T7/Motor_Spines_Pilot_Data/289N/231023/289N_231023_920nm_20x_10xd_Tseries_114.15um_512_512px_4avg-042')

#summary = summarize('/Volumes/T7/Motor_Spines_Pilot_Data/293L') 289N
summary = summarize('/Volumes/T7/Motor_Spines_Pilot_Data')

#ADD SAVE LINES 
path_parent = '/Volumes/T7/Motor_Spines_Pilot_Data/'
dir_save = 'python_dataframes'
path_save = path_parent + dir_save
if not os.path.exists(path_save):
    os.makedirs(path_save)
# Save the dataframe to a CSV file in python_dataframes dir
summary.to_csv(os.path.join(path_save, 'summary.csv'), index=False)
print('summary Dataframe saved to CSV file at:', path_save)

