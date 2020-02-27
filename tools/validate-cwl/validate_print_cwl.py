")"" Parses, Validates and Prints a cwl workflow and sub cwl files. """

import sys
import argparse
import pprint
from beeflow.common.parser.cwl_parser import BeeCWL

def parse_args(args):
    """Parse arguments."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-c', '--cwl_file', help='CWL file to parse.', required=True)
    arg_parser.add_argument('-r', '--recursive', help='Parse CWL steps files.', action='store_true')
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
        if args.list:
            print('\n Parsing ', cwl_file, '\n')
            pretty_print.pprint(cwl_dict)

        if args.recursive:
            if cwl_dict.get('steps'):
                for (step, cwl_file) in (zip(
                        list(cwl_dict.get('steps').keys()),
                        [cwl_dict['steps'][n]['run'] for n in cwl_dict['steps']])):
                    print('\n Step ', step, ': Parsing ', cwl_file)
                    cwl = BeeCWL(cwl_file)
                    cwl_dict = cwl.parser
                    if not cwl_dict:
                        error_files.append(cwl_file)
                    elif args.list:
                        pretty_print.pprint(cwl_dict)
            else:
                print('CWL file has no steps, -r flag not used.')

    elif args.recursive:
        print('The cwl file has errors, step files cannot be parsed!')
        error_files.append(cwl_file)

    if error_files:
        print('\n The following cwl files are invalid:')
        print('\t', *error_files, sep='\n\t')
    elif cwl_dict and args.recursive:
        print('All files are valid!')
if __name__ == '__main__':
    main()
