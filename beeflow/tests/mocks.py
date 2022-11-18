"""Mocks for the WFM and TM tests."""

from copy import deepcopy
from beeflow.common.wf_data import StepInput, StepOutput
from beeflow.common import expr


class MockTask:
    """Mock task object."""

    def __init__(self, task_name="task", state="DEFAULT", new_id=42):
        """Initialize."""
        self.name = task_name
        self.state = state
        self.id = new_id
        self.metadata = {}


class MockWFI:
    """Mock worfklow interface object."""

    def __init__(self):
        """Set the fake workflow id."""
        self._workflow_id = '42'
        self._loaded = False

    def pause_workflow(self):
        """Pause a workflow."""
        return

    def resume_workflow(self):
        """Resume a workflow."""
        return

    def reset_workflow(self, wf_id): #noqa
        """Reset a workflow."""
        wf_id = 0 # noqa

    def get_dependent_tasks(self, task): # noqa
        """Get depdendent states."""
        return [MockTask()]

    def get_task_metadata(self, task):
        """Get the task's metadata."""
        return task.metadata

    def set_task_metadata(self, task, metadata):
        """Set the metadata for this task."""
        task.metadata = metadata

    def get_task_by_id(self, task_id): # noqa
        """Return a mock task from an ID."""
        return MockTask()

    def get_workflow_state(self):
        """Get a workflow state."""
        return 'PENDING'

    @property
    def workflow_id(self):
        """Return the workflow id."""
        return self._workflow_id

    def get_ready_tasks(self):
        """Return a mock ready task."""
        return [MockTask()]

    def workflow_initialized(self):
        """Fake that the workflow has been initialized."""

    def set_task_state(self, task, job_state): # noqa
        """Set the state of a task."""
        task.state = job_state

    def workflow_loaded(self):
        """Fake workflow being loaded."""
        return self._loaded

    def initialize_workflow(self, wf_id, wf_name, inputs, outputs, req=None, hints=None): # noqa
        """Initialize the workflow."""
        self._loaded = True

    def finalize_workflow(self):
        """Finalize the workflow."""
        self._loaded = False

    def create_requirement(self, req_class, key, value):
        """Fake creating a requirement."""

    def add_task(self, name, base_command, inputs, outputs, requirements, hints, stdout, stderr):
        """Fake adding a task."""

    def get_workflow(self):
        """Get a list of workflows."""
        return None, [MockTask("task1"), MockTask("task2")]

    def get_task_state(self, task_name): # noqa
        """Returns the task state."""
        return "RUNNING"

    def execute_workflow(self):
        """Fake executing a workflow."""
        pass # noqa 


