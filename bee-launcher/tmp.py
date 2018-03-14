       map_by = run_conf['script']
            map_num = run_conf['script']
            cmd = ['mpirun']
            cmd.append(run_conf['script'])
        if 'SLURM_JOBID' in os.environ:
            if 'host' in run_conf:
                cprint("HERE BCL ", run_conf, "red")
                exit()



        cprint("HERE task_conf: " + str(self.__task_conf['general_run']),"cyan")
        cprint("HERE task_conf: " + str(self.__task_conf['general_run'][1]['script']),"red")
        exit()

      
