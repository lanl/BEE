#!/usr/bin/env python3
"""REST Interface for the BEE Scheduler."""

from flask import Flask, request
from flask_restful import Resource, Api

import algorithms
import allocation
import sched_types


# TODO: Grab this info from the config
SCHEDULER_PORT = 5100

flask_app = Flask(__name__)
api = Api(flask_app)

# List of all available resources
resources = []
allocation_store = allocation.AllocationStore()
tasks = []


class ResourcesHandler(Resource):
    """Resources handler.

    Handle creation of resources.
    """

    def put(self):
        """Create a list of resources to use for allocation.

        Create new resources based on a list of resources.
        """
        resources.clear()
        resources.extend([sched_types.Resource.decode(r) for r in request.json])
        return 'created %i resources(s)' % len(resources)

    def get(self):
        """Get a list of all resources.

        Returna a list of all available resources known to the scheduler.
        """
        # TODO: Handle complex objects
        return resources


class WorkflowJobHandler(Resource):
    """
    """

    def put(self, workflow_name, task_name=None):
        """"""
        data = request.json
        if task_name is None:
            new_tasks = [sched_types.Task.decode(t) for t in data]
            # TODO: Schedule the new_tasks
            tasks.extend(new_tasks)
            return [t.encode() for t in new_tasks]
        else:
            # Update a task
            task_update = sched_types.Task.decode(data)
            task_i = None
            for i, task in enumerate(tasks):
                if (task.workflow_name == task_update.workflow_name
                        and task.task_name == task_update.task_name):
                    task_i = i
                    break
            if task_i is not None:
                tasks[task_i] = task_update
            else:
                # Add a new task
                tasks.append(task_update)
            return task_update.encode()

    def get(self, workflow_name, task_name=None):
        """Get a job or jobs of a workflow.

        Find details about particular jobs of a workflow.
        """
        if task_name is None:
            return [t.encode() for t in tasks
                    if t.workflow_name == workflow_name]
        else:
            pass
            # TODO

    def delete(self, workflow_name, task_name=None):
        """"""
        # TODO


api.add_resource(ResourcesHandler, '/bee_sched/v1/resources')
api.add_resource(WorkflowJobHandler,
                 '/bee_sched/v1/workflows/<string:workflow_name>/jobs',
                 ('/bee_sched/v1/workflows/<string:workflow_name>/jobs/'
                  '<string:task_name>'))

if __name__ == '__main__':
    # TODO: Add -p port parsing
    flask_app.run(debug=True, port=SCHEDULER_PORT)
