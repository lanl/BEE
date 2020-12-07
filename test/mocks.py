class MockTask:
    def __init__(self, task_name="task", state="DEFAULT", id=42):
        self.name = task_name
        self.state = state
        self.id = id

class MockWFI:
    def get_dependent_tasks(self, task):
        return [MockTask()]

    def get_task_by_id(self, task_id):
        return MockTask()

    def workflow_initialized(self):
        pass

    def set_task_state(self, task, job_state):
        task.state = job_state

    def workflow_loaded(self):
        return True
    
    def initialize_workflow(self, inputs, outputs, req=None, hints=None):
        pass

    def finalize_workflow(self):
        pass

    def create_requirement(self, req_class, key, value):
        pass
    
    def add_task(self, name, command, inputs, outputs, hints):
        pass

    def get_workflow(self):
        return [MockTask("task1"), MockTask("task2")], [], []

    def get_task_state(self, task_name):
        return "RUNNING"

class MockWorkerSubmission:

    def __init__(self):
        pass

    def submit_task(self, task):
        return 1, 'PENDING'

    def query_task(self, job_id):
        return 'RUNNING'

    def cancel_task(self, job_id):
        return 'CANCELLED'

class MockWorkerCompletion:

    def __init__(self):
        pass

    def submit_task(self, task):
        return 1, 'PENDING'

    def query_task(self, job_id):
        return 'COMPLETED'

    def cancel_task(self, job_id):
        return 'CANCELLED'


class MockResponse:
    def __init__(self, status_code):
        self.status_code = status_code
    
    def json(self):
        return '{}'

def mock_put(url, params=None, **kwargs):
    return MockResponse(200)

def mock_post(url, params=None, **kwargs):
    return MockResponse(200)

def mock_get(url, params=None, **kwargs):
    return MockResponse(200)

def mock_delete(url, params=None, **kwargs):
    return MockResponse(200)
