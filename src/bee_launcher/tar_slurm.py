# system
from tempfile import NamedTemporaryFile
from subprocess import Popen, PIPE, \
    STDOUT, CalledProcessError
from termcolor import cprint


class SlurmAdaptee:
    def __init__(self, config, file_loc, task_name):
        self._config = config
        self._config_req = self._config['requirements']
        self._file_loc = file_loc
        self._task_name = task_name
        self._encode = 'UTF-8'

        # Termcolor
        self.error_color = "red"
        self.warning_color = "yellow"
        self.message_color = "cyan"

    def specific_allocate(self):
        """
        Create sbatch file utilizing Beefile's desfined 'requirements' then
        execute this sbatch via subprocess.
        At this moment this system must be run on the login node of the cluster
        :return: unique job id associated with successful allocation
        """
        tmp_f = NamedTemporaryFile()
        tmp_f.write(bytes("#!\\bin\\bash\n\n", 'UTF-8'))
        #######################################################################
        # Prepare SBATCH file
        # TODO: further document
        #######################################################################
        if self._config_req.get('ResourceRequirement') is not None:
            self.__resource_requirement(temp_file=tmp_f)
        else:
            cprint("[" + self._task_name + "] ResourceRequirement key is required for"
                                           " allocation", self.error_color)
        if self._config_req.get('SoftwarePackages') is not None:
            self.__software_packages(temp_file=tmp_f)
        if self._config_req.get('EnvVarRequirements') is not None:
            self.__env_variables(temp_file=tmp_f)
        if self._config_req.get('CharliecloudRequirement') is not None:
            self.__deploy_charliecloud(temp_file=tmp_f)
        self.__deploy_bee_orchestrator(temp_file=tmp_f)

        tmp_f.seek(0)
        out, err = self._run_sbatch(tmp_f.name)
        tmp_f.close()
        return out, err

    def specific_schedule(self):
        pass

    def specific_shutdown(self):
        pass

    def specific_move_file(self):
        pass

    # private / supporting functions
    def _run_salloc(self):
        pass

    def _run_sbatch(self, file):
        cmd = ['sbatch', file]
        """
        # TODO: remove test code
        print(cmd)
        command = ['mousepad', file]
        p = Popen(command, stdout=PIPE, stderr=STDOUT)
        p.communicate()
        exit(0)
        """
        out, err = self._run_popen_safe(command=cmd, err_exit=False)
        return out, err

    def __resource_requirement(self, temp_file):
        """
        sbatch resource requirements, add to file
        :param temp_file: Target sbatch file (named temp file)
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
        Generate single line for sbatch file
            e.g. #SBATCH --nodes=2
        :param key: sbatch key
                https://slurm.schedmd.com/sbatch.html
        :param value: associated with key
                Currently not verification!
        :return: sbatch line (string)
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
        Module load <target(s)>, add to file
        :param temp_file: Target sbatch file (named temp file)
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
        Identify and un-tar Charliecloud container, add to file
        :param temp_file: Target sbatch file (named temp file)
        """
        temp_file.write(bytes("\n# Deploy Charliecloud Container\n", self._encode))
        # TODO: better error handling?
        # TODO: options for build/pull?
        for cc in self._config_req['CharliecloudRequirement']:
            cc_task = self._config_req['CharliecloudRequirement'][cc]
            cc_deploy = "srun ch-tar2dir " + str(cc_task['source']) + " " + \
                         str(cc_task.get('tarDir', '/var/tmp')) + "\n"
            temp_file.write(bytes(cc_deploy, self._encode))

    def __env_variables(self, temp_file):
        """
        Added source <key> <value> and export <key> <value>:$<key>
        in order to establish the environment
        :param temp_file: Target sbatch file (named temp file)
        """
        temp_file.write(bytes("\n# Environmental Requirements\n", self._encode))
        env_dict = self._config_req['EnvVarRequirements']
        if env_dict.get('envDef') is not None:
            for key, value in env_dict.get('envDef').items():
                export = "export {} {}:${}".format(str(key), str(value), str(key))
                temp_file.write(bytes(export + "\n", 'UTF-8'))
        if env_dict.get('sourceDef') is not None:
            for key, value in env_dict.get('sourceDef').items():
                source = "source {}".format(str(key))
                if value is not None:
                    source += str(value)
                temp_file.write(bytes(source + "\n", 'UTF-8'))

    def __deploy_bee_orchestrator(self, temp_file):
        """
        Scripting to launch bee_orchestrator, add to file
        :param temp_file: Target sbatch file (named temp file)
        """
        temp_file.write(bytes("\n# Launch BEE\n", self._encode))
        bee_deploy = [
            "python3 -m bee-orchestrator -o -t " + self._file_loc +
            "/" + self._task_name + ") "
        ]
        for data in bee_deploy:
            temp_file.write(bytes(data + "\n", self._encode))

    def _run_popen_safe(self, command, shell=False, err_exit=True):
        """
        Run defined command via Popen, try/except statements
        built in and message output when appropriate
        :param command: Command to be run
        :param shell: Shell flag (boolean), default false
        :param err_exit: Exit upon error, default True
        :return: tuple [out, err] from p.communicate() based upon results
                    of command run via subprocess
                None, error message returned if except reached
                    and err_exit=False
        """
        self._handle_message("Executing: " + str(command))
        try:
            p = Popen(command, shell, stdout=PIPE, stderr=STDOUT)
            out, err = p.communicate()
            return out, err
        except CalledProcessError as e:
            self._handle_message(msg="Error during - " + str(command) + "\n" +
                                 str(e), color=self.error_color)
            if err_exit:
                exit(1)
            else:
                return None, str(e)
        except OSError as e:
            self._handle_message(msg="Error during - " + str(command) + "\n" +
                                 str(e), color=self.error_color)
            if err_exit:
                exit(1)
            else:
                return None, str(e)

    # Task management support functions (private)
    def _handle_message(self, msg, color=None):
        """
        :param msg: To be printed to console
        :param color: If message is be colored via termcolor
                        Default = none (normal print)
        """

        if color is None:
            print("[{}] {}".format(self._task_name, msg))
        else:
            cprint("[{}] {}".format(self._task_name, msg), color)
