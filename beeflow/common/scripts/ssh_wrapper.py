"""Minimal wrapper to execute the beeflow-ssh bash script."""
import os
import sys


def main():
    """Execute the beeflow-ssh bash script."""
    script = os.path.join(os.path.dirname(__file__), 'beeflow-ssh')
    os.execv(script, [script] + sys.argv[1:])


if __name__ == '__main__':
    main()
