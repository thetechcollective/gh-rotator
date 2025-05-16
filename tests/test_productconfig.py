import unittest
import os
import sys
from unittest.mock import patch, MagicMock
from unittest.mock import Mock
from io import StringIO
import pytest

class_path = os.path.dirname(os.path.abspath(__file__)) + "/../classes"
sys.path.append(class_path)

from productconfig import ProductConfig

class TestProject(unittest.TestCase):

    @pytest.mark.unittest
    def test_load_config_success(self):
        config = ProductConfig(file = './tests/data/config-rotator-valid.json')
        # Assertions
        self.assertRegex(config.get("config_file"), r"config-rotator-valid.json")

    @pytest.mark.unittest
    def test_load_explicit_config_success(self):
        config = ProductConfig(file = './tests/data/config-rotator-valid.json')
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
                config = ProductConfig(file="./tests/data/config-rotator-invalid.json")
            # Get the captured stderr content
            stderr_output = mock_stderr.getvalue()

            # Check the stderr message
            self.assertRegex(stderr_output, r"Error: Config file .* is not a valid JSON file")   
            self.assertEqual(cm.exception.code, 1)
