"""Parses and validates CWL workflow """
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
        """Returns the dictionary of components in a CWL workflow.

          :param __cwl__: the orginal CWL location to parse
          :type __cwl__: System Path
          """
        try:
            with open(__cwl__.path, 'r') as cwl_file:
                cwl_dict = yaml.safe_load(cwl_file)

            """retrieve the CWL workflow version from data set"""
            cwl_version = cwl_dict.get('cwlVersion')

            """validate CWL workflow structure based on version"""
            # To Fix: path to version files should not be hard coded
            version_path = '../BeeCWL/' + cwl_version + '/CommonWorkflowLanguage.yml'
            print('version_path = ', version_path)
            compare = schema_salad.main(argsl=[version_path, __cwl__.path])
            if compare.bit_length() == 0:
                return cwl_dict 

        except OSError as err:
            print("Error: {0} ".format(err))

"""
    List of some keys in cwl_dict that one might use the get method for:
        baseCommand
        id
        hints
        cwlVersion
        doc
        arguments
        stdin
        stderr
        stdout
        successCodes
        temporaryFailCodes
        permanentFailCodes
"""

