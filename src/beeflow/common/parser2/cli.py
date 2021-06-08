#!/usr/bin/env python
# coding=utf-8
"""
A simple application using cmd2 which demonstrates 8 key features:

    * Settings
    * Commands
    * Argument Parsing
    * Generating Output
    * Help
    * Shortcuts
    * Multiline Commands
    * History
"""
import argparse

import cmd2
from cmd2 import (
    ansi
)

from colorama import (
    Back,
    Fore,
    Style,
)


class NeoApp(cmd2.Cmd):
    """An app to test complex workflow database support."""

    def __init__(self):
        shortcuts = cmd2.DEFAULT_SHORTCUTS
        self.allow_style = ansi.STYLE_TERMINAL
        hist_file='cmd2_history.dat'
        self.prompt = 'BEE> '
        super().__init__(persistent_history_file=hist_file, persistent_history_length=500, allow_cli_args=False)

    neo_parser = argparse.ArgumentParser()
    neo_parser.add_argument('-d', '--database', type=str, help='Neo4j DB location')
    neo_parser.add_argument('-f', '--fg', choices=ansi.fg.colors(), help='foreground color to apply to output')

    @cmd2.with_argparser(neo_parser)
    def do_connect(self, args):
        """Connects to existing Neo4j database."""
        if args.database:
            self.poutput(ansi.style(args.database, fg=args.fg))
            print(f'{Fore.RED}{Back.YELLOW}databse{Style.RESET_ALL}: {args.database}')

    def do_status(self, _):
        """Dump status of connected Neo4j DB"""
        pass

    def do_aprint(self, statement):
        """Print the argument string this basic command is called with."""
        self.poutput('aprint was called with argument: {!r}'.format(statement))
        self.poutput('statement.raw = {!r}'.format(statement.raw))
        self.poutput('statement.argv = {!r}'.format(statement.argv))
        self.poutput('statement.command = {!r}'.format(statement.command))

    @cmd2.with_argument_list
    def do_lprint(self, arglist):
        """Print the argument list this basic command is called with."""
        self.poutput('lprint was called with the following list of arguments: {!r}'.format(arglist))

    @cmd2.with_argument_list(preserve_quotes=True)
    def do_rprint(self, arglist):
        """Print the argument list this basic command is called with (with quotes preserved)."""
        self.poutput('rprint was called with the following list of arguments: {!r}'.format(arglist))


if __name__ == '__main__':
    import sys

    c = NeoApp()
    sys.exit(c.cmdloop())
