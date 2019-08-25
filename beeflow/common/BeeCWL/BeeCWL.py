"""BeeCWL parser module

Copyright:  Kent State University & Los Alamos National Lab

Author: Betis Baheri

Date: 08/25/2019

This module Parse CWL workflows and returns the components.
"""
import yaml
import pandas as pd
from schema_salad import main


class BeeCWL:
    """Interface for manipulating CWL workflows."""

    def __init__(__cwl__, path):
        """Initialize the parser interface with a CWL workflow location.

    :param __cwl__: the workflow location
    :type __cwl__: System path (ex. /home/example/workflow/first_workflow.cwl)
    """
        __cwl__.path = path

    # noinspection PyBroadException
    @property
    def parser(__cwl__):
        """Return the dictionary of a components in a CWL workflow.

          :param __cwl__: the orginal CWL location to parse
          :type __cwl__: System Path
          """
        try:
            """Python Open file function"""
            with open(__cwl__.path, 'r') as cwl_file:
                """load CWL file with yaml safe_load function to retrieve each component as a dictionary"""
                cwl_dict = yaml.safe_load(cwl_file)

                """transpose the data structure to Panda data set"""
                df = pd.DataFrame.from_dict(cwl_dict.items())

                """reset the first index on data set"""
                df.reset_index(0)

                """assigning __key__ and __value__ as a column headers for indexing"""
                df.rename(columns={0: '__key__', 1: '__value__'}, inplace=True)

                """retrieve the CWL workflow version from data set"""
                cwl_version = df.loc[df['__key__'] == 'cwlVersion', '__value__'][0]

                """validate CWL workflow structure based on version"""
                if cwl_version == 'v1.0':
                    result = main.main(argsl=['./v1.0/CommonWorkflowLanguage.yml', __cwl__.path])
                    if result.bit_length() == 0:
                        return df

                if cwl_version == 'v1.1':
                    result = main.main(argsl=['./v1.1/CommonWorkflowLanguage.yml', __cwl__.path])
                    if result.bit_length() == 0:
                        return df

                if cwl_version == 'v1.1.0-dev1':
                    result = main.main(argsl=['./v1.1.0-dev1/CommonWorkflowLanguage.yml', __cwl__.path])
                    if result.bit_length() == 0:
                        return df
        except OSError as err:
            print("Error: {0} ".format(err))