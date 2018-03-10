# Some charliecloud notes:


# Launching tasks with Charliecloud tar balls:
The allocation must be made from the same window that bee_orc_ctl.py is run, 
    before running bee_orc_ctl.py.

    bee_launcher.py -r use this if you want to use the images already unpacked
      
# This launcher uses whatever nodes are in the allocation
The script that is run by the task must be specified in general_run and the
desired mpirun command must be in the script.
  i.e. mpirun -np X ch-run <args>

   If we want to pick specifid nodes it would be an easy change
   i.e. we can unpack and/or run using constraints with srun 
    (--nodelist="cn31 cn32")
    However its probably not worth it.

   Using some examples I have in my ~/share/bee_cc_share directory I might be 
  able to implement this with the mpi_run option 
