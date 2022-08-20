# CLAMR-FFMPEG WORKFLOW

These workflows execute the `CLAMR` AMR simulation and then `ffmpeg`, represented in a single CWL file.

Files:
* cf.cwl - clamr CWL file
* cf-darwin.cwl - clamr CWL file that runs on the LANL darwin cluster.
* cf-no-owrite.cwl - clamr CWL file no overwrite, ffmpeg to fails if movie file exists, useful to test FAILED step.
* copyContainer_containerName.cwl - A workflow which demonstrates the ability to copy a container tarball from some mount point to the BEE container archive.
* dockerFile_containerName.cwl - A workflow which demonstrates the ability to build a container from a Dockerfile and store that container in the BEE container archive.
* dockerPull.cwl - A workflow which demonstrates the ability to pull a container from a container registry and store that container in the BEE container archive. 


## Container registry interactions

Any workflow which interacts with the container registry may need to authenticate. In the case of Docker and Dockerhub, traditionally users execute `docker login` from the command line before attempting to interact with the container registry. With Charliecloud, the environment variables `CH_USERNAME` and `CH_PASSWORD` are used for the username/password combinations Dockerhub requires. In cases where Charliecloud interacts with a Gitlab container registry, tokens are used instead of passwords. A description about how to use Gitlab tokens follows.

Gitlab uses tokens to authenticate users at a command line. Tokens are intended to be shorter-lived than passwords, though it is possible to generate tokens without an expiration date. In contrast to username/password authentication methods, token based passwords provide multiple levels of access per user account. A user may have multiple active tokens at the same time, with independent levels of access assiciated with each. In order to generate a token for the workflows featured in this directory, you will need access to a gitlab container registry owned by qwofford at https://git.lanl.gov/qwofford/containerhub/. Please contact qwofford@lanl.gov for access. A description about how to generate tokens for that repository follows.

Once you have gained access to https://git.lanl.gov/qwofford/containerhub/, you will need to generate a token. Visit the git project webpage and navigate to the `Settings->Access Tokens` page. Enter a token name, and select permissions which are appropriate for your use case. Selecting all of the read permissions with no expiration date is a reasonable choice. Click the "Create project access token" link. Save this token somewhere! I use a directory called `~/Tokens` to manage my auth tokens for gitlab. I store tokens in this directory with filenames that reflect the project, for example: `~/Tokens/git.lanl.gov%qwofford%containerhub`. This is just a convention and any other method to store passwords will work as well. After a token is generated you can set `CH_USERNAME` to your username, which owns the token you just created. Then set `CH_PASSWORD` to the token you just generated. To test, try to pull a container. To find a container to pull, access the gitlab web page and click "Packages & Registries", then "Container Registry". You might try pulling from the command line (ch-image pull) before running the workflows featured below.


