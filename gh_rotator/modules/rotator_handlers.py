#!/usr/bin/env python3

import json
import sys

from gh_rotator.classes.productconfig import ProductConfig
from gh_rotator.classes.productmanifest import ProductManifest


def handle_lock(args):
    """Handle the lock command to generate a manifest"""
    # Generate the manifest
    config = ProductConfig(file=args.config_file)
    manifest = ProductManifest(config, directory=args.manifest_dir)
    result = manifest.rotate(
        repo=args.repo,
        sha=args.sha,
        event_type=args.event_type,
        event_name=args.event_name,
        verbose=args.verbose,
    )

    if result:
        sys.exit(0)
    else:
        print(f"Failed to lock manifest for {args.configuration}")
        sys.exit(1)


def handle_manifest(args):
    """Handle the manifest command to get configuration manifest"""
    config = ProductConfig(file=args.config_file)
    manifest = ProductManifest(config, directory=args.manifest_dir)

    if args.repo is None or args.repo == "":
        try:
            config_data = manifest.get(f"{args.configuration}_manifest")
            print(json.dumps(config_data, indent=4))
            sys.exit(0)
        except AssertionError:
            print(
                f"⛔️ Error: No manifest exists for configuration '{args.configuration}'.",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        version = manifest.get_version(
            configuration=args.configuration, repo=args.repo, verbose=args.verbose
        )

        print(f"{version}")
        sys.exit(0)


def handle_config(args):
    """Handle the config command to get configuration name"""
    # Get the configuration name
    config = ProductConfig(file=args.config_file)
    configuration = config.get_config_name(
        repo=args.repo, event_name=args.event_name, event_type=args.event_type, verbose=args.verbose
    )
    print(f"{configuration}")
    sys.exit(0)


# Command handler mapping - exported for use by main
COMMAND_HANDLERS = {
    "lock": handle_lock,
    "manifest": handle_manifest,
    "config": handle_config,
}
