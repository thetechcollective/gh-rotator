#!/usr/bin/env python3

import sys
from pathlib import Path

from gh_rotator.modules.rotator_handlers import COMMAND_HANDLERS
from gh_rotator.modules.rotator_parser import rotator_parse


def main():
    """Main entry point for the rotator CLI tool."""
    args = rotator_parse(sys.argv[1:])

    # Execute the appropriate command handler
    if args.command in COMMAND_HANDLERS:
        COMMAND_HANDLERS[args.command](args)
    elif args.command is None:
        # Print help if no arguments are provided
        print("No command specified. Use -h or --help for usage information.")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
