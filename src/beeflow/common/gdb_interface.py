"""Mid-level interface for managing a graph database with workflows.

Delegates the actual work to an instance of a subclass of
the abstract base class GraphDatabaseDriver. By default,
this is the Neo4jDriver class.
"""

import os
import re
from beeflow.common.gdb.neo4j_driver import Neo4jDriver


class GraphDatabaseInterface:
    """Interface for managing a graph database with workflows.

    Requires an implemented subclass of GraphDatabaseDriver (uses Neo4jDriver by default).
    """

    def __init__(self, gdb_driver=Neo4jDriver):
        """Initialize the graph database interface with a graph database driver.

        :param gdb_driver: the graph database driver (Neo4jDriver by default)
        :type gdb_driver: subclass of GraphDatabaseDriver
        """
        # Store the GDB driver state
        self._gdb_driver = gdb_driver
        self._connection = None

    def __del__(self):
        """Disconnect from the graph database when interface deconstructs."""
        if self.initialized():
            self.close()

    def connect(self, **kwargs):
        """Initialize a graph database interface with a driver.

        :param kwargs: arguments for initializing the graph database connection
        """
        # Initialize the graph database driver
        self._connection = self._gdb_driver(**kwargs)

    def initialize_workflow(self, workflow):
        """Begin construction of a workflow in the graph database.

        Connects to the database and creates the Workflow with accompanying Hint
        and Requirement nodes.
        Permits the addition of task nodes to the workflow.

        :param workflow: the workflow description
        :type workflow: Workflow
        """
        self._connection.initialize_workflow(workflow)

    def execute_workflow(self):
        """Begin execution of the loaded workflow."""
        self._connection.execute_workflow()

    def pause_workflow(self):
        """Pause execution of a running workflow."""
        self._connection.pause_workflow()

    def resume_workflow(self):
        """Resume execution of a running workflow."""
        self._connection.resume_workflow()

    def reset_workflow(self, new_id):
        """Reset the execution state and ID of a workflow.

        :param new_id: the new workflow ID
        :type new_id: str
        """
        self._connection.reset_workflow(new_id)

    def load_task(self, task):
        """Load a task into a workflow in the graph database.

        :param task: the task
        :type task: Task
        """
        self._connection.load_task(task)

    def initialize_ready_tasks(self):
        """Set runnable tasks in a workflow to ready."""
        self._connection.initialize_ready_tasks()
    
    def restart_task(self, old_task, new_task):
        """Create a new task from a failed task checkpoint restart enabled.
        
        :param old_task: the failed task
        :type old_task: Task
        :param new_task: the new (restarted) task
        :type new_task: Task
        """
        self._connection.restart_task(old_task, new_task)

    def finalize_task(self, task):
        """Set a task's state to completed.

        :param task: the task to finalize
        :type task: Task
        """
        self._connection.finalize_task(task)

    def get_task_by_id(self, task_id):
        """Return a workflow Task given its ID.

        :param task_id: the task's ID
        :type task_id: str
        :rtype: Task
        """
        return self._connection.get_task_by_id(task_id)

    def get_workflow_description(self):
        """Return the workflow description from the graph database.

        :rtype: Workflow
        """
        return self._connection.get_workflow_description()

    def get_workflow_tasks(self):
        """Return a workflow's tasks from the graph database.

        :rtype: list of Task
        """
        return self._connection.get_workflow_tasks()

    def get_workflow_requirements_and_hints(self):
        """Return a tuple containing a list of requirements and a list of hints.

        The returned tuple format is (requirements, hints).

        :rtype: (list of Requirement, list of Hint)
        """
        return self._connection.get_workflow_requirements_and_hints()

    def get_ready_tasks(self):
        """Return the tasks in a workflow with state 'READY'.

        :rtype: list of Task
        """
        return self._connection.get_ready_tasks()

    def get_dependent_tasks(self, task):
        """Return the dependents of a task in a workflow.

        :param task: the task whose dependents to retrieve
        :type task: Task
        :rtype: list of Task
        """
        return self._connection.get_dependent_tasks(task)

    def get_task_state(self, task):
        """Return the state of a task.

        :param task: the task whose state to retrieve
        :type task: Task
        :rtype: str
        """
        return self._connection.get_task_state(task)

    def set_task_state(self, task, state):
        """Set the state of a task.

        :param task: the task whose state to set
        :type task: Task
        :param state: the new state
        :type state: str
        """
        return self._connection.set_task_state(task, state)

    def get_task_metadata(self, task):
        """Return the job description metadata of a task.

        :param task: the task whose metadata to retrieve
        :type task: Task
        :rtype: dict
        """
        return self._connection.get_task_metadata(task)

    def set_task_metadata(self, task, metadata):
        """Set the job description metadata of a task.

        :param task: the task whose metadata to set
        :type task: Task
        :param metadata: the job description metadata
        :type metadata: dict
        """
        self._connection.set_task_metadata(task, metadata)

    def get_task_input(self, task, input_id):
        """Get a task input object.

        :param task: the task whose input to retrieve
        :type task: Task
        :param input_id: the ID of the input
        :type input_id: str
        :rtype: StepInput
        """
        return self._connection.get_task_input(task, input_id)

    def set_task_input(self, task, input_id, value):
        """Set the value of a task input.

        :param task: the task whose input to set
        :type task: Task
        :param input_id: the ID of the input
        :type input_id: str
        :param value: str or int or float
        """
        self._connection.set_task_input(task, input_id, value)

    def get_task_output(self, task, output_id):
        """Get a task output object.

        :param task: the task whose output to retrieve
        :type task: Task
        :param output_id: the ID of the output
        :type output_id: str
        :rtype: StepOutput
        """
        return self._connection.get_task_output(task, output_id)

    def set_task_output(self, task, output_id, value):
        """Set the value of a task output.

        :param task: the task whose output to set
        :type task: Task
        :param output_id: the ID of the output
        :type output_id: str
        :param value: the output value to set
        :type value: str or int or float
        """
        self._connection.set_task_output(task, output_id, value)

    def evaluate_expression(self, task, id, output):
        """Evaluate a task input/output expression.

        Expression can be a parameter substitution or a string concatenation in a StepInput
        valueFrom field or a StepOutput glob field. The only special variable supported
        is self.path.

        :param task: the task whose expression to evaluate
        :type task: Task
        :param id: the id of the step input/output
        :type id: str
        :param output: true if output glob expression being evaluated, else false
        :type output: bool
        """
        # Get ground-truth task from database before doing anything
        task =  self._connection.get_task_by_id(task.id)
        input_pairs = {input.id: input.value for input in task.inputs}
        if output:
            step_output = self._connection.get_task_output(task, id)
            # Find all matches of string pattern $(inputs.foo), capturing value of foo
            expr_pattern = r"\$\(inputs\.(\w+)\)"
            match = re.findall(expr_pattern, step_output.glob)
            if match:
                # Split string up to get list of non-matching characters
                split_pattern = r"\$\(inputs\.\w+\)"
                split = re.split(split_pattern, step_output.glob)
                values = []
                for m in match:
                    if m in input_pairs.keys():
                        values.append(input_pairs[m])
                    else:
                        raise ValueError(f"reference to non-existent task input {m}")
                # Construct string with evaluated inputs
                eval_string = split[0]
                for v, s in zip(values, split[1:]):
                    eval_string += v + s
                self._connection.set_task_output_glob(task, id, eval_string)
        else:
            step_input = self._connection.get_task_input(task, id)
            # Match any of the following patterns: self.path, inputs.foo, or "foo"
            # in an expression of the form $(A + B) in the valueFrom field
            expr_pattern = r'\$\((self\.path|inputs\.\w+|".+") \+ (self\.path|inputs\.\w+|".+")\)'
            match = re.fullmatch(expr_pattern, step_input.value_from)
            if match:
                values = []
                for m in match.groups():
                    if m == "self.path":
                        values.append(os.path.realpath(step_input.value))
                    elif m.startswith("inputs."):
                        if m[7:] in input_pairs.keys():
                            values.append(input_pairs[m[7:]])
                        else:
                            raise ValueError(f"reference to non-existent task input {m[7:]}")
                    else:
                        # Pattern "foo" (strip quotes)
                        values.append(m[1:-1])
                self._connection.set_task_input_type(task, id, "string")
                self._connection.set_task_input(task, id, values[0] + values[1])
            else:
                raise ValueError(f"unable to evaluate expression {step_input.value_from}")

    def workflow_completed(self):
        """Return true if all tasks in a workflow have state 'COMPLETED', else false.

        :rtype: bool
        """
        return self._connection.workflow_completed()

    def initialized(self):
        """Return true if the database connection has been initialized, else false.

        :rtype: bool
        """
        return bool(self._connection is not None)

    def empty(self):
        """Return true if the graph database is empty, else false.

        :rtype: bool
        """
        return self._connection.empty()

    def cleanup(self):
        """Clean up all data in the graph database."""
        self._connection.cleanup()

    def close(self):
        """Close the connection to the graph database."""
        self._connection.close()
        self._connection = None
