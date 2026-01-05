#!/usr/bin/env python3
import unittest
import sys
import json
import shutil
import tempfile
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure the project root is in sys.path so we can import the module
BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from proxmox_soc.snipe_it.snipe_scripts.log.snipe_snapshotter import AssetSnapshotter

class TestAssetSnapshotter(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary directory for test outputs
        self.test_dir = tempfile.mkdtemp()
        self.test_dir_path = Path(self.test_dir)

    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)

    @patch("proxmox_soc.snipe_it.snipe_scripts.log.snipe_snapshotter.AssetService")
    @patch("proxmox_soc.snipe_it.snipe_scripts.log.snipe_snapshotter.os.makedirs")
    @patch("pathlib.Path.mkdir")
    def test_take_snapshot(self, mock_mkdir, mock_makedirs, MockAssetService):
        """
        Test that take_snapshot fetches assets and writes them to a file.
        """
        # Setup Mock AssetService to return fake data
        mock_service = MockAssetService.return_value
        fake_assets = [
            {"id": 1, "asset_tag": "TAG-001", "name": "Laptop"},
            {"id": 2, "asset_tag": "TAG-002", "name": "Server"}
        ]
        mock_service.get_all.return_value = fake_assets

        # Initialize Snapshotter
        # Note: __init__ calls mkdir, which is mocked here to prevent side effects on real folders
        snapshotter = AssetSnapshotter()
        
        # Redirect snapshot_dir to our temp dir for the actual write test
        snapshotter.snapshot_dir = self.test_dir_path

        # Execute
        filename = "test_output.json"
        output_path = snapshotter.take_snapshot(filename=filename)

        # Verify API call
        mock_service.get_all.assert_called_once_with(limit=10000, refresh_cache=True)

        # Verify file exists and content matches
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, "r") as f:
            content = json.load(f)
        
        self.assertEqual(content, fake_assets)

    @patch("proxmox_soc.snipe_it.snipe_scripts.log.snipe_snapshotter.AssetService")
    @patch("proxmox_soc.snipe_it.snipe_scripts.log.snipe_snapshotter.os.makedirs")
    @patch("pathlib.Path.mkdir")
    def test_load_snapshot(self, mock_mkdir, mock_makedirs, MockAssetService):
        """
        Test that load_snapshot reads assets from a file correctly.
        """
        # Prepare a dummy snapshot file in the temp dir
        fake_data = [{"id": 100, "name": "Restored Asset"}]
        filename = "restore_test.json"
        file_path = self.test_dir_path / filename
        
        with open(file_path, "w") as f:
            json.dump(fake_data, f)

        # Initialize
        snapshotter = AssetSnapshotter()
        snapshotter.snapshot_dir = self.test_dir_path

        # Execute
        loaded_data = snapshotter.load_snapshot(filename)

        # Verify
        self.assertEqual(loaded_data, fake_data)

if __name__ == "__main__":
    unittest.main()