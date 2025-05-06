#!/usr/bin/env python3

import argparse
import sys
import os
import json

class_path = os.path.dirname(os.path.abspath(__file__)) + "/classes"
sys.path.append(class_path)

from productmanifest import ProductManifest
from productconfig import ProductConfig


def parse(args=None):
    global parser
    # Define the parent parser with the --verbose argument
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    # Define command-line arguments
    parser = argparse.ArgumentParser(
        prog="rotator",
        parents=[parent_parser],
        description="""   
            A command-line tool designed as a helper utility to the rotator.yml workflow.  
            """,
    )

    subparsers = parser.add_subparsers(dest="command")

    # Manifest subcommand
    manifest_parser = subparsers.add_parser(
        "manifest",
        parents=[parent_parser],
        help="Will generate a manifest file for the configuration",
        description="""
            Designed to take the same parameters as the rotator.yml accepts in the dispatch.
            Simply pass the parameters recived forward to manifest subcommand and it will generate a manifest file.
            """,
    )
    manifest_parser.add_argument(
        "--event",
        type=str,
        help="Event that triggered the run",
        required=True,
    )
    manifest_parser.add_argument(
        "--sha1",
        type=str,
        help="The SHA1 of the commit that triggered the run",
        required=True,
    )
    manifest_parser.add_argument(
        "--repo", 
        type=str, 
        help="The fully qualifeid name (owner/repo) of the repo that fired the event",
        required=True
    )
    manifest_parser.add_argument(
        "--configuration",
        type=str,
        help="The configuration to build the manifest for",
        required=True,
    )


    # version subcommand
    version_parser = subparsers.add_parser(
        "version",
        parents=[parent_parser],
        help="Print the version of a repo from a specific manifest",
        description="""
            Designed to easily return the sha1 of a repo from a specific manifest
            """,
    )
    version_parser.add_argument(
        "--repo", 
        type=str, 
        help="The fully qualifeid name (owner/repo) of the repo to look up",
        required=True
    )
    version_parser.add_argument(
        "--configuration",
        type=str,
        help="The configuration to query the manifest for",
        required=True,
    )




    args = parser.parse_args(args)
    return args

if __name__ == "__main__":
    args = parse(sys.argv[1:])

    if args.command == "manifest":
        
        # Generate the manifest
        config = ProductConfig()
        manifest = ProductManifest(config)
        result =  manifest.rotate(
            configuration=args.configuration,
            repo=args.repo,
            sha1=args.sha1,
            event=args.event,
            verbose=args.verbose)
        
        if result:
            sys.exit(0)
        else:
            print(f"Failed to update manifest for {args.configuration}")
            sys.exit(1)

    if args.command == "version":
        # Get the version of the repo
        config = ProductConfig()
        manifest = ProductManifest(config)
        version = manifest.get_version(
            configuration=args.configuration,
            repo=args.repo,
            verbose=args.verbose
        )
        
        if version:
            print(f"{version}")
            sys.exit(0)
        else:
            print(f"Failed to get version for {args.configuration}")
            sys.exit(1)
        
    
    
        
    
    if args.command is None:
        # Print help if no arguments are provided
        parser.print_help()

    exit(0)