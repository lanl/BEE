class LocalhostAdaptee:
    def __init__(self, config, file_loc, task_name):
        self._config = config
        self._config_req = self._config['requirements']
        self._file_loc = file_loc
        self._task_name = task_name
        self._encode = 'UTF-8'

    def specific_execute(self):
        pass

    def specific_shutdown(self):
        pass

    def specific_move_file(self):
        pass