class MockGDBInterface:
    """A mock GDB interface.

    TODO: This is very crude, and will likely break with more complicated GDB
    interactions.
    """

    def __init__(self, **_kwargs):
        """Create a new mock gdb (ignore kwargs)."""
        self.workflow = None
        self.workflow_state = None
        self.tasks = {}
        self.task_states = {}
        self.task_metadata = {}
        self.inputs = {}
        self.outputs = {}

    def connect(self, **kwargs):
        """Initialize a graph database interface with a driver."""

    def initialize_workflow(self, workflow):
        """Begin construction of a workflow in the graph database."""
        self.workflow = workflow
        self.workflow_state = 'SUBMITTED'

    def _is_ready(self, task_id):
        """Check whether a given task is ready to run."""
        sources = [inp.source for inp in self.inputs[task_id].values()]
        task_deps = [task_id for task_id in self.tasks
                     if any(source in self.outputs[task_id] for source in sources)]
        return all(self.task_states[task_dep_id] == 'COMPLETED'
                   for task_dep_id in task_deps)

    def execute_workflow(self):
        """Begin execution of the loaded workflow."""
        self.workflow_state = 'RUNNING'
        for task_id in self.task_states:
            if self._is_ready(task_id):
                self.task_states[task_id] = 'READY'

    def pause_workflow(self):
        """Pause execution of a running workflow."""
        self.workflow_state = 'PAUSED'

    def resume_workflow(self):
        """Resume execution of a running workflow."""
        self.workflow_state = 'RESUME'

    def reset_workflow(self, new_id):
        """Reset the execution state and ID of a workflow."""
        self.workflow = deepcopy(self.workflow)
        self.workflow.id = new_id
        for task_id, task in self.tasks.items():
            task.workflow_id = new_id
            self.task_metadata[task_id] = {}
            self.task_states[task_id] = 'WAITING'

    def load_task(self, task):
        """Load a task into a workflow in the graph database."""
        self.tasks[task.id] = task
        self.task_states[task.id] = 'WAITING'
        self.task_metadata[task.id] = {}
        self.inputs[task.id] = {}
        self.outputs[task.id] = {}
        for inp in task.inputs:
            self.inputs[task.id][inp.id] = inp
        for outp in task.outputs:
            self.outputs[task.id][outp.id] = outp

    def initialize_ready_tasks(self):
        """Set runnable tasks in a workflow to ready."""
        for task_id in self.tasks:
            if self._is_ready(task_id) and self.task_states[task_id] == 'WAITING':
                self.task_states[task_id] = 'READY'

    def restart_task(self, _old_task, new_task):
        """Create a new task from a failed task checkpoint restart enabled."""
        self.load_task(new_task)

    def finalize_task(self, task):
        """Set a task's state to completed."""
        self.task_states[task.id] = 'COMPLETED'

    def get_task_by_id(self, task_id):
        """Return a workflow Task given its ID."""
        return self.tasks[task_id]

    def get_workflow_description(self):
        """Return the workflow description from the graph database."""
        return deepcopy(self.workflow)

    def get_workflow_state(self):
        """Return workflow's current state."""
        return self.workflow_state

    def set_workflow_state(self, state):
        """Return workflow's current state."""
        self.workflow_state = state

    def get_workflow_tasks(self):
        """Return a workflow's tasks from the graph database."""
        return list(self.tasks.values())

    def get_workflow_requirements_and_hints(self):
        """Return a tuple containing a list of requirements and a list of hints."""
        return (None, None)

    def get_ready_tasks(self):
        """Return the tasks in a workflow with state 'READY'."""
        return [task for task_id, task in self.tasks.items()
                if self.task_states[task_id] == 'READY']

    def get_dependent_tasks(self, task):
        """Return the dependents of a task in a workflow."""
        tasks = [dep_task for dep_task_id, dep_task in self.tasks.items()
                 if any(outp_id in [inp.source
                                    for inp in self.inputs[dep_task_id].values()]
                        for outp_id in self.outputs[task.id])]
        return tasks

    def get_task_state(self, task):
        """Return the state of a task."""
        return self.task_states[task.id]

    def set_task_state(self, task, state):
        """Set the state of a task."""
        self.task_states[task.id] = state

    def get_task_metadata(self, task):
        """Return the job description metadata of a task."""
        return self.task_metadata[task.id]

    def set_task_metadata(self, task, metadata):
        """Set the job description metadata of a task."""
        self.task_metadata[task.id] = metadata

    def get_task_input(self, task, input_id):
        """Get a task input object."""
        inp = self.inputs[task.id][input_id]
        try:
            inp.id # noqa (trying to get an AttributeError here)
            return inp
        except AttributeError:
            return StepInput(input_id, 'File', inp,
                             'default.txt', input_id, None, None, None)

    def set_task_input(self, task, input_id, value):
        """Set the value of a task input."""
        self.inputs[task.id][input_id] = value

    def get_task_output(self, task, output_id):
        """Get a task output object."""
        return self.outputs[task.id][output_id]

    def set_task_output(self, task, output_id, value):
        """Set the value of a task output."""
        self.outputs[task.id][output_id] = StepOutput(
            output_id, 'File', value, value,
        )

    def evaluate_expression(self, task, id_, output):
        """Evaluate a task input/output expression."""
        input_pairs = {id_: inp.value for id_, inp in self.inputs[task.id].items()}
        if output:
            step_outp = self.outputs[task.id][id_]
            val = expr.eval_output(input_pairs, step_outp.glob)
            if val is not None:
                self.outputs[task.id][id_] = StepOutput(step_outp.id, step_outp.type,
                                                        step_outp.value, val)
        else:
            step_inp = self.inputs[task.id][id_]
            val = expr.eval_input(input_pairs, step_inp.value_from)
            self.inputs[task.id][id_] = StepInput(step_inp.id, 'string', val,
                                                  step_inp.default,
                                                  step_inp.source,
                                                  step_inp.prefix,
                                                  step_inp.position,
                                                  step_inp.value_from)

    def workflow_completed(self):
        """Return true if all of a workflow's final tasks have completed, else false."""
        return all(state == 'COMPLETED' for state in self.task_states.values())

    def initialized(self):
        """Return true if the database connection has been initialized, else false."""
        return not self.empty()

    def empty(self):
        """Return true if the graph database is empty, else false."""
        return self.workflow is None

    def cleanup(self):
        """Clean up all data in the graph database."""
        self.workflow = None
        self.workflow_state = None
        self.tasks.clear()
        self.task_states.clear()
        self.task_metadata.clear()
        self.inputs.clear()
        self.outputs.clear()

    def close(self):
        """Close the connection to the graph database."""


def mock_create_image(): # noqa
    """Fake image creation."""
    pass # noqa


class MockCwlParser:
    """Mock the CWLParser."""

    def __init__(self, bolt_port):
        """Need a port."""
        self.bolt_port = bolt_port

    def parse_workflow(self, wf_id, cwl_path, yaml_file=None): # noqa
        """Parse the workflow."""
        return MockWFI()


class MockWorkerSubmission:
    """Mock Worker during submission."""

    def submit_task(self, task): # noqa
        """Return submission."""
        return 1, 'PENDING'

    def query_task(self, job_id): #noqa
        """Return state of task."""
        return 'RUNNING'

    def cancel_task(self, job_id): # noqa
        """Return cancelled status"""
        return 'CANCELLED'


class MockWorkerCompletion:
    """Mock Worker after completion."""

    def submit_task(self, task): #noqa
        """Submit a task."""
        return 1, 'PENDING'

    def query_task(self, job_id): #noqa
        """Submit a task."""
        return 'COMPLETED'

    def cancel_task(self, job_id): #noqa
        """Cancel a task."""
        return 'CANCELLED'


class MockResponse:
    """Mock a response."""

    def __init__(self, status_code):
        """Initialize response."""
        self.status_code = status_code

    @staticmethod
    def json():
        """Return json output."""
        return '{}'


def mock_put(url, params=None, **kwargs): # noqa
    """Fake put."""
    return MockResponse(200)


def mock_post(url, params=None, **kwargs): # noqa
    """Fake post."""
    return MockResponse(200)


def mock_get(url, params=None, **kwargs): # noqa
    """Fake get."""
    return MockResponse(200)


def mock_delete(url, params=None, **kwargs): # noqa
    """Fake delete."""
    return MockResponse(200)
