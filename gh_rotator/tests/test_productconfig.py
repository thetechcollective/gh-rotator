import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch

import pytest

# Setup paths for imports and test data
test_dir = os.path.dirname(os.path.abspath(__file__))
class_path = os.path.join(test_dir, "../classes")
sys.path.append(class_path)

# Define data path relative to this test file
TEST_DATA_PATH = os.path.join(test_dir, "data")

from productconfig import ProductConfig


class TestProject(unittest.TestCase):
    
    def setUp(self):
        """Set up test variables before each test"""
        self.valid_config_path = os.path.join(TEST_DATA_PATH, "config-rotator-valid.json")
        self.invalid_config_path = os.path.join(TEST_DATA_PATH, "config-rotator-invalid.json")

    @pytest.mark.unittest
    def test_load_config_success(self):
        config = ProductConfig(file = self.valid_config_path)
        # Assertions
        self.assertRegex(config.get("config_file"), r"config-rotator-valid.json")

    @pytest.mark.unittest
    def test_load_explicit_config_success(self):
        config = ProductConfig(file = self.valid_config_path)
        # Assertions
        self.assertRegex(config.get("config_file"), r"config-rotator-valid.json")
 
    @pytest.mark.unittest
    def test_load_explicit_config_failure(self):
        # Assertions
        # capture stderr and check for error message
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                config = ProductConfig(file="blaha.json")
            stderr_output = mock_stderr.getvalue()
            self.assertRegex(stderr_output, "Error: Config file .* not found")
            self.assertEqual(cm.exception.code, 1)
            
    @pytest.mark.unittest
    def test_load_invalid_config_failure(self):
        # Capture stderr and check for error message
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                config = ProductConfig(file=self.invalid_config_path)
            # Get the captured stderr content
            stderr_output = mock_stderr.getvalue()

            # Check the stderr message
            self.assertRegex(stderr_output, r"Error: Config file .* is not a valid JSON file")   
            self.assertEqual(cm.exception.code, 1)
