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
        config = ProductConfig(file=self.valid_config_path)
        # Assertions
        self.assertRegex(config.get("config_file"), r"config-rotator-valid.json")

    @pytest.mark.unittest
    def test_load_explicit_config_success(self):
        config = ProductConfig(file=self.valid_config_path)
        # Assertions
        self.assertRegex(config.get("config_file"), r"config-rotator-valid.json")

    @pytest.mark.unittest
    def test_load_explicit_config_failure(self):
        # Assertions
        # capture stderr and check for error message
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                config = ProductConfig(file="blaha.json")
            stderr_output = mock_stderr.getvalue()
            self.assertRegex(stderr_output, "Error: Config file .* not found")
            self.assertEqual(cm.exception.code, 1)

    @pytest.mark.unittest
    def test_load_invalid_config_failure(self):
        # Capture stderr and check for error message
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                config = ProductConfig(file=self.invalid_config_path)
            # Get the captured stderr content
            stderr_output = mock_stderr.getvalue()

            # Check the stderr message
            self.assertRegex(stderr_output, r"Error: Config file .* is not a valid JSON file")
            self.assertEqual(cm.exception.code, 1)

    @pytest.mark.unittest
    @patch("subprocess.check_output")
    @patch("os.path.exists")
    def test_default_config_repo_root(self, mock_exists, mock_check_output):
        """Test that the default config file is found in the repo root"""
        # Mock git command to return a fake repo root
        mock_check_output.return_value = b"/fake/path"

        # Make it seem like the config file exists in repo root but not in the fallback location
        def mock_exists_impl(path):
            if path == "/fake/path/config-rotator.json":
                return True
            return False

        mock_exists.side_effect = mock_exists_impl

        # Mock the file opening and json parsing
        with patch("builtins.open", create=True) as mock_open:
            mock_file = mock_open.return_value.__enter__.return_value
            mock_file.read.return_value = "{}"
            with patch("json.load", return_value={}):
                # Initialize with no explicit config file path
                config = ProductConfig()

                # Check that it found the config in the repo root
                self.assertEqual(config.get("config_file"), "/fake/path/config-rotator.json")

    @pytest.mark.unittest
    @patch("subprocess.check_output")
    @patch("os.path.exists")
    @patch("os.path.dirname")
    def test_default_config_fallback(self, mock_dirname, mock_exists, mock_check_output):
        """Test fallback to the built-in default config"""
        # Mock git command to return a fake repo root
        mock_check_output.return_value = b"/fake/path"

        # Configure dirname for the fallback path construction
        mock_dirname.side_effect = ["/fake/path/classes", "/fake/path"]

        # Make it seem like the config file doesn't exist in repo root but does in fallback
        def mock_exists_impl(path):
            if path == "/fake/path/config-rotator.json":
                return False
            elif path == "/fake/path/config/config-rotator.json":
                return True
            return False

        mock_exists.side_effect = mock_exists_impl

        # Mock the file opening and json parsing
        with patch("builtins.open", create=True) as mock_open:
            mock_file = mock_open.return_value.__enter__.return_value
            mock_file.read.return_value = "{}"
            with patch("json.load", return_value={}):
                # Initialize with no explicit config file path
                config = ProductConfig()

                # Check that it found the config in the fallback location
                self.assertEqual(config.get("config_file"), "/fake/path/config/config-rotator.json")

    @pytest.mark.unittest
    @patch("subprocess.check_output")
    @patch("os.path.exists")
    def test_no_default_config_found(self, mock_exists, mock_check_output):
        """Test error when no default config is found"""
        # Mock git command to return a fake repo root
        mock_check_output.return_value = b"/fake/path"

        # Make it seem like no config file exists anywhere
        mock_exists.return_value = False

        # Capture stderr and check for error message
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                config = ProductConfig()

            # Get the captured stderr content
            stderr_output = mock_stderr.getvalue()

            # Check the stderr message
            self.assertRegex(stderr_output, r"Error: No configuration file found")
            self.assertEqual(cm.exception.code, 1)
