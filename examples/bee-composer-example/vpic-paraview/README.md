This example (vpic-paraview) requires interaction with ParaView client on users desktop/laptop. This readme file shows how to connect ParaView client to remote ParaView server running on a cluster.

* The example is tested with ParaView 5.2.0.

1. Launch this BeeFlow example. If success, the user should see two kinds of output. One is the output from VPIC. Another is the ParaView server, which should be looks like these:

	- Connection URL: cs://paraview-server-bee-master:11111
	- Accepting connection(s): paraview-server-bee-master:11111
	
   Since VPIC continues output timestep information, the output of ParaView server may get pushed out of the console, so please check it by scrolling the console up. 

2. Setup a ssh tunnel from user’s desktop/laptop to the remote ParaView server (on port 11111 by default). 
	1. If `bee_orc_ctl.py` runs on the headnode of the cluster, only one ssh tunnel needs to be setup. Run the following command in a new terminal and keep it open (this keeps the ssh session alive).
		- `ssh -L 11111:localhost:11111 <username>@<host>`
	2. If `bee_orc_ctl.py` runs on one of the compute node of the cluster, two ssh tunnels will need setup. Run the following command in a new terminal:
		- `ssh -L 11111:localhost:11111 <username>@<host>`	
           
	   Via the head node (connected too in the above step) of the cluster. Run the following command, keep the terminal open (keep ssh session alive).
		- `ssh -L 11111:localhost:11111 <username>@<node_name>` 

4. Now we have the port 11111 on users desktop/laptop forwarded to the port 11111 on the machine where ParaView server is running. 
	1. Open ParaView client on users desktop/laptop and click ‘connect’ button (third button on the first row). 
	2. In the pop-up window ('Choose Server Configuration'), click ‘Add Server’. 
	3. Fill in the following:
		- Name: `beeflow_example`
		- Server Type: `Client/Server`
		- Host: `localhost`
		- Port: `11111` 
	4. Select 'Configure'
	5. Leave Startup Type as ‘Manual’ and click ‘Save’. 
	6. Select the server we just added and click ‘connect’. Wait for a few seconds, we should see ‘Client connected.’ in the console that we ran `bee_orc_ctl.py`.

5. View in-situ visualization file through the ParaView client. 
	1. Click ‘Open’ button (first button on the first row). 
	2. Select directory in ‘/mnt/docker_share/my_test’. 
		- This is where VPIC is outputting result files. 
	3. Select any of the output files (*.pvtp or *.vtp) and click ‘ok’ to view them. 
		- Remember to click the eye-shaped button next to the file in the Pipeline Browser to make objects viewable.
