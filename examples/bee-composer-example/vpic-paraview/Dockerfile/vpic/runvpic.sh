#/bin/bash

# this function pulls information from a config file to do a run
function run_config {
    # Pull information from the config file
    file=$1
    FLAG=0
    file_list=()
    script_list=()
    while IFS= read -r line
    do
        if [ "$line" == "# End" ]; then
            break
        fi
        if [ "$line" == "# Folder Name" ]; then
            FLAG=1
            continue
        fi
        if [ "$line" == "# Deck" ]; then
            FLAG=2
            continue
        fi
        if [ "$line" == "# Files" ]; then
            FLAG=3
            continue
        fi
        if [ "$line" == "# Scripts" ]; then
            FLAG=4
            continue
        fi
        if [ $FLAG == 1 ]; then
            folder_name="$line"
            continue
        fi
        if [ $FLAG == 2 ]; then
            deck_name="$line"
            continue
        fi
        if [ $FLAG == 3 ]; then
            file_list+=("$line")
            continue
        fi
        if [ $FLAG == 4 ]; then
            script_list+=("$line")
        fi
    done <"$file"

    # Create Folder
    mkdir -p /mnt/docker_share/$folder_name

    # Copy Files
    for i in "${file_list[@]}"; do
        cp $i /mnt/docker_share/$folder_name
    done

    # Copy Scripts
    for i in "${script_list[@]}"; do
        cp $i /mnt/docker_share/$folder_name
    done

    # Configure insitu.py and move it
    rm insitu.py
    touch insitu.py
    for i in "${script_list[@]}"; do
        filename="${i##*/}"
        scriptname="${filename%.*}"
        printf "import $scriptname\n" >> insitu.py
    done
    printf "def RequestDataDescription(datadescription):\n" >> insitu.py
    for i in "${script_list[@]}"; do
        filename="${i##*/}"
        scriptname="${filename%.*}"
        printf "\t$scriptname.RequestDataDescription(datadescription)\n" >> insitu.py
    done
    printf "def DoCoProcessing(datadescription):\n" >> insitu.py
    for i in "${script_list[@]}"; do
        filename="${i##*/}"
        scriptname="${filename%.*}"
        printf "\t$scriptname.DoCoProcessing(datadescription)\n" >> insitu.py
    done
    mv insitu.py /mnt/docker_share/$folder_name

    # Compile deck and configure libraries
    cd /mnt/docker_share/vpic.bin
    export CPLUS_INCLUDE_PATH=/mnt/docker_share/vpic/src/util/catalyst/
    cd /mnt/docker_share/$folder_name
    ../vpic.bin/bin/vpic $deck_name
    export LD_LIBRARY_PATH=/usr/local/paraview.bin/lib
    echo "Sleeping 5 to wait for filehandle."
    sleep 5
    echo "Launching..."
    # Get executable name
    temp="${deck_name##*/}"
    executable="${temp%.*}.Linux"
    # Run it
    LD_LIBRARY_PATH=/usr/local/paraview.bin/lib 
    #mpirun --mca btl_tcp_if_include eth0 --hostfile /mnt/docker_share/hostfile /mnt/docker_share/$folder_name/$executable
}

# Build VPIC
cd /mnt/docker_share/vpic.bin
#cmake \
#    -DUSE_CATALYST=ON \
#    -DCMAKE_BUILD_TYPE=Release \
#    /mnt/docker_share/vpic
#make -j16

# PUT RUNS BELOW

# Run 1 using vpic_config
run_config "/mnt/docker_share/vpic_config"

# Run 2 using vpic_config2
#run_config "/mnt/docker_share/vpic_config2"
