#!/usr/bin/env python
import sys
import argparse

#  Copy an input file to another file. Add a "*" to the beginning of each line.

def parse_args(args=sys.argv[1:]):
    """Parse arguments."""
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)

    parser.add_argument("input_file", type=str, help="input data file")
    parser.add_argument("output_file", type=str, help="output data file")
    return parser.parse_args(args)


def main():
    args = parse_args()
    print(args.input_file, args.output_file)
    with open(args.input_file) as f, open(args.output_file, mode="w") as of:
        for line in f:
            of.write(f"*{line}")


if __name__ == "__main__":
    sys.exit(main())
