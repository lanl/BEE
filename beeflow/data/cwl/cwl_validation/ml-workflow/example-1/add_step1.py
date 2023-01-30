"""Add Step."""
import json
import click


@click.command()
@click.argument('x', type=int)
@click.argument('y', type=int)
def add(x, y):
    """Add."""
    click.echo(json.dumps({'answer': x + y}))


if __name__ == '__main__':
    add(x=1, y=2)
