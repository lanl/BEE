""" Parses, Validates and Prints a cwl file  """

import sys
import pprint
from beeflow.common.wf_interface import WorkflowInterface
from beeflow.common.parser.cwl_parser import BeeCWL

if len(sys.argv) < 2:
    print('No cwl filename entered on command line!')
else:
    cwl_file = sys.argv[1]
    cwl_bee = BeeCWL(cwl_file)
    cwl_dict = cwl_bee.parser
    pp = pprint.PrettyPrinter(indent=4)
    print('\n Parsing ', cwl_file, '\n')
    pp.pprint(cwl_dict)
