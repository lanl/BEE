""" Parses, Validates and Prints a cwl workflow and sub cwl files. """

import sys
import argparse
import pprint
from beeflow.common.parser.cwl_parser import BeeCWL

def parse_args(args):
    """Parse arguments."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-c', '--cwl_file', help='CWL file to parse.', required=True)
    arg_parser.add_argument('-l', '--list', help='Full list of cwl files.', action='store_true')
    return arg_parser.parse_args(args)

def main():
    '''Entry point if called as an executable'''


    error_files = []
    cwl_dict = []
    args = parse_args(sys.argv[1:])
    cwl_file = args.cwl_file
    pretty_print = pprint.PrettyPrinter(indent=4)

    cwl_wf = BeeCWL(cwl_file)
    cwl_dict = cwl_wf.parser
    if cwl_dict:
        if cwl_dict.get('steps'):
            for step in  list(cwl_dict.get('steps').keys()):
                if isinstance(cwl_dict['steps'][step]['run'], (str)):
                    step_file = cwl_dict['steps'][step]['run']
                    step_cwl = BeeCWL(step_file)
                    step_dict = step_cwl.parser
                    if not step_dict:
                        error_files.append(step_file)
                    else:
                        cwl_dict['steps'][step]['run'] = step_dict
        if args.list:
            print('\n Parsing ', cwl_file, '\n')
            pretty_print.pprint(cwl_dict)


    if error_files:
        print('\n The following cwl files are invalid:')
        print('\t', *error_files, sep='\n\t')

if __name__ == '__main__':
    main()
