from BeeCWL import BeeCWL

p1 = BeeCWL("./echo2-wf.cwl")
result = p1.parser # dictionary of
print(result)
print(80*'-')


p2 = BeeCWL("./blast-cc/blast-cc-flow.cwl")
result2 = p2.parser
print(result2)
print(80*'-')

p3 = BeeCWL("./echo.cwl")
result3 = p3.parser
print(result3)

print(result._get_value(result.loc[result['__key__']=='steps'].index[0],'__value__'))

print(BeeCWL.get_baseCommand(p3,datafram=result3))
from beeflow.common.wf_interface import WorkflowInterface

name = result._get_value(result.loc[result['__key__']=='class'].index[0],'__value__')
inputs = result._get_value(result.loc[result['__key__']=='inputs'].index[0],'__value__')
outputs = result._get_value(result.loc[result['__key__']=='outputs'].index[0],'__value__')
print('inputs using _get_value from dataframe:', inputs)
print('inputs using BeeCWL get_inputs:', p1.get_inputs(result))
try:
    hints = result._get_value(result.loc[result['__key__']=='hints'].index[0],'__value__')
    print('hints: ', hints)
except:
    hints = None
    print('hints were not found and were set to', hints)

Task = WorkflowInterface.create_task(name=name,hints=hints,inputs=inputs,outputs=outputs)


