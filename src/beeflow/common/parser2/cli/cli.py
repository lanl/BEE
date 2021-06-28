#!/usr/bin/env python3
# coding=utf-8
"""
A CLI application to single step a BEE workflow. It's a multi-command
interface and suports commands for:

    * Database (connect, disconnect, status, info, etc.)
    * Workflow (info, set, get, etc.)
    * Task (info, set, get, etc.)
"""
import argparse

import cmd2

from rich.console import Console

from beeflow.common.wf_interface import WorkflowInterface
from beeflow.common.gdb_interface import GraphDatabaseInterface
from beeflow.common.wf_data import Workflow, Task, Requirement, Hint

gdb = None

con = Console()

class NeoApp(cmd2.Cmd):
    """An app to single-step a BEE workflow."""

    def __init__(self):
        shortcuts = cmd2.DEFAULT_SHORTCUTS
        hist_file='bee_history.dat'
        self.prompt = 'BEE> '
        del cmd2.Cmd.do_shell
        delattr(cmd2.Cmd, 'do_run_pyscript')
        delattr(cmd2.Cmd, 'do_run_script')
        delattr(cmd2.Cmd, 'do_edit')
        super().__init__(persistent_history_file=hist_file, persistent_history_length=500, allow_cli_args=False)

    neo_parser = argparse.ArgumentParser()
    neo_parser.add_argument('-d', '--database', type=str, help='Neo4j DB location')
    
    task_states = ['READY', 'RUNNING', 'COMPLETE', 'CRASHED', 'WAITING']
    CMD_CAT_BEE = "BEE Commands"

    # db {info, connect, disconnect}
    db_parser = argparse.ArgumentParser()
    db_subparsers = db_parser.add_subparsers(title='subcommands', help='supported opetarions')
    # db info
    parser_dbinfo = db_subparsers.add_parser('info', help='dump info on connected GDB')
    parser_dbconnect = db_subparsers.add_parser('connect', help='connect to the GDB')
    parser_dbdisconnect = db_subparsers.add_parser('disconnect', help='disconnect from the GDB')

    # workflow {info, set, get}
    workflow_parser = argparse.ArgumentParser()
    workflow_subparsers = workflow_parser.add_subparsers(title='subcommands', help='supported opetarions')
    # workflow info
    parser_workflowinfo = workflow_subparsers.add_parser('info', help='dump Workflow information')

    # task {info, set, get}
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

    ###################################################
    # subcommand functions for the db command
    def db_info(self, args):
        """info subcommand of db command"""
        if gdb.initialized():
            con.print('GDB [green]connected[/green]')
        else:
            con.print('GDB [red]not connected[/red]')

    def db_connect(self, args):
        """connect subcommand of db command"""
        if gdb.initialized():
            con.print('GDB already connected!')
        else:
            gdb.connect()
            con.print('GDB [green]connected[/green]')

    def db_disconnect(self, args):
        """disconnect subcommand of db command"""
        if gdb.initialized():
            gdb.close()
            con.print('GDB [red]disconnected[/red]')
        else:
            con.print('GDB already disconnected!')
    parser_dbinfo.set_defaults(func=db_info)
    parser_dbconnect.set_defaults(func=db_connect)
    parser_dbdisconnect.set_defaults(func=db_disconnect)

    ###################################################
    # subcommand functions for the workflow command
    def workflow_info(self, args):
        """info subcommand of workflow command"""
        if gdb.initialized():
            wf = gdb.get_workflow_description()
            con.print(f'Workflow ID/name: {wf.id}/{wf.name}')
            con.print(f'  hints:        {wf.hints}')
            con.print(f'  requirements: {wf.requirements}')
            con.print(f'  inputs:       {wf.inputs}')
            con.print(f'  outputs:      {wf.outputs}')
        else:
            con.print('GDB [red]not connected[/red]!')
    parser_workflowinfo.set_defaults(func=workflow_info)

    # subcommand functions for the task command
    def task_info(self, args):
        """info subcommand of task command"""
        if args.all:
            self.poutput('dumping all tasks')
        self.poutput(args)
        self.perror('bung')
        self.pwarning('daddy')
        self.pfeedback('feed me')
        self.poutput('task info!')
    def task_set(self, args):
        """info subcommand of task command"""
        self.poutput('task setinfo!')
    # Set handler functions for the subcommands
    parser_taskinfo.set_defaults(func=task_info)
    parser_taskset.set_defaults(func=task_set)

    @cmd2.with_category(CMD_CAT_BEE)
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

    @cmd2.with_category(CMD_CAT_BEE)
    @cmd2.with_argparser(workflow_parser)
    def do_workflow(self, args):
        """Operate on BEE's graph database."""
        func = getattr(args, 'func', None)
        if func is not None:
            # Call whatever subcommand function was selected
            func(self, args)
        else:
            # No subcommand was provided, so call help
            self.do_help('db')

    @cmd2.with_category(CMD_CAT_BEE)
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
            print(f'[bold cyan]databse[/bold cyan]: {args.database}')
            print('[bold cyan]databse[/bold cyan]: butt')

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

    wfi = WorkflowInterface()
    gdb = GraphDatabaseInterface()

    c = NeoApp()
    sys.exit(c.cmdloop())
