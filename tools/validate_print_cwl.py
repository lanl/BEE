""" Parses, Validates and Prints a cwl file  """

import argparse 
import pprint
from beeflow.common.wf_interface import WorkflowInterface
from beeflow.common.parser.cwl_parser import BeeCWL

cl_parser= argparse.ArgumentParser()
cl_parser.add_argument('-c','--cwl_file', help='CWL file to parse.', required=True)
cl_parser.add_argument('-r','--recursive', help='Parse CWL steps files.', action='store_true')
cl_parser.add_argument('-l','--list', help='Full list of cwl files.', action='store_true')
args = cl_parser.parse_args()

error_files=[]
cwl_dict=[]
cwl_file = args.cwl_file

cwl_bee = BeeCWL(cwl_file)
cwl_dict = cwl_bee.parser
if cwl_dict:
    if args.list: 
        pp = pprint.PrettyPrinter(indent=4)
        print('\n Parsing ', cwl_file, '\n')
        pp.pprint(cwl_dict)
    
    if args.recursive :
         
        for (step, cwl_file) in (zip(
                list(cwl_dict.get('steps').keys()),
                    [cwl_dict['steps'][n]['run'] for n in cwl_dict['steps']])):
            print('\n Step ', step,': Parsing ', cwl_file)
            cwl_bee = BeeCWL(cwl_file)
            cwl_dict = cwl_bee.parser
            if not cwl_dict:
                error_files.append(cwl_file)   
            elif args.list: 
                pp = pprint.PrettyPrinter(indent=4)
                pp.pprint(cwl_dict)
elif args.recursive:
    print('The cwl file has errors, step files cannot be parsed!')
    error_files.append(cwl_file)

if error_files:
    print('\n The following cwl files need to be fixed:')
    print('\t', *error_files, sep='\n\t')
else:
    print('All files are valid!')        
