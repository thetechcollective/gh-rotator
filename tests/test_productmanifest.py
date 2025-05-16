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
    def test_load_empty_manifest_success(self):
        config = ProductConfig(file="./tests/data/config-rotator-valid.json")
        manifest = ProductManifest(config, directory="./tests/data/no-manifests")
        
        # Assertions
        self.assertIsInstance(manifest.get("dev_manifest"), dict)
        self.assertIsInstance(manifest.get("prod_manifest"), dict)
        self.assertIsInstance(manifest.get("qa_manifest"), dict)

    @pytest.mark.unittest
    def test_load_manifest_bad_json(self):
        config = ProductConfig(file="./tests/data/config-rotator-valid.json")
        
        # Capture stderr and check for error message
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                manifest = ProductManifest(config, directory="./tests/data/bad_manifests")

            # Get the captured stderr content
            stderr_output = mock_stderr.getvalue()

            # Check the stderr message
            self.assertRegex(stderr_output, r"Error: Manifest file .* is not a valid JSON file")   
            self.assertEqual(cm.exception.code, 1)

    @pytest.mark.unittest
    def test_load_manifest_from_alternate_source(self):
        config = ProductConfig(file="./tests/data/config-rotator-valid.json")
        manifest = ProductManifest(config, directory="./tests/data/manifests")

        # Assertions
        self.assertIsInstance(manifest.get("dev_manifest"), dict)
        self.assertIsInstance(manifest.get("prod_manifest"), dict)
        self.assertIsInstance(manifest.get("qa_manifest"), dict)
        
    @pytest.mark.unittest
    def test_rotate_manifest_dev_success(self):
        config = ProductConfig(file="./tests/data/config-rotator-valid.json")
        manifest = ProductManifest(config, directory="./tests/data/manifests")
        manifest.rotate(
            event_type="branch",
            event_name="main",
            repo="config-rotator/backend-component",
            sha="1a0b35a3cf0416b9ae8017509941334608243840")
        
        # Assertions
        self.assertIsInstance(manifest.get("dev_manifest"), dict)
        self.assertIsInstance(manifest.get("prod_manifest"), dict) 
        self.assertIsInstance(manifest.get("qa_manifest"), dict)
        self.assertEqual(manifest.get("dev_manifest")["dev"][0]["repo"],"config-rotator/iac-component")
        self.assertEqual(manifest.get("dev_manifest")["dev"][1]["repo"],"config-rotator/frontend-component")
        self.assertEqual(manifest.get("dev_manifest")["dev"][2]["repo"],"config-rotator/backend-component")
        self.assertEqual(manifest.get("dev_manifest")["dev"][2]["repo"],"config-rotator/backend-component")
        self.assertEqual(manifest.get("dev_manifest")["dev"][2]["version"],"1a0b35a3cf0416b9ae8017509941334608243840")
        self.assertEqual(manifest.get("dev_manifest")["dev"][2]["ref_name"],"main")
        self.assertEqual(manifest.get("dev_manifest")["dev"][2]["ref_type"],"branch")
        
    @pytest.mark.unittest
    def test_rotate_manifest_qa_success(self):
        config = ProductConfig(file="./tests/data/config-rotator-valid.json")
        manifest = ProductManifest(config, directory="./tests/data/manifests")
        manifest.rotate(
            event_type="tag",
            event_name="1.0.34rc",
            repo="config-rotator/backend-component",
            sha="1a0b35a3cf0416b9ae8017509941334608243840")
        
        # Assertions
        self.assertEqual(manifest.get("qa_manifest")["qa"][2]["repo"],"config-rotator/backend-component")
        self.assertEqual(manifest.get("qa_manifest")["qa"][2]["version"],"1a0b35a3cf0416b9ae8017509941334608243840")
        self.assertEqual(manifest.get("qa_manifest")["qa"][2]["ref_name"],"1.0.34rc")
        self.assertEqual(manifest.get("qa_manifest")["qa"][2]["ref_type"],"tag")

    @pytest.mark.unittest
    def test_rotate_manifest_prod_success(self):
        config = ProductConfig(file="./tests/data/config-rotator-valid.json")
        manifest = ProductManifest(config, directory="./tests/data/manifests")
        manifest.rotate(
            event_type="tag",
            event_name="1.0.0",
            repo="config-rotator/backend-component",
            sha="1a0b35a3cf0416b9ae8017509941334608243840")
        
        # Assertions
        self.assertEqual(manifest.get("prod_manifest")["prod"][2]["repo"],"config-rotator/backend-component")
        self.assertEqual(manifest.get("prod_manifest")["prod"][2]["version"],"1a0b35a3cf0416b9ae8017509941334608243840")
        self.assertEqual(manifest.get("prod_manifest")["prod"][2]["ref_name"],"1.0.0")
        self.assertEqual(manifest.get("prod_manifest")["prod"][2]["ref_type"],"tag")


    @pytest.mark.unittest
    def test_rotate_manifest_bad_repo(self):
        config = ProductConfig(file="./tests/data/config-rotator-valid.json")
        manifest = ProductManifest(config, directory="./tests/data/manifests")
        
        # Capture stderr and check for error message
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                manifest.rotate(
                    event_type="tag",
                    event_name="1.0.0",
                    repo="config-rotator/blaha-component",
                    sha="1a0b35a3cf0416b9ae8017509941334608243840")

            # Get the captured stderr content
            stderr_output = mock_stderr.getvalue()

            # Check the stderr message
            self.assertRegex(stderr_output, r"Error: No matching configuration found for repo 'config-rotator/blaha-component', event_type 'tag', and event_name '1.0.0'")   
            self.assertEqual(cm.exception.code, 1)    

    @pytest.mark.unittest
    def test_get_version_success(self):
        config = ProductConfig(file="./tests/data/config-rotator-valid.json")
        manifest = ProductManifest(config, directory="./tests/data/manifests")
        sha1 = manifest.get_version(
            configuration="dev",
            repo="config-rotator/backend-component")
        self.assertRegex(sha1, r"[0-9a-f]{7,40}")