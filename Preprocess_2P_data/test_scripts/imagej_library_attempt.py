#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  9 22:20:22 2024

@author: emmaodom
"""


#imagej library path: /Users/emmaodom/opt/miniconda3/lib/python3.10/site-packages
import imagej

def run_imagej_macro(filePath):
    # Initialize ImageJ
    ij = imagej.init('sc.fiji:fiji')  # Adjust the path to your local Fiji installation if needed

    # Path to the .ijm file
    macro_path = "/Volumes/T7/Analysis_code/macros/test_function.ijm"

    # Load and run the macro file with the file path as an argument
    with open(macro_path, 'r') as macro_file:
        macro = macro_file.read()

    ij.script().run('your_macro.ijm', macro, True, ij.py.to_java([filePath])).get()

    # Optionally, interact with the ImageJ window to view results
    input("Press Enter to close ImageJ...")
    ij.dispose()

# Example usage
image_path = "/path/to/your/image.tif"  # Replace with the path to your image file
run_imagej_macro(image_path)


