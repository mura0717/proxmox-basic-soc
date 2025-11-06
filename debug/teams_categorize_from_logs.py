#!/usr/bin/env python3
"""
Debug script to quickly check if assets are categorized correctly 
It doesn't need to Teams or Snipe-It via API since it uses raw_intune_log.txt file.
"""

import os
import sys
import json
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assets_sync_library.asset_categorizer import AssetCategorizer

class TeamsDebugCategorization:
    pass

teams_debug_categorization = TeamsDebugCategorization()