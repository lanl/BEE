"""Mocks for the WFM and TM tests."""


class MockTask:
    """Mock task object."""

    def __init__(self, task_name="task", state="DEFAULT", new_id=42):
        """Initialize."""
        self.name = task_name
        self.state = state
        self.id = new_id


class MockWFI:
    """Mock worfklow interface object."""

    def get_dependent_tasks(self, task): # noqa
        """Get depdendent states."""
        return [MockTask()]

    def get_task_by_id(self, task_id): # noqa
        """Return a mock task from an ID."""
        return MockTask()

    @staticmethod
    def workflow_initialized():
        """Fake that the workflow has been initialized."""

    def set_task_state(self, task, job_state): # noqa
        """Set the state of a task."""
        task.state = job_state

    @staticmethod
    def workflow_loaded():
        """Fake workflow being loaded."""
        return True

    def initialize_workflow(self, inputs, outputs, req=None, hints=None): # noqa
        """Initialize the workflow."""

    @staticmethod
    def finalize_workflow():
        """Finalize the workflow."""

    def create_requirement(self, req_class, key, value):
        """Fake creating a requirement."""

    def add_task(self, name, command, inputs, outputs, hints):
        """Fake adding a task."""

    @staticmethod
    def get_workflow():
        """Get a list of workflows."""
        return [MockTask("task1"), MockTask("task2")], [], []

    def get_task_state(self, task_name): # noqa
        """Returns the task state."""
        return "RUNNING"


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
        return 1, 'PENDING'

    def query_task(self, job_id): #noqa
        return 'COMPLETED'

    def cancel_task(self, job_id): #noqa
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
    """Fake put"""
    return MockResponse(200)


def mock_post(url, params=None, **kwargs): # noqa
    """Fake post"""
    return MockResponse(200)


def mock_get(url, params=None, **kwargs): # noqa
    """Fake get"""
    return MockResponse(200)


def mock_delete(url, params=None, **kwargs): # noqa
    """Fakes delete"""
    return MockResponse(200)
