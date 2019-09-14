""" Some examples of parsing various files"""

from cwl_parser import BeeCWL
from beeflow.common.wf_interface import WorkflowInterface

cwl_file = 'examples/echo2-wf.cwl'
cwl_bee = BeeCWL(cwl_file)
cwl_dict = cwl_bee.parser
print(list(cwl_dict.keys()))
print('inputs = ', cwl_dict.get('inputs'))
print('There should be no hints in', cwl_file, '!')
print('hints = ', cwl_dict.get('hints'))
Task = WorkflowInterface.create_task(
        name=cwl_dict.get('class'),
        hints=cwl_dict.get('hints'),
        inputs=cwl_dict.get('inputs'),
        outputs=cwl_dict.get('outputs'))
print(Task)
print(80*'-')

cwl_file = 'examples/blast-cc/blast-cc-flow.cwl'
cwl_bee = BeeCWL(cwl_file)
cwl_dict = cwl_bee.parser
print("keys in 'steps'  = ", list(cwl_dict.get('steps').keys()))
print(80*'-')

cwl_file = "examples/echo.cwl"
cwl_bee = BeeCWL(cwl_file)
cwl_dict = cwl_bee.parser
print(cwl_dict)
print('steps = ', cwl_dict.get('steps'))
print('baseCommand =', cwl_dict.get('baseCommand'))

