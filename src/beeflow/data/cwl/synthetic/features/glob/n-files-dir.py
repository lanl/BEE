#!/usr/bin/env python
import sys
import os
import argparse

#  Create a directory. Write num files into it.

def parse_args(args=sys.argv[1:]):
    """Parse arguments."""
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)

    parser.add_argument("output_dir", type=str, help="output directory name")
    parser.add_argument("num_files", type=int, help="number of files to create")

    return parser.parse_args(args)


def main():
    args = parse_args()
    assert args.num_files < 100, "Too many files"
    os.mkdir(args.output_dir)
    for i in range(args.num_files):
        with open(f"{args.output_dir}/file_{i:03}.dat", mode="w") as f:
            f.write(f"This is file number {i}\n")


if __name__ == "__main__":
    sys.exit(main())
