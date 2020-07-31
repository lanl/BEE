import re
import sys
import math

import define

class Task:
    def __init__(self, line="0        0      0    0   0     0    0   0  0 0  0   0   0  0  0 0 0 0"):
        line = line.strip()
        s_array = re.split("\\s+", line)
        self.task_id = int(s_array[0])
        self.submit_time = int(s_array[1])
        self.wait_time = int(s_array[2])
        self.run_time = int(s_array[3])
        self.number_of_allocated_processors = int(s_array[4])
        self.average_cpu_time_used = float(s_array[5])
        self.used_memory = int(s_array[6])

        self.request_number_of_processors = int(s_array[7])
        self.number_of_allocated_processors = max(self.number_of_allocated_processors,
                                                  self.request_number_of_processors)
        self.request_number_of_processors = self.number_of_allocated_processors

        self.request_number_of_nodes = -1

        self.request_time = int(s_array[8])
        if self.request_time == -1:
            self.request_time = self.run_time


        self.request_memory = int(s_array[9])
        self.status = int(s_array[10])
        self.user_id = int(s_array[11])
        self.group_id = int(s_array[12])
        self.executable_number = int(s_array[13])
        self.queue_number = int(s_array[14])

        try:
            self.partition_number = int(s_array[15])
        except ValueError:
            self.partition_number = 0

        self.proceeding_task_number = int(s_array[16])
        self.think_time_from_proceeding_task = int(s_array[17])

        self.random_id = self.submit_time

        self.scheduled_time = -1

        self.allocated_machines = None

        self.slurm_in_queue_time = 0
        self.slurm_age = 0
        self.slurm_task_size = 0.0
        self.slurm_fair = 0.0
        self.slurm_partition = 0
        self.slurm_qos = 0
        self.slurm_tres_cpu = 0.0

    def __eq__(self, other):
        return self.task_id == other.task_id

    def __str__(self):
        return "t[" + str(self.task_id) + "]-[" + str(self.request_number_of_processors) + "]-[" + str(
            self.submit_time) + "]-[" + str(self.request_time) + "]"

    def __feature__(self):
        return [self.submit_time, self.request_number_of_processors, self.request_time,
                self.user_id, self.group_id, self.executable_number, self.queue_number]
    all_tasks = []


class Workloads:
    def __init__(self, path):
        self.max = 0
        self.max_exec_time = 0
        self.min_exec_time = sys.maxsize
        self.max_task_id = 0
        self.max_group_id = 0
        self.max_executable_number = 0
        self.max_task_id = 0
        self.max_nodes = 0
        self.max_procs = 0

        self.all_tasks = []
        with open(path) as fp:
            for line in fp:
                if line.startswith(";"):
                    if line.startswith("; MaxNodes:"):
                        self.max_nodes = int(line.split(":")[1].strip())
                    if line.startswith("; MaxProcs:"):
                        self.max_procs = int(line.split(":")[1].strip())
                    continue

                t = Task(line)
                if t.run_time > self.max_exec_time:
                    self.max_exec_time = t.run_time
                if t.run_time < self.min_exec_time:
                    self.min_exec_time = t.run_time

                self.all_tasks.append(t)

                if t.request_number_of_processors > self.max:
                    self.max = t.request_number_of_processors

        if self.max_procs == 0:
            self.max_procs = self.max_nodes

        print("Max Allocated Processors:", str(self.max),
              ";max node:",self.max_nodes,
              ";max procs:", self.max_procs,
              ";max execution time:", self.max_exec_time)

        self.all_tasks.sort(key=lambda task: task.task_id)

    def size(self):
        return len(self.all_tasks)

    def reset(self):
        for task in self.all_tasks:
            task.scheduled_time = -1

    def to_vector(self):
        """Return a vector representation.

        Return a vector representation of the workflow
        :rtype: list
        """
        vec = []
        # TODO: Add in machine information
        for task in self.all_tasks:
            vec.extend([float(task.submit_time), float(task.wait_time),
                        float(task.run_time)])
        return vec

    def __getitem__(self, item):
        return self.all_tasks[item]



class Machine:
    def __init__(self, id):
        self.id = id
        self.running_task_id = -1
        self.is_free = True
        self.task_history = []
    def taken_by_task(self, task_id):
        if self.is_free:
            self.running_task_id = task_id
            self.is_free = False
            self.task_history.append(task_id)
            return True
        else:
            return False
    def reset(self):
        self.is_free = True
        self.running_task_id = -1
        self.task_history = []
    def release(self):
        if self.is_free:
            return -1
        else:
            self.is_free = True
            self.running_task_id = -1
            return 1

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return "M["+str(self.id)+"] "


class Cluster:
    def __init__(self, cluster_name, node_num, num_procs_per_node):
        self.name = cluster_name
        self.total_node = node_num
        self.free_node = node_num
        self.used_node = 0
        self.num_procs_per_node = num_procs_per_node
        self.all_nodes = []

        for i in range(self.total_node):
            self.all_nodes.append(Machine(i))

    def feature(self):
        return [self.free_node]

    def can_allocated(self, task):
        if task.request_number_of_nodes != -1 and task.request_number_of_nodes > self.free_node:
            return False
        if task.request_number_of_nodes != -1 and task.request_number_of_nodes <= self.free_node:
            return True

    def allocate(self, task_id, request_num_procs):
        allocated_nodes = []
        request_node = int(math.ceil(float(request_num_procs) / float(self.num_procs_per_node)))

        if request_node > self.free_node:
            return []

        allocated = 0

        for m in self.all_nodes:
            if allocated == request_node:
                return allocated_nodes
            if m.taken_by_task(task_id):
                allocated += 1
                self.used_node += 1
                self.free_node -= 1
                allocated_nodes.append(m)

        if allocated == request_node:
            return allocated_nodes

        print ("Error in allocation, there are enough free resources but can not allocated!")
        return []

        request_node = int(math.ceil(float(task.request_number_of_processors)/float(self.num_procs_per_node)))
        task.request_number_of_nodes = request_node
        if request_node > self.free_node:
            return False
        else:
            return True

    def reset(self):
        self.used_node = 0
        self.free_node = self.total_node
        for m in self.all_nodes:
            m.reset()


    def is_idle(self):
        if self.used_node == 0:
            return True
        return False

    def release(self, releases):
        self.used_node -= len(releases)
        self.free_node += len(releases)

        for m in releases:
            m.release()


def load_workloads(workload_file='', sched_file=''):
    print("loading from dataset:", workload_file)
    workloads = Workloads(workload_file)
    cluster = Cluster("Cluster", workloads.max_nodes,
                      workloads.max_procs / workloads.max_nodes)
    penalty_task_score = (define.TASK_SEQUENCE_SIZE * workloads.max_exec_time
                          / 10)
    return workloads, cluster, penalty_task_score

if __name__ == '__main__':
    workloads, cluster, penalty_task_score = load_workloads(
        workload_file='Dataset/SDSC-SP2-1998-4.2-cln.swf')
