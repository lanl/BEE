#!/usr/bin/env python
import sys
import os
import glob
import argparse

#  Create a directory. Write num files into it.

def parse_args(args=sys.argv[1:]):
    """Parse arguments."""
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)

    parser.add_argument("input_dir", type=str, help="input directory name")
    parser.add_argument("pattern", type=str, help="pattern match for file names")

    return parser.parse_args(args)


def main():
    args = parse_args()
    with open("viz.mov", mode="w") as v:
        os.chdir(args.input_dir)
        # Normally we'd sort these if really making a movie.
        for file in glob.glob(args.pattern):
            v.write(f"Viz file {file}\n")


if __name__ == "__main__":
    sys.exit(main())
