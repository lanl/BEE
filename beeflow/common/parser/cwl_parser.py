"""Parses and validates CWL workflow """

import os
import yaml
from schema_salad import main as schema_salad

class BeeCWL:
    """Retrieving and validating CWL workflow"""

    def __init__(__cwl__, path):
        """Initialize the parser interface with a CWL workflow location.

    :param __cwl__: the workflow location
    :type __cwl__: System path (ex. home/user./example/workflow/first_workflow.cwl)
    """
        __cwl__.path = path

    # noinspection PyBroadException
    @property
    def parser(__cwl__):
        """Validates cwl file then returns a dictionary of components in a CWL workflow.

           $CWL_VERSIONS required in environment for path to CWL versions for schema.

          :param __cwl__: the orginal CWL location to parse
          :type __cwl__: System Path
          """
        try:
            with open(__cwl__.path, 'r') as cwl_file:
                cwl_dict = yaml.safe_load(cwl_file)
            cwl_version = cwl_dict.get('cwlVersion')
            versions_path = (os.environ['CWL_VERSIONS']
                            + cwl_version
                            + '/CommonWorkflowLanguage.yml')
            compare = schema_salad.main(argsl=[versions_path, __cwl__.path])
            if compare.bit_length() == 0:
                return cwl_dict

        except OSError as err:
            print("Error: {0} ".format(err))
