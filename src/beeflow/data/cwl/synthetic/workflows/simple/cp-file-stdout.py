#!/usr/bin/env python
import sys
import argparse

#  Copy an input file to stdout. Add a "-" to the beginning of each line.

def parse_args(args=sys.argv[1:]):
    """Parse arguments."""
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)

    parser.add_argument("input_file", type=str, help="input data file")
    return parser.parse_args(args)


def main():
    args = parse_args()
    with open(args.input_file) as f:
        for line in f:
            print(f"-{line}", end="")


if __name__ == "__main__":
    sys.exit(main())
