#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 18:43:53 2023

@author: emmaodom
"""

#each other module should import helper_functions as hf
#UPDATE GET DURATION FOR TZSERIES. 

import os
import glob
import time
import tifffile
import logging
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime

#get_xml_image, get_sequence_type, and get_max_z_index are duplicates from batch_concat.py

def get_xml_image(directory):
    '''
the purpose of this function is to search a directory (imaging session folder) 
for the xml file with imaging metadata (and to exclude voltage recording metadata) 
    Parameters
    ----------
    directory : TYPE
        DESCRIPTION.

    Returns
    -------
    xml_file : TYPE
        DESCRIPTION.

    '''
        #get list of xml files
    xml_files = glob.glob(os.path.join(directory, '*.xml'))
    if len(xml_files) == 0:
        print("No XML files found.")
        return None
    #sort xml files in case there are more than 1 
    if len(xml_files)>1:
        xml_files = [f for f in xml_files if 'VoltageRecording' not in f]
    #get string from list structure
    xml_file = xml_files[0]
    return xml_file

def get_sequence_type(directory):
    '''
    #I wrote this function to identify TSeries, ZSeries, TZSeries
    this function returns sequence type of imaging as Tseries, Zseries, or TZSeries
    it first identifies the correct xml file with relevant imaging metadata 
    it then parses the xml file for 'Sequence type' 
    it returns the string that follows Sequence Type in the metadata
    
    example Sequence Type from emtadata 
    #<Sequence type="TSeries Timed Element"
    #<Sequence type="TSeries ZSeries Element"
    '''
    #get list of xml files
    xml_file = get_xml_image(directory)
    if xml_file is None:
        return
    # Parse the XML file
    tree = ET.parse(xml_file)
    # Get the root of the XML document
    root = tree.getroot()
    # Iterate over all 'Sequence' elements in the document
    for sequence in root.iter('Sequence'):
        # If the 'type' attribute exists, return its value
        if 'type' in sequence.attrib:
            return sequence.attrib['type']

def report_sequence_type(directory):
    seq_type = get_sequence_type(directory)
    if seq_type is not None:
        if "TSeries" in seq_type and "ZSeries" not in seq_type:
            return 'T'
        if "ZSeries" in seq_type and "TSeries" not in seq_type:
            return 'Z'
        if "TSeries" in seq_type and "ZSeries" in seq_type:
            return 'TZ'

def get_max_Z_index(directory):
    '''
    Parameters
    ----------
    directory : TYPE
        DESCRIPTION.

    Returns
    -------
    max_index : TYPE
        DESCRIPTION.

    '''
    xml_file = get_xml_image(directory)
    if xml_file is None:
        return
    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()
    # Find the first Sequence element with cycle='1'
    sequence = root.find(".//Sequence[@cycle='1']")
    if sequence is not None:
        # Get all Frame elements within this Sequence
        frames = sequence.findall('.//Frame')
        # Extract the index attribute from each Frame, convert to int, and find the max
        max_index = max(int(frame.get('index')) for frame in frames)
        return max_index
    else:
        print("No Sequence element with cycle='1' found.")
        return None


def get_avg(directory):
    '''
    This function finds the time between two frames, 
    and divides by the frame period to get the number of averages per scan.

    Parameters
    ----------
    directory : str
        The directory path.

    Returns
    -------
    int or None
        The number of averages per scan or None if calculation is not possible.
    '''
    fp = get_frame_period(directory)
    # Get list of XML files
    xml_file = get_xml_image(directory)
    if xml_file is None:
        return None
    
    # Parse the XML file
    tree = ET.parse(xml_file)
    # Get the root of the XML document
    root = tree.getroot()
    
    relativeTimes = []
    for frame in root.iter('Frame'):
        relativeTime = frame.attrib.get('relativeTime')
        if relativeTime is not None:
            relativeTimes.append(float(relativeTime))
        if len(relativeTimes) == 2:  # Take only first two recorded points
            break
    # Check if we have at least two time points
    if len(relativeTimes) < 2:
        print('Only one frame detected')
        return None 

    T2_T1 = relativeTimes[1] - relativeTimes[0]  # Time between first two frames
    avg = round(T2_T1 / fp)
    return avg
    
def get_frame_period(directory):
    #get list of xml files
    xml_file = get_xml_image(directory)
    if xml_file is None:
        return
    # Parse the XML file
    tree = ET.parse(xml_file)
    # Get the root of the XML document
    root = tree.getroot()
    for pv_state_value in root.iter('PVStateValue'):
        if pv_state_value.attrib.get('key') == 'framePeriod':
            fp = pv_state_value.attrib.get('value')
            return float(fp)
    return None

def get_laser_power(directory):
    """
    Extracts the laser power from the XML metadata file.

    Parameters:
    directory (str): Path to the directory containing the XML file.

    Returns:
    float: Laser power or None if not found.
    """
    xml_file = get_xml_image(directory)
    if xml_file is None:
        return None
    try:
        # Parse the XML file
        tree = ET.parse(xml_file)
        root = tree.getroot()
        # Iterate through PVStateValue elements to find laser power
        for pv_state_value in root.iter('PVStateValue'):
            if pv_state_value.attrib.get('key') == 'laserPower':
                for indexed_value in pv_state_value.findall('IndexedValue'):
                    if indexed_value.attrib.get('description') == 'Insight Pockels':
                        laser_power = float(indexed_value.attrib.get('value', 0))
                        return laser_power
        return None
    except ET.ParseError:
        print("Error parsing the XML file.")
        return None
    except ValueError:
        print("Error in laser power value.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_pmt_gain(directory, channel_description):
    """
    Extracts the PMT gain for a specified channel from the XML metadata file.

    Parameters:
    directory (str): Path to the directory containing the XML file.
    channel_description (str): Description of the channel to get the PMT gain for.

    Returns:
    int: PMT gain for the specified channel or None if not found.
    """
    xml_file = get_xml_image(directory)
    if xml_file is None:
        return None

    try:
        # Parse the XML file
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Iterate through PVStateValue elements to find pmtGain
        for pv_state_value in root.iter('PVStateValue'):
            if pv_state_value.attrib.get('key') == 'pmtGain':
                for indexed_value in pv_state_value.findall('IndexedValue'):
                    if indexed_value.attrib.get('description') == channel_description:
                        pmt_gain = int(indexed_value.attrib.get('value', 0))
                        return pmt_gain
        return None
    except ET.ParseError:
        print("Error parsing the XML file.")
        return None
    except ValueError:
        print("Error in PMT gain value.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_wavelength(directory):
    """
    Checks which laser has non-zero power and returns the wavelength of that laser.

    Parameters:
    directory (str): Path to the directory containing the XML file.

    Returns:
    int: Wavelength of the active laser or None if not found.
    """
    xml_file = get_xml_image(directory)
    if xml_file is None:
        return None
    try:
        # Parse the XML file
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Dictionary to store laser power
        laser_power = {}
        # Dictionary to store laser wavelength
        laser_wavelength = {}

        # Iterate through PVStateValue elements
        for pv_state_value in root.iter('PVStateValue'):
            key = pv_state_value.attrib.get('key')
            if key == 'laserPower':
                # Find laser power
                for indexed_value in pv_state_value.findall('IndexedValue'):
                    index = indexed_value.attrib.get('index')
                    value = float(indexed_value.attrib.get('value', 0))
                    laser_power[index] = value
            elif key == 'laserWavelength':
                # Find laser wavelength
                for indexed_value in pv_state_value.findall('IndexedValue'):
                    index = indexed_value.attrib.get('index')
                    value = int(indexed_value.attrib.get('value', 0))
                    laser_wavelength[index] = value

        # Check which laser is active and return its wavelength
        for index, power in laser_power.items():
            if power > 0:  # Non-zero power indicates active laser
                return laser_wavelength.get(index, None)

        return None
    except ET.ParseError:
        print("Error parsing the XML file.")
        return None
    except ValueError:
        print("Error in value format.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_objective(directory):
    '''
can use objectiveLens for the naming, of objectiveLensMag for just the number magnification
<PVStateValue key="objectiveLens" value="20x_new"/>
<PVStateValue key="objectiveLensMag" value="20"/>
    '''
    xml_file = get_xml_image(directory)
    if xml_file is None:
        return None
    try:
        # Parse the XML file
        tree = ET.parse(xml_file)
        root = tree.getroot()
        obj_lens = None
        obj_mag = None
        for pv_state_value in root.iter('PVStateValue'):
            if pv_state_value.attrib.get('key') == 'objectiveLens':
                obj_lens = pv_state_value.get('value')
            elif pv_state_value.attrib.get('key') == 'objectiveLensMag':
                obj_mag = pv_state_value.get('value')
        return obj_lens #can switch out with objective magnification for numerical value
    except ET.ParseError:
        return None  
    
def get_resolution(directory):
    xml_file = get_xml_image(directory)
    if xml_file is None:
        return None
    try:
        # Parse the XML file
        tree = ET.parse(xml_file)
        root = tree.getroot()
        lines_per_frame = None
        pixels_per_line = None
        # Iterate through PVStateValue elements to find laser power
        for pv_state_value in root.iter('PVStateValue'):
            if pv_state_value.attrib.get('key') == 'linesPerFrame':
                lines_per_frame = int(pv_state_value.get('value'))
            elif pv_state_value.attrib.get('key') == 'pixelsPerLine':
                pixels_per_line = int(pv_state_value.get('value'))
        # Check if both values are found
        if lines_per_frame is not None and pixels_per_line is not None:
            return [lines_per_frame, pixels_per_line]
        else:
            return None
    except ET.ParseError:
        return None  
    
def get_microns_per_pixel(directory):
    ''' 
    returns microns_per_pixels with unit microns squared
    '''
    xml_file = get_xml_image(directory)
    if xml_file is None:
        return None
    try:
        # Parse the XML file
        tree = ET.parse(xml_file)
        root = tree.getroot()
        microns_per_pixel = None
        x = None
        y = None
        for pv_state_value in root.iter('PVStateValue'):
            if pv_state_value.attrib.get('key')=='micronsPerPixel':
                for indexed_value in pv_state_value.findall('IndexedValue'):
                    index = indexed_value.get('index')
                    value = float(indexed_value.get('value', 0))
                    if index == 'XAxis':
                        x = value
                    elif index == 'YAxis':
                        y = value
        if x is not None and y is not None:
            microns_per_pixel = x*y
            return microns_per_pixel #return [x,y]
        else:
            return None
    except ET.ParseError:
        print("Error parsing the XML file.")
        return None
    except ValueError:
        print("Error in value format.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None    

def get_imaging_session_duration(directory):
    '''
    Extracts the duration of the imaging session from the XML file.
    Parameters:
    xml_file_path (str): Path to the XML file.
    Returns:
    float: Duration of the imaging session in seconds.
    UPDATE FOR TZSERIES, NOT REPORTING PROPERLY
    '''
        #get list of xml files
    xml_file = get_xml_image(directory)
    if xml_file is None:
        return
    try:
        # Parse the XML file
        tree = ET.parse(xml_file)
        # Get the root of the XML document
        root = tree.getroot()
        # Find all 'Frame' elements
        frames = root.findall('.//Frame')
        if not frames:
            print("No Frame elements found in the XML file.")
            return None
        # Get the last frame
        last_frame = frames[-1]
        # Extract the 'relativeTime' attribute
        duration = float(last_frame.get('relativeTime'))
        return duration
    except ET.ParseError:
        print("Error parsing the XML file.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_imaging_date(directory):
    """
    Extracts the date from the XML metadata file.

    Parameters:
    xml_file_path (str): Path to the XML file.

    Returns:
    str: Date in the format 'YYYY-MM-DD' or None if the date is not found.
    """
    #get list of xml files
    xml_file = get_xml_image(directory)
    if xml_file is None:
        return
    try:
        # Parse the XML file, ignoring namespaces
        tree = ET.iterparse(xml_file, events=['start'])
        for event, elem in tree:
            if elem.tag.endswith('PVScan'):
                date_str = elem.attrib.get('date', None)
                if date_str:
                    date_parts = date_str.split(' ')[0].split('/')
                    formatted_date = '/'.join([date_parts[2], date_parts[0], date_parts[1]])
                    return formatted_date
    except ET.ParseError:
        print("Error parsing the XML file.")
        return None
    except ValueError:
        print("Error in date format.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def check_batch_concat(directory):
    '''
    if there are less than 20 tif files then return true, batch_concat run. 

    '''
    #list all tiff files with 6 digit identifier '######.ome.tif' -> this allows for specificity of which tif files are selected, concatenated and deleted. 
    file_list = glob.glob(os.path.join(directory, '*[0-9][0-9][0-9][0-9][0-9][0-9].ome.tif')) 
    n = len(file_list)  # Record number of tifs
    #print("number of files: " + str(n))
    return (n<20)

def check_double_motion_correct(directory):
    '''
    Parameters
    ----------
    directory : TYPE
        DESCRIPTION.
    Returns
    -------
    list of boolean [T/F,T/F,T/F]
        [if stab 1 exists, if stab 2 exists, if both stab 1 and stab 2 exist]
    '''
    # Use glob to search for files with 'stab 1' and 'stab 2' in their names
    file1_pattern = os.path.join(directory, '*stab 1*.csv')
    file2_pattern = os.path.join(directory, '*stab 2*.csv')

    # Check if files exist
    file1_exists = len(glob.glob(file1_pattern)) > 0
    file2_exists = len(glob.glob(file2_pattern)) > 0
    return [file1_exists, file2_exists, (file1_exists and file2_exists)]

def record_motion_correct_status(parent_dir):
    '''
    input_dir should be a parent directory with a subdirectory for each imaging session 
    the code checks the sequence type and only runs function_ if the seq type is TSeries 
    '''
    results = []
    for root, dirs, files in os.walk(parent_dir):
        for dir in dirs:
            directory = os.path.join(root,dir)            
            seq_type = get_sequence_type(directory)
            #maybe add a column to record session type (T(10),Z(01),TZ(11))
            if seq_type is not None:#sometimes there is no metadata
                #select ONLY TSeries for batch concat by the process_folder() function
                if "TSeries" in seq_type and "ZSeries" not in seq_type:
                    file1_exists, file2_exists, both_exist = check_double_motion_correct(directory)
                    results.append({
                        'Directory Path': directory,
                        'type':'TSeries',
                        'stab 1.csv Exists': file1_exists,
                        'stab 2.csv Exists': file2_exists,
                        'stab 1 and stab 2 Exist': both_exist
                    })
                if "ZSeries" in seq_type and "TSeries" not in seq_type:
                    #z series should not be motion corrected
                    None
                if "TSeries" in seq_type and "ZSeries" in seq_type:
                    file1_exists, file2_exists, both_exist = check_double_motion_correct(directory)
                    results.append({
                        'Directory Path': directory,
                        'type': 'TZSeries',
                        'stab 1.csv Exists': file1_exists,
                        'stab 2.csv Exists': file2_exists,
                        'stab 1 and stab 2 Exist': both_exist
                    })
    return pd.DataFrame(results)   

def check_if_single_frame(directory):
    #copied from get_avg, consolidate functions in future
    # Get list of XML files
    xml_file = get_xml_image(directory)
    if xml_file is None:
        return None
    
    # Parse the XML file
    tree = ET.parse(xml_file)
    # Get the root of the XML document
    root = tree.getroot()
    
    relativeTimes = []
    for frame in root.iter('Frame'):
        relativeTime = frame.attrib.get('relativeTime')
        if relativeTime is not None:
            relativeTimes.append(float(relativeTime))
        if len(relativeTimes) == 2:  # Take only first two recorded points
            return False
    # Check if we have at least two time points
    if len(relativeTimes) < 2:
        print('Only one frame detected')
        return True 

#write helper function to record if manual roi selection has been done.

###TEST CODE
#fp = get_frame_period('/Volumes/T7/Motor_Spines_Pilot_Data/293L/231105/293L_231105_Cell2_dend1_920nm_20x_20xd_Tseries_78um_512px_0Avg-083')
#avg = get_avg('/Volumes/T7/Motor_Spines_Pilot_Data/293L/231105/293L_231105_Cell2_dend1_920nm_20x_20xd_Tseries_78um_512px_0Avg-083')
#file1,file2,test = check_double_motion_correct('/Volumes/T7/Motor_Spines_Pilot_Data/293L/231105/293L_231105_Cell2_dend1_920nm_20x_20xd_Tseries_78um_512px_0Avg-083')
#results = record_motion_correct_status('/Volumes/T7/Motor_Spines_Pilot_Data/289N')
#dur = get_imaging_session_duration('/Volumes/T7/Motor_Spines_Pilot_Data/293L/231105/293L_231105_Cell2_dend1_920nm_20x_20xd_Tseries_78um_512px_0Avg-083')
#date = get_imaging_date('/Volumes/T7/Motor_Spines_Pilot_Data/289N/231101/289N_231101_Cell2_dend2_920nm_10x_20xd_Tseries_96.23um_512px_noAvg-062')
#date2 = get_imaging_date('/Volumes/T7/Motor_Spines_Pilot_Data/289N/231031/289N_231031_920nm_20x_10xd_Tseries_81.5um_512px_4avg-057')
#laser_power = get_laser_power('/Volumes/T7/Motor_Spines_Pilot_Data/289N/231031/289N_231031_920nm_20x_10xd_Tseries_81.5um_512px_4avg-057')
#pmt_gain = get_pmt_gain('/Volumes/T7/Motor_Spines_Pilot_Data/289N/231031/289N_231031_920nm_20x_10xd_Tseries_81.5um_512px_4avg-057', "Ch 2 GaAsP")
#wavelength = get_wavelength('/Volumes/T7/Motor_Spines_Pilot_Data/289N/231031/289N_231031_920nm_20x_10xd_Tseries_81.5um_512px_4avg-057')
#dmc = check_double_motion_correct('/Volumes/T7/Motor_Spines_Pilot_Data/289N/231031/289N_231031_920nm_20x_10xd_Tseries_81.5um_512px_4avg-057')
check_concat = check_batch_concat('/Volumes/T7/Motor_Spines_Pilot_Data/289N/231031/289N_231031_920nm_20x_10xd_Tseries_81.5um_512px_4avg-057')
dur = get_imaging_session_duration('/Volumes/T7/First_Pilot_Data/S15742_gregg/230927/230927_glusnfr_810nm_90.68um_121.53um_step1um_64avg-085')
res = get_resolution('/Volumes/T7/Motor_Spines_Pilot_Data/289N/231031/289N_231031_cell2_920nm_20x_2xd_Zstack_110_140um_1024_512px_4avg-098')
microns = get_microns_per_pixel('/Volumes/T7/Motor_Spines_Pilot_Data/289N/231031/289N_231031_cell2_920nm_20x_2xd_Zstack_110_140um_1024_512px_4avg-098')
obj = get_objective('/Volumes/T7/Motor_Spines_Pilot_Data/289N/231031/289N_231031_cell2_920nm_20x_2xd_Zstack_110_140um_1024_512px_4avg-098')
