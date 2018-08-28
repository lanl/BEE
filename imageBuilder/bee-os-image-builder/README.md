# CC-CentOS7

This directory contains the scripts used to generate the Chameleon KVM and
bare-metal CentOS 7 images. It relies on diskimage-builder.

There are a couple variants of images it can produce, assembled using the
needed elements:

* `base`
* `gpu` - Includes CUDA8 framework
* `fpga` - Includes Altera Nallatech tools

Images are created with [diskimage-builder](http://docs.openstack.org/developer/diskimage-builder)

## Quickstart

```
sudo install-reqs.sh         # install tools and dependencies
python create-image.py base  # create the "base" iamge with most recent cloud image
```

## Requirements

Installed by `install-reqs.sh`

* qemu-utils:
  * CentOS: `yum install qemu-img`, may also require epel-release
  * Ubuntu: `apt-get install qemu-disk`
* diskimage-builder: `pip install diskimage-builder`

## Usage

The main script takes the variant and revision number.

`python create-image.py --help`.

The output is dumped to a temporary folder.

At the end of its execution, the script provides the Glance command that can be
used to upload the image to an existing OpenStack infrastructure.

The other scripts in the `elements` directory are invoked by create-image.sh.
This script does the following:

* Download a CentOS 7 cloud image from upstream
* Customize it for Chameleon (see `elements` directory for details)
* Generate an image compatible with OpenStack KVM and bare-metal

The image must then be uploaded and registered with Glance (currently done
manually, by running the Glance command given at the end of execution).
