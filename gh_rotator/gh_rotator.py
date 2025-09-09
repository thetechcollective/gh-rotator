#!/usr/bin/env python3

import argparse
import json
import os
import sys

class_path = os.path.dirname(os.path.abspath(__file__)) + "/classes"
sys.path.append(class_path)

from productconfig import ProductConfig
from productmanifest import ProductManifest


def parse(args=None):
    global parser
    # Define the parent parser with the --verbose argument
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    parent_parser.add_argument(
        "--config-file",
        type=str,
        dest="config_file",
        help="The path to the config file",
        default="config-rotator.json",
    )

    mainfestdir_parser = argparse.ArgumentParser(add_help=False)
    mainfestdir_parser.add_argument(
        "--manifest-dir",
        type=str,
        dest="manifest_dir",
        help="The directory to save the manifest file",
        default="configurations",
    )

    # Define command-line arguments
    parser = argparse.ArgumentParser(
        prog="rotator",
        parents=[parent_parser,mainfestdir_parser],
        description="""   
            A command-line tool designed as a helper utility to the rotator.yml workflow.  
            """,
    )

    subparsers = parser.add_subparsers(dest="command")

    # Manifest subcommand
    lock_parser = subparsers.add_parser(
        "lock",
        parents=[parent_parser, mainfestdir_parser],
        help="Lock a manifest file for the derived configuration",
        description="""
            Designed to take the same parameters as the rotator.yml accepts in the dispatch. (see the templates directory in this repo)
            Simply pass the parameters recived forward to manifest subcommand and it will generate a manifest file.
            """,
    )
    lock_parser.add_argument(
        "--repo", 
        type=str, 
        help="The fully qualified name (owner/repo) of the repo that fired the event",
        required=True
    )
    lock_parser.add_argument(
        "--event-type",
        type=str,
        choices=["branch", "tag"],
        dest="event_type",
        help="Event type that triggered the run (branch|tag)",
        required=True,
    )
    lock_parser.add_argument(
        "--event-name",
        type=str,
        dest="event_name",
        help="Event name that triggered the run (branch or tag name)",
        required=True,
    )
    lock_parser.add_argument(
        "--sha",
        type=str,
        help="The SHA1 of the commit that triggered the run",
        required=True,
    )

    # manifest subcommand
    manifest_parser = subparsers.add_parser(
        "manifest",
        parents=[parent_parser,mainfestdir_parser],
        help="Get the manifest of agiven configuration",
        description="""
            Designed to easily return the manifest of a repo from a specific manifest
            """,
    )
    manifest_parser.add_argument(
        "--repo", 
        type=str, 
        help="The fully qualified name (owner/repo) of the repo to look up",
        default=None
    )
    manifest_parser.add_argument(
        "--configuration",
        type=str,
        help="The configuration to query the manifest for",
        required=True,
    )

    # config subcommand
    config_parser = subparsers.add_parser(
        "config",
        parents=[parent_parser],
        help="Get the configuration",
        description="""
            Designed to easily return the configuration name from context
            """,
    )
    config_parser.add_argument(
        "--repo", 
        type=str, 
        help="The fully qualified name (owner/repo) of the repo to look up",
        default=None
    )
    config_parser.add_argument(
        "--event-type",
        type=str,
        choices=["branch", "tag"],
        dest="event_type",
        help="Event type that triggered the run (branch|tag)",
        required=True,
    )
    config_parser.add_argument(
        "--event-name",
        type=str,
        dest="event_name",
        help="Event name that triggered the run (branch or tag name)",
        required=True,
    )

    args = parser.parse_args(args)
    return args

if __name__ == "__main__":
    args = parse(sys.argv[1:])

    if args.command == "lock":
        
        # Generate the manifest
        config = ProductConfig(file=args.config_file)
        manifest = ProductManifest(config, directory=args.manifest_dir)
        result =  manifest.rotate(
            repo=args.repo,
            sha=args.sha,
            event_type=args.event_type,
            event_name=args.event_name,            
            verbose=args.verbose)
        
        if result:
            sys.exit(0)
        else:
            print(f"Failed to lock manifest for {args.configuration}")
            sys.exit(1)

    if args.command == "manifest":
        config = ProductConfig(file=args.config_file)
        manifest = ProductManifest(config, directory=args.manifest_dir)
        if args.repo is None or args.repo == "":
            try:
                config_data = manifest.get(f"{args.configuration}_manifest")
                print(json.dumps(config_data, indent=4))
                sys.exit(0)            
            except AssertionError:
                print(f"⛔️ Error: No manifest exists for configuration '{args.configuration}'.", file=sys.stderr)
                sys.exit(1)
        
        else :
            version = manifest.get_version(
                configuration=args.configuration,
                repo=args.repo,
                verbose=args.verbose
            )

            print(f"{version}")
            sys.exit(0)

    if args.command == "config":
        # Get the configuration name
        config = ProductConfig(file=args.config_file)
        configuration = config.get_config_name(
            repo=args.repo,
            event_name=args.event_name,
            event_type=args.event_type,
            verbose=args.verbose
        )
        print(f"{configuration}")
        sys.exit(0)
    
    if args.command is None:
        # Print help if no arguments are provided
        parser.print_help()

    exit(0)