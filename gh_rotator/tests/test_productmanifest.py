import unittest
import os
import sys
import shutil
import tempfile
from unittest.mock import patch, MagicMock
from unittest.mock import Mock
from io import StringIO
import pytest

# Setup paths for imports and test data
test_dir = os.path.dirname(os.path.abspath(__file__))
class_path = os.path.join(test_dir, "../classes")
sys.path.append(class_path)

from productconfig import ProductConfig
from productmanifest import ProductManifest

# Define data paths relative to this test file
TEST_DATA_PATH = os.path.join(test_dir, "data")
NO_MANIFESTS_PATH = os.path.join(TEST_DATA_PATH, "no-manifests")
ORIGINAL_MANIFESTS_PATH = os.path.join(TEST_DATA_PATH, "manifests")
BAD_MANIFESTS_PATH = os.path.join(TEST_DATA_PATH, "bad_manifests")


class ManifestTestBase(unittest.TestCase):
    """Base class for tests that need to work with manifest files.

    This base class provides a temporary directory containing copies of the
    original manifest files. Tests can modify these copies without affecting
    the original files. The temporary directory is automatically cleaned up
    after each test.
    """

    def setUp(self):
        """Set up test variables before each test"""
        # Create a temporary directory for manifest files
        self.temp_dir = tempfile.mkdtemp()
        self.MANIFESTS_PATH = os.path.join(self.temp_dir, "manifests")

        # Copy the original manifest directory structure
        if os.path.exists(ORIGINAL_MANIFESTS_PATH):
            shutil.copytree(ORIGINAL_MANIFESTS_PATH, self.MANIFESTS_PATH)

    def tearDown(self):
        """Clean up after each test"""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)


