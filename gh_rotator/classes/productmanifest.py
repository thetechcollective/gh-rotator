
import datetime
import json
import os
import subprocess
import sys
import time

from gh_rotator.classes.productconfig import ProductConfig
from gh_rotator.classes.lazyload import Lazyload


class ProductManifest(Lazyload):
    """Class used to load and represent the product config (defaults to product-rotator.json in the repo root)"""

    def __init__(self, config=ProductConfig, directory=None):
        super().__init__()

        self.set('config', config)

        # make sure we're in a git context, capture the git repo root
        # and set the config_dir to the root of the git repo
        try:
            self.set('git_root', subprocess.check_output(
                ['git', 'rev-parse', '--show-toplevel']).decode('utf-8').strip())
        except subprocess.CalledProcessError:
            print("⛔️ Error: Not in a git repository. Please run this script from a git repository.", file=sys.stderr)
            sys.exit(1)

        if directory is None:
            directory = "configurations"
        self.set('configuration_dir', os.path.join(
            self.get('git_root'), directory))

        # for each configuration, in the config, add the filepath to the corresponting manifest
        for configuration in config.get('config').keys():
            file = os.path.join(self.get(
                'configuration_dir'), configuration, f"config-{configuration}-manifest.json")
            self.set(f'{configuration}_file', file)

            # Load the config file
            self.__load_manifest(configuration)

    def __save_manifest(self, configuration=str):
        """Save the manifest of the corresponding configuration to disk"""

        file_path = self.get(f"{configuration}_file")

        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(self.get(f"{configuration}_file"), 'w') as f:
                json.dump(self.get(f"{configuration}_manifest"), f, indent=4)
        except Exception as e:
            print(
                f"⛔️ Error: Failed to save manifest for {configuration}: {e!s}", file=sys.stderr)
            sys.exit(1)

    def __load_manifest(self, configuration=str):
        """Load the maifest from manifest files or configuration"""

        # If no manifest file exists, create an empty configuration
        if not os.path.exists(self.get(f"{configuration}_file")):
            # Create an empty manifest with just the configuration key and an empty array
            manifest_data = {configuration: []}
            self.set(f'{configuration}_manifest', manifest_data)

        else:
            # The manifest already exist - Load it file
            try:
                with open(self.get(f"{configuration}_file")) as f:
                    self.set(f"{configuration}_manifest", json.load(f))
            except json.JSONDecodeError:
                print(f"⛔️ Error: Manifest file {self.get(f"{configuration}_file")
                                                 } is not a valid JSON file", file=sys.stderr)
                sys.exit(1)

    def rotate(self, repo=str, event_name=str, event_type=str, sha=str, verbose=False):
        """Rotate the manifest for the given configuration

        Args:
            repo (str): The fully qualified name (owner/repo) of the repo that fired the event
            event_name (str): The event name that triggered the run (branch or tag name)
            event_type (str): The event type that triggered the run (branch|tag)
            sha (str): The sha to set for the repo in the manifest
            verbose (bool, optional): Whether to print verbose output. Defaults to False.
        Returns:
            configuration (str): The configuration name that was rotated (None if failed)
        """
        # The constructor already loaded the manifests, so were good to assume it's healthy

        configuration = self.get('config').get_config_name(
            repo, event_name, event_type, verbose)

        # Create entry data function to avoid code duplication
        def create_entry():
            now = datetime.datetime.now().strftime(
                f"%Y-%m-%d (%H:%M:%S) [{time.strftime("%Z")}]")
            return {
                "repo": repo,
                "version": sha,
                "ref_type": event_type,
                "ref_name": event_name,
                "last_update": now
            }

        # Check if the repo exists in the manifest
        found = False
        try:
            # First, try to find and update the repository if it exists
            for entry in self.get(f"{configuration}_manifest")[configuration]:
                if entry["repo"] == repo:
                    # Update the entry
                    now = datetime.datetime.now().strftime(
                        f"%Y-%m-%d (%H:%M:%S) [{time.strftime("%Z")}]")
                    entry["version"] = sha
                    entry["ref_type"] = event_type
                    entry["ref_name"] = event_name
                    entry["last_update"] = now
                    if verbose:
                        print(
                            f"Rotating {repo} in {configuration} manifest with version {sha} triggered by event: {event_type}")
                    found = True
                    break

            # If repository not found, add it to the manifest
            if not found:
                new_entry = create_entry()
                self.get(f"{configuration}_manifest")[
                    configuration].append(new_entry)
                if verbose:
                    print(
                        f"Adding {repo} to {configuration} manifest with version {sha} triggered by event: {event_type}")

        except AssertionError:
            print(
                f"⛔️ Error: The configuration '{configuration}' is not valid.", file=sys.stderr)
            sys.exit(1)
        except KeyError:
            # If the configuration key doesn't exist, create it
            new_entry = create_entry()
            self.get(f"{configuration}_manifest")[configuration] = [new_entry]
            if verbose:
                print(
                    f"Created {configuration} configuration and added {repo} with version {sha}")

        # Write the updated manifest back to the file
        # Check if the file exists and run __save_manifest if it doesn't
        if not os.path.exists(self.get(f"{configuration}_file")):
            self.__save_manifest(configuration)

        with open(self.get(f"{configuration}_file"), 'w') as f:
            json.dump(self.get(f'{configuration}_manifest'), f, indent=4)
            if verbose:
                manifest_file = self.get(f"{configuration}_file")
                print(
                    f"The file '{manifest_file}' is updated with content show below, but it is not checked in yet.")
                print(json.dumps(
                    self.get(f'{configuration}_manifest'), indent=4))

        return configuration

    def get_version(self, configuration=str, repo=str):
        """Get the version of a repo in the given configuration

        Args:
            configuration (str): The configuration to query the manifest for
            repo (str): The fully qualified name (owner/repo) of the repo to look up
        Returns:
            version (str): The version of the repo in the manifest (Exit with error if not found)
        """
        # The constructor already loaded the manifests, for were good to assume it's healthy

        # Check if the repo exists in the manifest
        for entry in self.get(f"{configuration}_manifest")[configuration]:
            if entry["repo"] == repo:
                try:
                    return entry["version"]
                except KeyError:
                    print(
                        f"⛔️ Error: The repo '{repo}' is not yet manifested in  the '{configuration}' configuation.", file=sys.stderr)
                    sys.exit(1)

        print(
            f"⛔️ Error: Repository {repo} not found in configuration {configuration}", file=sys.stderr)
        sys.exit(1)
