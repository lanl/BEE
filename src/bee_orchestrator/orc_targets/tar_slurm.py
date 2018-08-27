# system
from tempfile import NamedTemporaryFile


class SlurmAdaptee:
    def __init__(self, config, file_loc, task_name):
        self._config = config
        self._config_req = self._config['requirements']
        self._file_loc = file_loc
        self._task_name = task_name
        self._encode = 'UTF-8'

    def specific_allocate(self):
        """
        Create sbatch file utilizing Beefile's desfined 'requirements' then
        execute this sbatch via subprocess.
        At this moment this system must be run on the login node of the cluster
        """
        tmp_f = NamedTemporaryFile()
        tmp_f.write(bytes("#!\\bin\\bash\n\n", 'UTF-8'))
        #######################################################################
        # Prepare SBATCH file
        # TODO: further document
        #######################################################################
        self.__resource_requirement(temp_file=tmp_f)
        self.__software_packages(temp_file=tmp_f)
        if self._config_req.get('CharliecloudRequirement', None) is not None:
            self.__deploy_charliecloud(temp_file=tmp_f)
        self.__deploy_bee_orchestrator(temp_file=tmp_f)

        tmp_f.seek(0)
        self._run_sbatch(tmp_f.name)
        tmp_f.close()

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

    # private / supporting functions
    def _run_salloc(self):
        pass

    def _run_sbatch(self, file):
        # TODO: execute via subprocess?
        print("sbatch -> " + str(file))
        import subprocess
        subprocess.call(['cp', str(file), '/home/paul/Downloads'])

    def __resource_requirement(self, temp_file):
        """

        :param temp_file: Named Temporary File
        """
        for key, value in self.\
                _config['requirements']['ResourceRequirement'].items():
            if key == 'custom':
                for c_key, c_value in value.items():
                    temp_file.write(bytes("#SBATCH {}={}\n".format(c_key,
                                                                   c_value),
                                    self._encode))
            else:
                gsl = self.__generate_sbatch_line(key, value)
                if gsl is not None:
                    temp_file.write(bytes(gsl + "\n", self._encode))
        # Set job-name equal if ID is available
        j_id = self._config.get('id', None)
        if j_id is not None:
            temp_file.write(bytes("#SBATCH --job-name={}".format(j_id),
                                  self._encode))

    @staticmethod
    def __generate_sbatch_line(key, value):
        """

        :param key:
        :param value:
        :return:
        """
        # supported sbtach scripting options
        result = {
            'numNodes': 'nodes',
            'jobTime': 'time',
            'partition': 'partition'
        }
        b = result.get(key, None)
        if b is None:
            return None
        else:
            a = "#SBATCH --"
            c = "=" + str(value)
            return a + b + c

    def __software_packages(self, temp_file):
        """

        :param temp_file:
        """
        temp_file.write(bytes("\n\n# Load Modules\n", self._encode))
        for key, value in self.\
                _config['requirements']['SoftwarePackages'].items():
            module = "module load {}".format(key)
            if value is not None:
                module += "/" + str(value.get('version', None))
            temp_file.write(bytes(module + "\n", 'UTF-8'))

    def __deploy_charliecloud(self, temp_file):
        """

        :param temp_file:
        """
        temp_file.write(bytes("\n# Deploy Charliecloud Container\n", self._encode))
        # TODO: better error handling?
        cc_task = self._config_req['CharliecloudRequirement']
        cc_deploy = "srun ch-tar2dir " + str(cc_task['source']) + " " + \
                    str(cc_task.get('tarDir', '/var/tmp')) + "\n"
        temp_file.write(bytes(cc_deploy, self._encode))

    def __deploy_bee_orchestrator(self, temp_file):
        """

        :param temp_file:
        """
        temp_file.write(bytes("\n# Launch BEE\n", self._encode))
        bee_deploy = [
            "screen -S bee_orc -d -m " +
            "(cd " + self._file_loc + " ; python3 -m bee_orchestrator -o -t " +
            self._task_name + ") ",
            "screen -X -S bee_orc quit"
        ]
        for data in bee_deploy:
            temp_file.write(bytes(data + "\n", self._encode))
