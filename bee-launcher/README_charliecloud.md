# Some charliecloud notes:

Unpacking on all allocated nodes when using -l


# Launching tasks with Charliecloud tar balls:
The allocation must be made from the same window that bee_orc_ctl.py is run, 
    before running bee_orc_ctl.py.

    bee_launcher.py -r use this if you want to use the images already unpacked
      
# The BEE Charliecloud launcher uses whatever nodes are in the allocation
    when using the general_run option the desired mpirun command must be in the 
    script.
  i.e. mpirun -np X ch-run <args>

    mpirun has many options such as -host or -H to specify nodes to run on 
           -np number of process (default uses all cores/threads)
           and -map-by ppr:n:node to map to n cores per node 
           or  -map-by ppr:n:sockets to map to n cores per socket
           
           
   If we want to pick specified nodes to unpack the would be an easy change
   i.e. we can unpack and/or run using constraints with srun 
    (--nodelist="cn31 cn32")
    mpirun -host cn31,cn32 or "cn31,cn32" or "cn31","cn32" 
    or we can do things like use -r relative using a certain number of nodes
    However its probably not worth it. It would most likely be advantageous to 
    have the images on all the nodes.

   Using some examples I have in my ~/share/bee_cc_share directory I might be 
  able to implement this with the mpi_run option 

  Note: 
node_list, map_by and map_num are used only for mpi_run
if you use general run you can specify -map-by ppr:n:node or ppr:n:socket
and -host or -H cn30,cn31 etc. there are many other flags you can specify with
mpirun yourself so mpi_run might not even be necessary

This leaves room for using tasking models that do not depend on mpi

