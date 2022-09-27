"""Common CLI code used by different BEE scripts."""
import click


class NaturalOrderGroup(click.Group):
    """Natural ordering class for using with CLI code."""

    def list_commands(self, ctx):  # noqa
        """List the commands in order."""
        return self.commands.keys()
