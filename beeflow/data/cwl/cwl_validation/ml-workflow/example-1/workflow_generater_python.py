"""Workflow Generator."""
from scriptcwl import WorkflowGenerator

with WorkflowGenerator() as wf:
    wf.load(steps_dir='/Users/raginigupta/PythonCodes/cwl')

    num1 = wf.add_input(num1='int')
    num2 = wf.add_input(num2='int')

    answer1 = wf.add(x=num1, y=num2)
    answer2 = wf.multiply(x=answer1, y=num2)

    wf.add_outputs(final_answer=answer2)

    wf.save('add_multiply_example_workflow.cwl')