class TestProject(ManifestTestBase):
    def setUp(self):
        """Set up test variables before each test"""
        super().setUp()
        self.valid_config_path = os.path.join(TEST_DATA_PATH, "config-rotator-valid.json")
        self.invalid_config_path = os.path.join(TEST_DATA_PATH, "config-rotator-invalid.json")

    @pytest.mark.unittest
    def test_load_empty_manifest_success(self):
        config = ProductConfig(file=self.valid_config_path)
        manifest = ProductManifest(config, directory=NO_MANIFESTS_PATH)

        # Assertions
        self.assertIsInstance(manifest.get("dev_manifest"), dict)
        self.assertIsInstance(manifest.get("prod_manifest"), dict)
        self.assertIsInstance(manifest.get("qa_manifest"), dict)

    @pytest.mark.unittest
    def test_load_manifest_bad_json(self):
        valid_config_path = os.path.join(TEST_DATA_PATH, "config-rotator-valid.json")
        config = ProductConfig(file=self.valid_config_path)

        # Use a context manager to capture stderr output
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                manifest = ProductManifest(config, directory=BAD_MANIFESTS_PATH)

    @pytest.mark.unittest
    def test_load_manifest_from_alternate_source(self):
        config = ProductConfig(file=self.valid_config_path)
        manifest = ProductManifest(config, directory=self.MANIFESTS_PATH)

        # Assertions
        self.assertIsInstance(manifest.get("dev_manifest"), dict)
        self.assertIsInstance(manifest.get("prod_manifest"), dict)
        self.assertIsInstance(manifest.get("qa_manifest"), dict)

    @pytest.mark.unittest
    def test_rotate_manifest_dev_success(self):
        config = ProductConfig(file=self.valid_config_path)
        manifest = ProductManifest(config, directory=self.MANIFESTS_PATH)
        manifest.rotate(
            event_type="branch",
            event_name="main",
            repo="config-rotator/backend-component",
            sha="1a0b35a3cf0416b9ae8017509941334608243840",
        )

        # Assertions
        self.assertIsInstance(manifest.get("dev_manifest"), dict)
        self.assertIsInstance(manifest.get("prod_manifest"), dict)
        self.assertIsInstance(manifest.get("qa_manifest"), dict)
        self.assertEqual(
            manifest.get("dev_manifest")["dev"][0]["repo"], "config-rotator/iac-component"
        )
        self.assertEqual(
            manifest.get("dev_manifest")["dev"][1]["repo"], "config-rotator/frontend-component"
        )
        self.assertEqual(
            manifest.get("dev_manifest")["dev"][2]["repo"], "config-rotator/backend-component"
        )
        self.assertEqual(
            manifest.get("dev_manifest")["dev"][2]["repo"], "config-rotator/backend-component"
        )
        self.assertEqual(
            manifest.get("dev_manifest")["dev"][2]["version"],
            "1a0b35a3cf0416b9ae8017509941334608243840",
        )
        self.assertEqual(manifest.get("dev_manifest")["dev"][2]["ref_name"], "main")
        self.assertEqual(manifest.get("dev_manifest")["dev"][2]["ref_type"], "branch")

    @pytest.mark.unittest
    def test_rotate_manifest_qa_success(self):
        config = ProductConfig(file=self.valid_config_path)
        manifest = ProductManifest(config, directory=self.MANIFESTS_PATH)
        manifest.rotate(
            event_type="tag",
            event_name="1.0.34rc",
            repo="config-rotator/backend-component",
            sha="1a0b35a3cf0416b9ae8017509941334608243840",
        )

        # Assertions
        self.assertEqual(
            manifest.get("qa_manifest")["qa"][2]["repo"], "config-rotator/backend-component"
        )
        self.assertEqual(
            manifest.get("qa_manifest")["qa"][2]["version"],
            "1a0b35a3cf0416b9ae8017509941334608243840",
        )
        self.assertEqual(manifest.get("qa_manifest")["qa"][2]["ref_name"], "1.0.34rc")
        self.assertEqual(manifest.get("qa_manifest")["qa"][2]["ref_type"], "tag")

    @pytest.mark.unittest
    def test_rotate_manifest_prod_success(self):
        config = ProductConfig(file=self.valid_config_path)
        manifest = ProductManifest(config, directory=self.MANIFESTS_PATH)
        manifest.rotate(
            event_type="tag",
            event_name="1.0.0",
            repo="config-rotator/backend-component",
            sha="1a0b35a3cf0416b9ae8017509941334608243840",
        )

        # Assertions
        self.assertEqual(
            manifest.get("prod_manifest")["prod"][2]["repo"], "config-rotator/backend-component"
        )
        self.assertEqual(
            manifest.get("prod_manifest")["prod"][2]["version"],
            "1a0b35a3cf0416b9ae8017509941334608243840",
        )
        self.assertEqual(manifest.get("prod_manifest")["prod"][2]["ref_name"], "1.0.0")
        self.assertEqual(manifest.get("prod_manifest")["prod"][2]["ref_type"], "tag")

    @pytest.mark.unittest
    def test_rotate_manifest_bad_repo(self):
        config = ProductConfig(file=self.valid_config_path)
        manifest = ProductManifest(config, directory=self.MANIFESTS_PATH)

        # Capture stderr and check for error message
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                manifest.rotate(
                    event_type="tag",
                    event_name="1.0.0",
                    repo="config-rotator/blaha-component",
                    sha="1a0b35a3cf0416b9ae8017509941334608243840",
                )

            # Get the captured stderr content
            stderr_output = mock_stderr.getvalue()

            # Check the stderr message
            self.assertRegex(
                stderr_output,
                r"Error: No matching configuration found for repo 'config-rotator/blaha-component', event_type 'tag', and event_name '1.0.0'",
            )
            self.assertEqual(cm.exception.code, 1)

    @pytest.mark.unittest
    def test_get_version_success(self):
        config = ProductConfig(file=self.valid_config_path)
        manifest = ProductManifest(config, directory=self.MANIFESTS_PATH)
        sha1 = manifest.get_version(configuration="dev", repo="config-rotator/backend-component")
        self.assertRegex(sha1, r"[0-9a-f]{7,40}")
