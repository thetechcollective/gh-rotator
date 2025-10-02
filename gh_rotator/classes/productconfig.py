import json
import os
import re
import subprocess
import sys

from gh_rotator.classes.lazyload import Lazyload


class ProductConfig(Lazyload):
    """Class used to load and represent the product config (defaults to config-rotator.json in the repo root)"""

    def __init__(self, file=None):
        super().__init__()

        # make sure we're in a git context, capture the git repo root
        # and set the config_dir to the root of the git repo
        try:
            self.set(
                "git_root",
                subprocess.check_output(["git", "rev-parse", "--show-toplevel"])
                .decode("utf-8")
                .strip(),
            )
        except subprocess.CalledProcessError:
            print(
                "⛔️ Error: Not in a git repository. Please run this script from a git repository.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Set the default config file
        if file is None:
            # Try to use the default config file in the repo
            repo_config = os.path.join(self.get("git_root"), "config-rotator.json")
            if os.path.exists(repo_config):
                self.set("config_file", repo_config)
            else:
                # Fall back to the built-in default config
                default_config_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "config",
                    "config-rotator.json",
                )
                if os.path.exists(default_config_path):
                    self.set("config_file", default_config_path)
                else:
                    print(f"Error: No configuration file found", file=sys.stderr)
                    sys.exit(1)
        else:
            # If user explicitly specified a config file, treat it as relative to git root
            relative_path = os.path.join(self.get("git_root"), file)

            if os.path.exists(relative_path):
                self.set("config_file", relative_path)
            else:
                print(f"Error: Config file '{relative_path}' not found", file=sys.stderr)
                sys.exit(1)

        self.set("config", None)

        # Load the config file
        self.__load_config()

    def __load_config(self):
        """Load the config file and set the config property"""
        # Config file existence was already checked in __init__
        # Just load the file and handle JSON errors
        try:
            with open(self.get("config_file")) as f:
                self.set("config", json.load(f))
        except json.JSONDecodeError:
            print(
                f"Error: Config file {self.get('config_file')} is not a valid JSON file",
                file=sys.stderr,
            )
            sys.exit(1)

    def get_config_name(self, repo=str, event_name=str, event_type=str, verbose=False):
        """Look up the configuration name for the given repo, event_name and event_type

        Args:
            repo (str): The fully qualified name (owner/repo) of the repo to look up
            event_name (str): The event name that triggered the run (branch or tag name)
            event_type (str): The event type that triggered the run (branch|tag)
            verbose (bool, optional): Whether to print verbose output. Defaults to False.
        Returns:
            configuration (str): The configuration name that was found
        """
        found_config = None

        for configuration, repos in self.get("config").items():
            for repo_config in repos:
                if (
                    re.fullmatch(repo_config["repo"], repo)
                    and repo_config["ref_type"] == event_type
                    and re.fullmatch(repo_config["ref_name"], event_name)
                ):
                    found_config = configuration
                    if verbose:
                        print(
                            f"Found configuration '{configuration}' for repo '{repo}', event_type '{event_type}', and event_name '{event_name}'."
                        )
                    break
            if found_config:
                break

        if not found_config:
            print(
                f"⛔️ Error: No matching configuration found for repo '{repo}', event_type '{event_type}', and event_name '{event_name}'.",
                file=sys.stderr,
            )
            sys.exit(1)

        return found_config
