"""Parses and validates CWL workflow """

import os
import yaml
from schema_salad import main as schema_salad

class BeeCWL:
    """Retrieving and validating CWL workflow"""

    def __init__(self, path):
        """Initialize the parser interface with a CWL workflow location.

    :param path: the workflow location
    :type path: System path (ex. home/user./example/workflow/first_workflow.cwl)
    """
        self.path = path

    # noinspection PyBroadException
    @property
    def parser(self):
        """ Validates cwl file then returns a dictionary of components in a CWL workflow.

           $CWL_VERSIONS required in environment for path to CWL versions for schema.

          :param path: the orginal CWL location to parse
          :type path: System Path
          """
        try:
            with open(self.path, 'r') as cwl_file:
                cwl_dict = yaml.safe_load(cwl_file)

            cwl_version = cwl_dict.get('cwlVersion')
            versions_path = (os.environ['CWL_VERSIONS']
                             + cwl_version
                             + '/CommonWorkflowLanguage.yml')
            compare = schema_salad.main(argsl=[versions_path, self.path])
            if not compare.bit_length() == 0:
                cwl_dict = None

        except OSError as err:
            print("Error: {0} ".format(err))
            cwl_dict = None

        if cwl_dict and cwl_dict.get('steps'):
            error_files = []
            self.load_steps(cwl_dict, error_files)
            if error_files:
               print('error files: ', error_files)
               print('CWL files with errors:')
               [print('\t',i) for i in error_files]
        return cwl_dict

    def load_steps(self, cwl_dict, error_files):
        """ Validates and loads step cwl files into dictionary for workflow """
        for step in  list(cwl_dict.get('steps').keys()):
            step_file = cwl_dict['steps'][step]['run']
            if isinstance(step_file, str):
                step_cwl = BeeCWL(step_file)
                step_dict = step_cwl.parser
                if step_dict:
                    cwl_dict['steps'][step]['run'] = step_dict
                else:
                    error_files.append(step_file)
