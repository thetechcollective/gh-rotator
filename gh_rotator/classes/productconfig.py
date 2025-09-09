import json
import os
import re
import subprocess
import sys

# Add directory of this class to the general class_path
# to allow import of sibling classes
class_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(class_path)

from lazyload import Lazyload


class ProductConfig(Lazyload):
    """Class used to load and represent the product config (defaults to config-rotator.json in the repo root)"""

    def __init__(self, file=None):
        super().__init__()

        # make sure we're in a git context, capture the git repo root
        # and set the config_dir to the root of the git repo
        try:
            self.set('git_root', subprocess.check_output(['git', 'rev-parse', '--show-toplevel']).decode('utf-8').strip())
        except subprocess.CalledProcessError:
            print("⛔️ Error: Not in a git repository. Please run this script from a git repository.", file=sys.stderr)
            sys.exit(1)           
          
        # Set the default config file 
        if file is None:
            # use the default config file
            file = os.path.join(self.get("git_root"), 'config-rotator.json')
        self.set('config_file', file)
        self.set('config', None)
        
        # Load the config file
        self.__load_config()


    def __load_config(self):
        """Load the config file and set the config property"""
        # Check if the file exists
        if not os.path.exists(self.get('config_file')):
            print(f"⛔️ Error: Config file {self.get('config_file')} not found", file=sys.stderr)
            sys.exit(1)
        
        # Load the config file
        try:
            with open(self.get('config_file')) as f:
                self.set('config', json.load(f))
        except json.JSONDecodeError:
            print(f"⛔️ Error: Config file {self.get('config_file')} is not a valid JSON file", file=sys.stderr)
            sys.exit(1)
    
    def get_config_name(self, repo=str, event_name=str, event_type=str, verbose=False):
        """Look up the configuration name for the given repo, event_name and event_type"""      
        found_config = None

        for configuration, repos in self.get('config').items():
            for repo_config in repos:
                if (
                    repo_config["repo"] == repo and
                    repo_config["ref_type"] == event_type and
                    re.match(repo_config["ref_name"], event_name)
                ):
                    found_config = configuration
                    break
            if found_config:
                break

        if not found_config:
            print(f"⛔️ Error: No matching configuration found for repo '{repo}', event_type '{event_type}', and event_name '{event_name}'.", file=sys.stderr)
            sys.exit(1)

        return found_config    
        
              
 