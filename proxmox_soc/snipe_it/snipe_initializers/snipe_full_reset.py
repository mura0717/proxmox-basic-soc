#!/usr/bin/env python3

"""
Master Reset Script for Snipe-IT Configuration

This script performs a complete and safe reset of the Snipe-IT environment
by deleting entities in the correct order of dependency, purging them,
and then running the clean setup.

Order of Operations:
1. Delete ALL assets (removes dependency on models).
2. Delete ALL models (removes dependency on fieldsets, categories, manufacturers).
3. Run the clean_setup.py script in 'reset' mode, which will:
   a. Clean up remaining entities (fieldsets, fields, etc.).
   b. Purge all soft-deleted records from the database.
   c. Set up all entities from scratch based on snipe_schema.py.
"""

import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

def print_step(message):
    """Prints a formatted step header."""
    print("\n" + "=" * 60)
    print(f" {message}")
    print("=" * 60)

def run_script(script_path: str):
    """Runs a given Python script and checks for errors."""
    print(f"-> Executing: {os.path.basename(script_path)}")
    try:
        subprocess.run([sys.executable, script_path], check=True, text=True)
        print(f"✓ Successfully executed {os.path.basename(script_path)}")
    except subprocess.CalledProcessError as e:
        print(f"✗ ERROR: Failed to execute {os.path.basename(script_path)}.")
        print(f"   Return Code: {e.returncode}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"✗ ERROR: Script not found at {script_path}")
        sys.exit(1)

if __name__ == "__main__":

    print_step("STEP 1: Deleting all existing assets")
    run_script(os.path.join(BASE_DIR, "snipe_it", "snipe_scripts", "delete", "delete_all_assets.py"))

    print_step("STEP 2: Running the main cleanup and setup process")
    run_script(os.path.join(BASE_DIR, "snipe_it", "snipe_initializers", "snipe_setup.py"))

    print("\n✅ Full reset and setup process completed successfully!")
