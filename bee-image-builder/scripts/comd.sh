echo "==> Cloning and building CoMD"
#  Note that is all done via sudo, so you'll need to run as sudo too.
git clone https://github.com/exmatex/CoMD.git
cd CoMD/src-mpi
cp Makefile.vanilla Makefile
make
