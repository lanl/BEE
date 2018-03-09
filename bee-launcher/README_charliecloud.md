# Some charliecloud notes:


# Launching tasks with Charliecloud tar balls:
The allocation must be made from the same window that bee_orc_ctl.py is run, 
    before running bee_orc_ctl.py.

    bee_launcher.py -r use this if you want to use the images already unpacked
      
# This launcher uses whatever nodes are in the allocation
   If we want to pick specifid nodes it would be an easy change
   i.e. we can unpack and/or run using constraints with srun 
    (--nodelist="cn31 cn32")
