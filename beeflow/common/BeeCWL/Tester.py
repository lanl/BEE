from beeflow.common.BeeCWL.BeeCWL import BeeCWL

p1 = BeeCWL("./echo2-wf.cwl")
result = p1.parser
print(result)

p2 = BeeCWL("./blast-cc/blast-cc-flow.cwl")
result2 = p2.parser
print(result2)


from beeflow.common.wf_interface import WorkflowInterface

name = result._get_value(result.loc[result['__key__']=='class'].index[0],'__value__')
inputs = result._get_value(result.loc[result['__key__']=='inputs'].index[0],'__value__')
outputs = result._get_value(result.loc[result['__key__']=='outputs'].index[0],'__value__')
hints = result._get_value(result.loc[result['__key__']=='requirements'].index[0],'__value__')

Task = WorkflowInterface.create_task(name=name,hints=hints,inputs=inputs,outputs=outputs)
