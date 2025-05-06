import unittest
import os
import sys
from unittest.mock import patch, MagicMock
from unittest.mock import Mock
from io import StringIO
import pytest

class_path = os.path.dirname(os.path.abspath(__file__)) + "/../classes"
sys.path.append(class_path)

from productmanifest import ProductManifest
from productconfig import ProductConfig

class TestProject(unittest.TestCase):

    @pytest.mark.unittest
    def test_load_manifest_success(self):
        config = ProductConfig()
        manifest = ProductManifest(config)
        
        # Assertions
        self.assertIsInstance(manifest.get("dev_manifest"), dict)
        self.assertIsInstance(manifest.get("prod_manifest"), dict)
        self.assertIsInstance(manifest.get("qa_manifest"), dict)

    @pytest.mark.unittest
    def test_load_manifest_bad_json(self):
        config = ProductConfig()
        
        # Capture stderr and check for error message
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                manifest = ProductManifest(config, directory="tests/data/bad_manifests")

            # Get the captured stderr content
            stderr_output = mock_stderr.getvalue()

            # Check the stderr message
            self.assertRegex(stderr_output, r"Error: Manifest file .* is not a valid JSON file")   
            self.assertEqual(cm.exception.code, 1)

    @pytest.mark.unittest
    def test_load_manifest_from_alternate_source(self):
        config = ProductConfig()
        manifest = ProductManifest(config, directory="tests/data/manifests")

        # Assertions
        self.assertIsInstance(manifest.get("dev_manifest"), dict)
        self.assertIsInstance(manifest.get("prod_manifest"), dict)
        self.assertIsInstance(manifest.get("qa_manifest"), dict)
        
    @pytest.mark.unittest
    def test_rotate_manifest_success(self):
        config = ProductConfig()
        manifest = ProductManifest(config)
        manifest.rotate(
            configuration="dev",
            repo="thetechcollective/gh-tt",
            sha1="367127575123de",
            event="main/LATEST")
        
        # Assertions
        self.assertIsInstance(manifest.get("dev_manifest"), dict)
        self.assertIsInstance(manifest.get("prod_manifest"), dict)
        self.assertIsInstance(manifest.get("qa_manifest"), dict)        
        

    @pytest.mark.unittest
    def test_rotate_manifest_bad_repo(self):
        config = ProductConfig()
        manifest = ProductManifest(config)
        
        # Capture stderr and check for error message
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                        manifest.rotate(
                            configuration="dev",
                            repo="blaha",
                            sha1="367127575123de",
                            event="main/LATEST")

            # Get the captured stderr content
            stderr_output = mock_stderr.getvalue()

            # Check the stderr message
            self.assertRegex(stderr_output, r"Error: Repository .* not found in configuration .*")   
            self.assertEqual(cm.exception.code, 1)    

    @pytest.mark.unittest
    def test_get_version_success(self):
        config = ProductConfig()
        manifest = ProductManifest(config)
        sha1 = manifest.get_version(
            configuration="dev",
            repo="thetechcollective/gh-tt")
        self.assertRegex(sha1, r"[0-9a-f]{7,40}")