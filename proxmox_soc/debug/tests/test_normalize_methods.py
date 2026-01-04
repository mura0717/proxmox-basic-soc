"""
Test script for text normalization methods
It uses sample text and runs the normnalize functions to display the final results.
"""

import proxmox_soc.utils.text_utils as text_utils

inputs = ["TL-SG108PE.Diabetes.local"]

for input in range (len(inputs)):
    after_display_normalized = text_utils.normalize_for_display(name=inputs[input])
    print(f"Display normalized: '{after_display_normalized}'")
   
    after_comparison_normalized = text_utils.normalize_for_comparison(text=inputs[input])
    print(f"Comparison normalized: '{after_comparison_normalized}'")
          
