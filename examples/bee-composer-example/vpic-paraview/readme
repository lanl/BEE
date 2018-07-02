This example (vpic-paraview) requires interaction with ParaView client on users desktop/laptop. This readme file shows how to connect ParaView client to remote ParaView server running on a cluster.

* The example is tested with ParaView 5.2.0.

Step 1: Launch this BeeFlow example. If success, the user should see two kinds of output. One is the output from VPIC. Another is the ParaView server, which should be looks like these:
	Connection URL: cs://paraview-server-bee-master:11111
	Accepting connection(s): paraview-server-bee-master:11111

Since VPIC continues output timestep information, the output of ParaView server may get pushed out of the console, so please check it by scrolling the console up. 

Step 2: Setup a ssh tunnel from user’s desktop/laptop to the remote ParaView server (on port 11111 by default). 
	(1) if bee_orc_ctl.py runs on the headnode of the cluster, only one ssh tunnel need to be setup. run the following command in a new terminal and keep it open (keep ssh session alive).
	ssh -L 11111:localhost:11111 <username>@<host>
	(2) if ee_orc_ctl.py runs on one of the compute node of the cluster, two ssh tunnels need to be setup. run the following command in a new terminal:
	ssh -L 11111:localhost:11111 <username>@<host> 
User should be in the head node of the cluster. Now run the command in the same terminal and keep it open (keep ssh session alive).
	ssh -L 11111:localhost:11111 <username>@<node_name> 

Step 3: Now we have the port 11111 on users desktop/laptop forwarded to the port 11111 on the machine where ParaView server is running. Open ParaView client on users desktop/laptop. Click ‘connect’ button (third button on the first row). In the pop-up window, click ‘Add Server’. Fill in the name as ‘beeflow_example’, Server Type as ‘Client/Server’, Host as ‘localhost’, and Port as ‘11111’. Next, click ‘Configure’. Leave Startup Type as ‘Manual’ and click ‘Save’. Now we have a new server setup in ParaView client. Select the server we just added and click ‘connect’. Wait for a few section, we should see ‘Client connected.’ in the console that we run bee_orc_ctl.py.

Step 4: View in-situ visualization file through the ParaView client. Click ‘Open’ button (first button on the first row). Select directory in ‘/mnt/docker_share/my_test’. This is where VPIC is outputting result files. Select any of the output files (*.pvtp or *.vtp) and click ‘ok’ to view them. Remember to click the eye-shaped button next to the file in the Pipeline Browser to make objects viewable.


