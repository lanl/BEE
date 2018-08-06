# system


class SlurmAdaptee:
    def __init__(self, config):
        self._config = config

    def specific_allocate(self):
        print("\nALLOCATE")
        print(str(self._config))

    def specific_execute(self):
        pass

    def specific_schedule(self):
        pass

    def specific_query_job(self):
        pass

    def specific_query_scheduler(self):
        pass

    def specific_shutdown(self):
        pass

    def specific_move_file(self):
        pass