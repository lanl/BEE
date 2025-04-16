#!/usr/bin/env python
"""CI workflow run script."""
import typer
import coverage

from beeflow.common import integration_test


if __name__ == '__main__':
    cov = coverage.Coverage(data_file='.coverage.integration', auto_data=True)
    cov.start()
    typer.run(integration_test.main)
    cov.stop()
    cov.save()
