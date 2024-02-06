#!/usr/bin/env python
"""CI workflow run script."""
import typer

from beeflow.common import integration_test


if __name__ == '__main__':
    typer.run(integration_test.main)
