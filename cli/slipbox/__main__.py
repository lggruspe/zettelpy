"""Build HTML from all notes in slipbox."""

from argparse import ArgumentParser
from pathlib import Path
import sys

from .app import main, show_info
from .initializer import initialize, DotSlipbox, default_config
from .utils import check_requirements, check_if_initialized

if __name__ == "__main__":
    if not check_requirements():
        sys.exit("[ERROR] pandoc not found.")

    parser = ArgumentParser(description="Generate a single-page HTML from your notes.")
    subparsers = parser.add_subparsers(dest="command")

    build = subparsers.add_parser("build", help="generate static site")

    info = subparsers.add_parser("info", help="show information about note")
    info.add_argument("id", type=int, help="note ID")

    defaults = default_config()
    init = subparsers.add_parser("init", help="initialize notes directory")
    init.add_argument("-c", "--content-options",
                      default=defaults.get("slipbox", "content_options"),
                      help="pandoc options for the content")
    init.add_argument("-d", "--document-options",
                      default=defaults.get("slipbox", "document_options"),
                      help="pandoc options for the output")
    init.add_argument("--convert-to-data-url", action="store_true",
                      default=defaults.getboolean("slipbox", "convert_to_data_url"),
                      help="convert local images links to data URL")

    args = parser.parse_args()

    command = args.command
    del args.command
    if command == "init":
        args.convert_to_data_url = str(args.convert_to_data_url)
        parent = Path()
        initialize(parent, args)
        print(f"Initialized .slipbox in {parent.resolve()!s}.")
    elif check_if_initialized():
        dot = DotSlipbox()
        if command == "build":
            main(dot)
        elif command == "info":
            show_info(dot, args.id)
    else:
        sys.exit("could not find '.slipbox' in any parent directory.")
