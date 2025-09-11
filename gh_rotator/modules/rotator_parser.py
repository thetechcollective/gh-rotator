#!/usr/bin/env python3

import argparse


def rotator_parse(args=None):
    """Parse command line arguments for the rotator tool."""
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
        parents=[parent_parser, mainfestdir_parser],
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
        parents=[parent_parser, mainfestdir_parser],
        help="Get the manifest of a given configuration",
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

    return parser.parse_args(args)
