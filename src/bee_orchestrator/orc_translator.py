# system
import abc
from termcolor import cprint
# project
from .tar_localhost import LocalhostAdaptee
from .tar_ssh import SSHAdaptee
from .tar_slurm import SlurmAdaptee


class Target(metaclass=abc.ABCMeta):
    """
    Define the domain-specific interface that Client uses
    """
    def __init__(self, system, config, file_loc, task_name):
        self.__system = str(system).lower()

        # Beefile related
        self._config = config
        self._file_loc = file_loc
        self._task_name = task_name

        self._adaptee = None
        self.update_adaptee()

    def update_adaptee(self):
        if self.__system == "slurm":
            self._adaptee = SlurmAdaptee(self._config, self._file_loc,
                                         self._task_name)
        if self.__system == "localhost":
            self._adaptee = LocalhostAdaptee(self._config, self._file_loc,
                                             self._task_name)
        else:
            cprint("Unable to support target system: " + self.__system +
                   " attempting ssh.", "yellow")
            self._adaptee = SSHAdaptee(self._config, self._file_loc,
                                       self._task_name)

    @abc.abstractmethod
    def execute(self):
        pass

    @abc.abstractmethod
    def shutdown(self):
        pass

    @abc.abstractmethod
    def move_file(self):
        pass


class Adapter(Target):
    """
    Adapt the interface of adaptee to the target request
    """
    def execute(self):
        self._adaptee.specific_execute()

    def shutdown(self):
        self._adaptee.specific_shutdown()

    def move_file(self):
        self._adaptee.specific_move_file()
