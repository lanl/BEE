#!/usr/bin/env python3
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
        hist_file='bee_history.dat'
        self.prompt = 'BEE> '
        super().__init__(persistent_history_file=hist_file, persistent_history_length=500, allow_cli_args=False)

    neo_parser = argparse.ArgumentParser()
    neo_parser.add_argument('-d', '--database', type=str, help='Neo4j DB location')
    neo_parser.add_argument('-f', '--fg', choices=ansi.fg.colors(), help='foreground color to apply to output')

    task_states = ['READY', 'RUNNING', 'COMPLETE', 'CRASHED', 'WAITING']

    # db {subcommands}
    db_parser = argparse.ArgumentParser()
    db_subparsers = db_parser.add_subparsers(title='subcommands', help='supported opetarions')
    # db info
    parser_dbinfo = db_subparsers.add_parser('info', help='dump info on connected GDB')
    # task {subcommands}
    task_parser = argparse.ArgumentParser()
    task_subparsers = task_parser.add_subparsers(title='subcommands', help='subcommand help')
    # task info
    parser_taskinfo = task_subparsers.add_parser('info', help='dump info on one or more Task nodes')
    parser_taskinfo.add_argument('-a', '--all', action='store_true', help='dump all Task nodes in GDB')
    parser_taskinfo.add_argument('task', nargs='?', type=str, help='one or more Task node names')
    # task set
    parser_taskset = task_subparsers.add_parser('set', help='set property on one or more Task nodes')
    parser_taskset.add_argument('-x', type=int, default=1, help='integer')
    parser_taskset.add_argument('y', type=float, help='float')
    parser_taskset.add_argument('prop', type=str, help='property to set')

    # subcommand functions for the db command
    def db_info(self, args):
        """info subcommand of db command"""
        self.poutput('db info!')
    # subcommand functions for the task command
    def task_info(self, args):
        """info subcommand of task command"""
        self.poutput('task info!')
    def task_set(self, args):
        """info subcommand of task command"""
        self.poutput('task setinfo!')
    # Set handler functions for the subcommands
    parser_dbinfo.set_defaults(func=db_info)
    parser_taskinfo.set_defaults(func=task_info)
    parser_taskset.set_defaults(func=task_set)

    @cmd2.with_argparser(db_parser)
    def do_db(self, args):
        """Operate on BEE's graph database."""
        func = getattr(args, 'func', None)
        if func is not None:
            # Call whatever subcommand function was selected
            func(self, args)
        else:
            # No subcommand was provided, so call help
            self.do_help('db')

    @cmd2.with_argparser(task_parser)
    def do_task(self, args):
        """Operate on one or more BEE Task nodes."""
        func = getattr(args, 'func', None)
        if func is not None:
            # Call whatever subcommand function was selected
            func(self, args)
        else:
            # No subcommand was provided, so call help
            self.do_help('task')


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
        self.poutput(f'aprint was called with argument: {statement}')
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
