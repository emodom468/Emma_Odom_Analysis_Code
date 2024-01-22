#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 16:59:06 2023

@author: emmaodom
"""

import os
import re
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from src import helper_functions as hf

def get_roi_trace_files(directory):
    #column 0: spine; column 1: background (iterates 0-1)
    file1 = glob.glob(os.path.join(directory, '**', '*spine0_bgr1*.csv'), recursive=True)
    file2 = glob.glob(os.path.join(directory, '**', '*0spine_1bgr*.csv'), recursive=True)
    file_list = file1+file2
    return file_list

def get_raw_fluorescence_trace(file_path):
    #import data to pandas df
    #csv structure: each column is an ROI, each row is fluorescence (mean grey value) at a timepoint
    df = pd.read_csv(file_path)
    #remove first column, which is just index values from imageJ results file
    df = df.loc[:, df.columns != ' ']
    return df

def get_bgr_subtracted_trace(file_path):
    df = get_raw_fluorescence_trace(file_path)
    #spine_background_subtracted = spine roi mean grey value - mean grey of same roi in background 
    spine_bgr_subtracted = pd.DataFrame()
    #subtract background from spine signal for every spine
    for i in range(0,len(df.columns),2):
        spine_bgr_subtracted[i//2] = df.iloc[:,i] - df.iloc[:,i+1]
    return spine_bgr_subtracted

def get_num_spines(file_path):
    df = get_raw_fluorescence_trace(file_path)
    num_spines = df.shape[1]/2
    return int(num_spines)

#need helper functions to access relevant metadata (ie to determine how many rows/frames go into a rolling window)
def get_dFF(file_path, f0_ = 'mode', window_size = 30):
    '''

    Parameters
    ----------
    file_path : string
        file_path to csv file
    f0 : string
       'mean': calculate f0 as the mean value for each ROI
       'mode': calculate f0 as the most common value for each ROI
       'rolling10': calculate f0 as the lowest 10th percentile F value over rolling window
       'rollingMean': calculate f0 as the mean value over rolling window
    window_size: integer (seconds)
        duration of rolling window in seconds

    Returns
    -------
    dFF: dataframe
        each column is the dFF (change in fluorescence) of a single spine roi 

    '''
    directory = os.path.dirname(file_path)
    #spine_background_subtracted = spine roi mean grey value - mean grey of same roi in background 
    spine_bgr_subtracted = get_bgr_subtracted_trace(file_path)
    if f0_ == 'mode':
        #calculate f0 as the most common value for each ROI
        f0 = spine_bgr_subtracted.mode().median() #this will find all mode (most common) values, and select the middle range mode if there are multiple
        #replace any 0 values with nonzero value, to prevent errors when calculating df/f trace
        f0 = f0.replace(0,1)#alternative just add one to everything (that way it is also a consistent offset for all values)
    if f0_ == 'rolling10':
        #calculate f0 as lowest 10th percentil of moving window
        frame_period = hf.get_frame_period(directory) #time per frame
        avg = hf.get_avg(directory) #num averages per scan
        sampling_rate = 1/(avg*frame_period) #units: Hz, number frames per second
        window_frames = int(window_size*sampling_rate) #num of frames to match duration of window_size
        #this calulates the 10th percentile of a rolling window of size window_frames
            #min_periods=1 allows df.rolling() to report a value for all indeces before the window_frames number is reached 
            #quantile(0.1) reports the value below which 10 percent of the data falls
        f0 = spine_bgr_subtracted.rolling(window = window_frames, min_periods = 1).quantile(0.1)
        #f0 = rolling10 use rolling10 as f0
    #DFF CODE: calculate df/f stored in dFF dataframe
    dFF = pd.DataFrame()
    #perform (f(t)-f0)/f0 in two steps, to avoid a for loop! 
    #step one, subtract f0 from f(t)
    dFF = spine_bgr_subtracted.subtract(f0)
    #step two, divide by f0
    dFF = dFF.div(f0) #the rolling 10 value needs to be above zero
    #do we want to save the dFF dataframe?
    return dFF

def get_event_detection(file_path, f0_ = 'mode', window_size = 30):
    '''
    Parameters
    ----------
    file_path : string
        file_path to csv file.
    f0 : string
        DESCRIPTION. The default is 'mode'.
        This variable is passed to get_dFF()
        'mean': calculate f0 as the mean value for each ROI
       'mode': calculate f0 as the most common value for each ROI
       'rolling10': calculate f0 as the lowest 10th percentile F value over rolling window
       'rollingMean': calculate f0 as the mean value over rolling window
    window_size : integer (seconds)
        DESCRIPTION. The default is 30.
        This is passed to get_dFF()
        duration of rolling window in seconds

    Returns
    -------
    event_detect : pandas dataframe
        reports if the dFF value goes above the threshold. the threshold is 
        currently defined as 3 standard deviations above the mean. std and mean
        are calculated over the rolling period of window_size (sec)
    '''
    dFF = get_dFF(file_path, f0_, window_size)
    #get metadata
    directory = os.path.dirname(file_path)
    frame_period = hf.get_frame_period(directory) #time per frame
    avg = hf.get_avg(directory) #num averages per scan
    sampling_rate = 1/(avg*frame_period) #units: Hz, number frames per second
    window_frames = int(window_size*sampling_rate) #num of frames to match duration of window_size
    #calculate rolling std for each spine roi
        #min periods tells you how many frames are needed to calcualte std
    rollingSTD = dFF.rolling(window = window_frames, min_periods = 8).std() #why 8?
    rollingSTD.fillna(1,inplace=True)
    rollingMean = dFF.rolling(window = window_frames, min_periods = 1).mean()
    threshold = rollingMean + (3*rollingSTD)
    event_detect = dFF.gt(threshold) #df1.gt(df2) checks if df1 value is greater than df2 value, element by element
    return event_detect

def plot_dFF(file_path, f0_ = 'mode', window_size = 30, event_detection = True):
    dFF = get_dFF(file_path, f0_, window_size)
    n = len(dFF) #number of frames, n
    #get metadata
    directory = os.path.dirname(file_path)
    frame_period = hf.get_frame_period(directory) #time per frame
    avg = hf.get_avg(directory) #num averages per scan
    time = np.linspace(0,int(n*frame_period*avg),n) 
        #start: 0, end: n*frame_period*avg, number of points:n
        #number of frames * time per frame * num of averages should equal total imaging time
    path_svg = directory +'/svg/'
    if not os.path.exists(path_svg):
        os.makedirs(path_svg)
    for roi in range(dFF.shape[1]):
        plt.figure()
        plt.xlabel('(sec)')
        plt.ylabel('dF/F')
        plt.title(f"Spine {roi}")  
        plt.plot(time,dFF[roi],color='r')
        save_svg = directory +'/svg/' + f'spine_{roi}_dFF.svg'
        print(save_svg)
        if event_detection == True:
            event_detect = get_event_detection(file_path, f0_, window_size)
            plt.title(f"Spine {roi} with event detection")
            save_svg = directory +'/svg/' + f'spine_{roi}_dFF_w_event_detection.svg'
            x = [time[i] for i,j in enumerate(event_detect[roi]) if j==True]
            #y_ is defined relative to higher bound of dFF, to plot event dots at top
            y_ = 1.5*dFF[roi].max()
            y = [y_*j for j in event_detect[roi] if j == True]
            plt.scatter(x,y, color = 'b')
        plt.savefig(save_svg, format = 'svg')
    return 

def get_event_rate(file_path, f0_ = 'mode', window_size = 30):
    directory = os.path.dirname(file_path)
    dur = hf.get_imaging_session_duration(directory)
    sum_events = get_event_detection(file_path, f0_, window_size).sum()
    return sum_events/dur

def get_variance(file_path, state = 'dFF', f0_ = 'mode', window_size = 30):
    if state == 'raw':
        raw_traces = get_raw_fluorescence_trace(file_path)
        variances = raw_traces.var()
    if state == 'bgr_subtracted':
        F_traces = get_bgr_subtracted_trace(file_path) 
        variances = F_traces.var()
    if state == 'dFF':
        dFF = get_dFF(file_path, f0_, window_size)
        variances = dFF.var()
    return variances

def get_baseline_drift():
    #either by linear regression 
    #or other baseline correction method and subtraction (see bio image analysis gpt)
    #note to self baseline corr should probably be done on raw, not subtracted trace. 
    return

def corr_spine_dFF():
    #lines 11 through 141 in plot_spine_dFF but too messy I dont want to copy over. 
    #/Users?emma?Desktop?plot_spine_dFF_112923
    '''
    corr_spine_bgr_sub = spine_bgr_subtracted.corr(method='pearson')
    corr_dFF = dFF.corr(method = "pearson")
    mask = np.triu(np.ones_like(corr_dFF, dtype=bool))
    plt.figure()
    plt.title("Pearson correlation for spine fluorescence time series with background subtracted")
    cmap = sns.diverging_palette(230, 20, as_cmap=True)
    sns.heatmap(corr_spine_bgr_sub,mask=mask, cmap = cmap)
    plt.figure()
    plt.title("Pearson correlation for spine dFF (f0=rolling 10th percentile)")
    sns.heatmap(corr_dFF, mask=mask, cmap = cmap)
    diff = corr_dFF-corr_spine_bgr_sub
    plt.figure()
    plt.title("Difference in pearson correlation from spine bgr sub to spine dFF")
    sns.heatmap(diff, mask=mask, cmap = cmap)
    
    
    #repeat of pearson correlation, but as spearman correlation. 
    #results: the output figures look very very similar between pearson and spearman 
    #which indicates that the method of correlation calcualtion is not super important. 
    #spearman is supposed to use a ranking system where it compares the position of ranked (lowest to highest values within time series) flourescence between time series 
    corr_spine_bgr_sub = spine_bgr_subtracted.corr(method='spearman')
    corr_dFF = dFF.corr(method = "spearman")
    mask = np.triu(np.ones_like(corr_dFF, dtype=bool))
    plt.figure()
    plt.title("Spearman correlation for spine fluorescence time series with background subtracted")
    cmap = sns.diverging_palette(230, 20, as_cmap=True)
    sns.heatmap(corr_spine_bgr_sub,mask=mask, cmap = cmap)
    plt.figure()
    plt.title("Spearman correlation for spine dFF (f0=rolling 10th percentile)")
    sns.heatmap(corr_dFF, mask=mask, cmap = cmap)
    diff = corr_dFF-corr_spine_bgr_sub
    plt.figure()
    plt.title("Difference in spearman correlation from spine bgr sub to spine dFF")
    sns.heatmap(diff, mask=mask, cmap = cmap)
        '''
    return

#use this loop to plot_dFF for all spines in all sessions. 
file_list = get_roi_trace_files('/Volumes/T7/Motor_Spines_Pilot_Data')
for file in file_list: 
    dFF = get_dFF(file)
    event_detect = get_event_detection(file)
    plot_dFF(file)
    var = get_variance(file)
    event_rate = get_event_rate(file, f0_ = 'mode', window_size = 30)
    break #use break to test on single session
 
    
#USE THIS LOOP TO CREATE THE COMPREHENSIVE EVENT DETECT AND VARIANCE DATAFRAMES. 
# Initialize lists for DataFrame columns
file_paths = []
#parent_dirs = []
animal_IDs = []
dates = []
cell_ids = []
dend_ids = []
event_detects = []
event_rates = []
event_means = []
event_stdevs = []
variances = []
var_dFF_means = []
#pearson_corrs = []
num_spines = []

file_list = get_roi_trace_files('/Volumes/T7/Motor_Spines_Pilot_Data')
for file in file_list: 
    #Calculate metrics
    event_detect = get_event_detection(file, f0_ = 'mode', window_size = 30)
    event_rate = get_event_rate(file, f0_ = 'mode', window_size = 30)
    var = get_variance(file, state = 'dFF', f0_ = 'mode', window_size = 30)
    #corr = corr_spine_dFF()
    # Get ID info
    file_paths.append(file)
    parent_dir = os.path.dirname(file)
    #parent_dirs.append(os.path.dirname(file))
    path_parts = os.path.dirname(file).split(os.sep)
    animal_IDs.append(path_parts[-3])
    dates.append(path_parts[-2])
    # Flexible regex pattern to find cell and dend numbers
    # This pattern is case-insensitive and allows for some variability in naming
    match = re.search(r'(?i)_cell(\d+).*?_dend(\d+)', parent_dir)
    if match:
        cell_id = match.group(1)
        dend_id = match.group(2)
    else:
        cell_id = None
        dend_id = None
    cell_ids.append(cell_id)
    dend_ids.append(dend_id)
    # Append data to lists
    event_detects.append(pd.DataFrame(event_detect))  
    event_rates.append(pd.Series(event_rate))
    event_means.append(event_rate.mean())
    event_stdevs.append(event_rate.std())
    variances.append(var)
    var_dFF_means.append(var.mean())
    #pearson_corrs.append(corr)
    num_spines.append(get_num_spines(file))

    #break # Remove this break to process all files

# Create DataFrame
activity = pd.DataFrame({
    'File Path': file_paths,
    #'Parent Directory': parent_dirs,
    'Animal ID': animal_IDs,
    'Date': dates,
    'Cell': cell_ids,
    'Dend': dend_ids,
    'Event Detect': event_detects,
    'Event Rate': event_rates,
    'Event Mean': event_means,
    'Event Stdev': event_stdevs,
    'dFF_var': variances,
    'mean_dFF_var': var_dFF_means,
    'Number of Spines': num_spines
})


 
    
    
#if you save a lot of figures, save as svg bc they take least storage space. 
#for now, I will save event detect as its own csv for every imaging session because 
#I previously used vstack to concatenate matrices for kyles data, but there is
#no clear seperation of cells/sessions/etc so it doesnt seem like a favorable approach
#instead i will record a summary statistic in the summary df 
    
    