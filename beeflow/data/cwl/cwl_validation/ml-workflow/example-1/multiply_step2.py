"""Multiply Step."""

import json
import click


@click.command()
@click.argument('x', type=int)
@click.argument('y', type=int)
def multiply(x, y):
    """Multiply."""
    click.echo(json.dumps({'answer': x * y}))


if __name__ == '__main__':
    multiply(x=2, y=10)
