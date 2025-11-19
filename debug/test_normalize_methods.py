"""
Test script for text normalization methods
It uses sample text and runs the normnalize functions to display the final results.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils.text_utils as text_utils

inputs = ["iPad Pro (11\")(2nd generation)", "iPad Pro (10.5\")"]

for input in range (len(inputs)):
    after_display_normalized = text_utils.normalize_for_display(name=inputs[input])
    print(f"Display normalized: '{after_display_normalized}'")
   
    after_comparison_normalized = text_utils.normalize_for_comparison(text=inputs[input])
    print(f"Comparison normalized: '{after_comparison_normalized}'")
          
