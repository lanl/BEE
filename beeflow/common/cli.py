"""Common CLI code used by different BEE scripts."""
import click


class NaturalOrderGroup(click.Group):
    def list_commands(self, ctx):
        return self.commands.keys()
