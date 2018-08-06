# system
import abc
from termcolor import cprint
from tar_slurm import SlurmAdaptee
from tar_ssh import SSHAdaptee


class Target(metaclass=abc.ABCMeta):
    """
    Define the domain-specific interface that Client uses
    """
    def __init__(self, system, config):
        self.__system = str(system).lower()
        self._config = config
        self._adaptee = None
        if self.__system == "slurm":
            self._adaptee = SlurmAdaptee(self._config)
        else:
            cprint("Unable to support target system: " + self.__system +
                   " attempting ssh.", "yellow")
            self._adaptee = SSHAdaptee(self._config)

    @abc.abstractmethod
    def allocate(self):
        pass

    @abc.abstractmethod
    def execute(self):
        pass

    @abc.abstractmethod
    def schedule(self):
        pass

    @abc.abstractmethod
    def query_job(self):
        pass

    @abc.abstractmethod
    def query_scheduler(self):
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
    def allocate(self):
        self._adaptee.specific_allocate()

    def execute(self):
        self._adaptee.specific_execute()

    def schedule(self):
        self._adaptee.specific_schedule()

    def query_job(self):
        self._adaptee.specific_query_job()

    def query_scheduler(self):
        self._adaptee.specific_schedule()

    def shutdown(self):
        self._adaptee.specific_shutdown()

    def move_file(self):
        self._adaptee.specific_move_file()
