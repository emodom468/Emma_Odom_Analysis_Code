#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  9 22:20:22 2024

@author: emmaodom

make sure to go to terminal and type 
conda activate /Users/emmaodom/opt/anaconda3
to ensure localizability of packages. 
"""

import imagej
import scyjava

#To change the memory capacity, you need to restart kernel (command + .)
scyjava.config.add_options('-Xmx14g')

def batch_motion_correct_IMJ_macro(file_path):
    # Initialize ImageJ to local installation
    ij = imagej.init('sc.fiji:fiji') #imagej.init('/Applications/Fiji.app')
    
    # Path to macro .ijm
    macro_path = "/Volumes/T7/Analysis_code/macros/test_function.ijm"

    # Read the contents of the macro file
    with open(macro_path, 'r') as file:
        macro = file.read()

    # Run the macro with the file path as an argument
    ij.py.run_macro(macro, file_path)
    
    # Print version and memory info
    # print(f"ImageJ version: {ij.getVersion()}")
    print(ij.getApp().getInfo(True))
    
    # Deinitialize ImageJ
    # ij.getContext().dispose()


image_path = "/Volumes/T7/Motor_Spines_Pilot_Data/289N/231030/289N_231030_920nm_20x_10xd_Tseries_59.53um_512_512px_4avg-055/MoCorr1_AVG_289N_231030_920nm_20x_10xd_Tseries_59.53um_512_512px_4avg-055-Ch2.tif" 
batch_motion_correct_IMJ_macro(image_path)












#SO FAR THE MACRO INTEGRATION DOESNT WORK AT ALLLLLL
'''
def run_imagej_macro(filePath):
    # Initialize ImageJ
    ij = imagej.init('/Applications/Fiji.app')  # 'sc.fiji:fiji' Adjust the path to your local Fiji installation if needed

    # Path to the .ijm file
    macro_path = "/Volumes/T7/Analysis_code/macros/test_function.ijm"

    # Read the macro file
    with open(macro_path, 'r') as macro_file:
        macro = macro_file.read()

    # Run the macro with filePath as an argument
    ij.py.run_macro(macro, {'filePath': filePath})

    # Optionally, interact with the ImageJ window to view results
    input("Press Enter to close ImageJ...")
    ij.dispose()

# Replace with the path to your image file
image_path = "/Volumes/T7/Motor_Spines_Pilot_Data/289N/231030/289N_231030_920nm_20x_10xd_Tseries_59.53um_512_512px_4avg-055/MoCorr1_AVG_289N_231030_920nm_20x_10xd_Tseries_59.53um_512_512px_4avg-055-Ch2.tif"  
run_imagej_macro(image_path)

'''

#import sys
#print(sys.executable)
#active environemtn /Users/emmaodom/opt/anaconda3/bin/python 

#imagej installed in 
#imagej library path: /Users/emmaodom/opt/miniconda3/lib/python3.10/site-packages
#import sys can try this!
#sys.path.append('/Users/emmaodom/opt/miniconda3/lib/python3.10/site-packages')
