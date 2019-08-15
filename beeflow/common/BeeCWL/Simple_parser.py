import yaml
import pandas as pd
from schema_salad import main as validator

def get_cwl_inputs(dataframe):
    cwl_inputs = dataframe.loc[df['CWL_Key'] == 'inputs','CWL_Value'][0:]
    return cwl_inputs
def get_cwl_outputs(dataframe):
    cwl_outputs = dataframe.loc[df['CWL_Key'] == 'outputs','CWL_Value'][0:]
    return cwl_outputs
def get_cwl_version(dataframe):
    cwlVersion = dataframe.loc[df['CWL_Key'] == 'cwlVersion','CWL_Value'][0]
    return cwlVersion
def get_cwl_requirements(dataframe):
    cwl_requirements = dataframe.loc[df['CWL_Key'] == 'requirements','CWL_Value'][0:]
    return cwl_requirements
def get_cwl_steps(dataframe):
    cwl_steps = dataframe.loc[df['CWL_Key'] == 'steps','CWL_Value'][0:]
    return cwl_steps
def get_cwl_hints(dataframe):
    cwl_hints = dataframe.loc[df['CWL_Key'] == 'hints','CWL_Value'][0:]
    return cwl_hints
def get_cwl_label(dataframe):
    cwl_label = dataframe.loc[df['CWL_Key'] == 'label','CWL_Value'][0:]
    return cwl_label
def get_cwl_doc(dataframe):
    cwl_doc = dataframe.loc[df['CWL_Key'] == 'doc','CWL_Value'][0:]
    return cwl_doc
def get_cwl_class(dataframe):
    cwl_class = dataframe.loc[df['CWL_Key'] == 'class','CWL_Value'][0:]
    return cwl_class
def get_cwl_id(dataframe):
    cwl_id = dataframe.loc[df['CWL_Key'] == 'id','CWL_Value'][0:]
    return cwl_id


with open("./echo2-wf.cwl", 'r') as cwl_file:
    file_path = "./echo2-wf.cwl"
    cwl_dict = yaml.safe_load(cwl_file)
    df = pd.DataFrame.from_dict(cwl_dict.items())
    df.reset_index(0)
    df.rename(columns={0: 'CWL_Key',1: 'CWL_Value'},inplace=True)
    cwlVersion = df.loc[df['CWL_Key'] == 'cwlVersion','CWL_Value'][0]
    if cwlVersion == 'v1.0':
        validation_result = validator.main(argsl=['./v1.0/CommonWorkflowLanguage.yml',file_path])
        if validation_result.bit_length() == 0:
            #df.to_csv(r'.\result.csv')
            #print(get_cwl_inputs(df))
            #print(get_cwl_label(df))
            print(get_cwl_requirements(df))
            #print(cwl_dict)
            #print(df.loc[df['CWL_Key'] == 'requirements'])
            #print("================================")
            print(df)
    if cwlVersion == 'v1.1':
        validation_result = validator.main(argsl=['./v1.1/CommonWorkflowLanguage.yml', file_path])
        if validation_result.bit_length() == 0:
            df.to_csv(r'.\result.csv')
            #print("Version 1.1")
            # print(cwl_dict)
            # print(df.loc[df['CWL_Key'] == 'requirements'])
            # print("================================")
            print(df)

    if cwlVersion == 'v1.1.0-dev1':
        validation_result = validator.main(argsl=['./v1.1.0-dev1/CommonWorkflowLanguage.yml', file_path])
        if validation_result.bit_length() == 0:
            df.to_csv(r'.\result.csv')
            # print(cwl_dict)
            # print(df.loc[df['CWL_Key'] == 'requirements'])
            # print("================================")
            print(df)