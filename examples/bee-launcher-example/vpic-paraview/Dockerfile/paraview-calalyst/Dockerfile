from cjy7117/ubuntu-ompi

USER root

#ENV http_proxy 'http://proxyout.lanl.gov:8080'
#ENV https_proxy 'http://proxyout.lanl.gov:8080'
#ENV no_proxy 'localhost,127.0.0.1'

#RUN echo 'Acquire::http::Proxy "http://proxyout.lanl.gov:8080";' >> /etc/apt/apt.conf.d/docker-clean

RUN apt-get update

RUN apt-get -y install \
  autoconf\
#  cmake\
#  gcc\
#  git\
 # gfortran\
 # g++\
 # libtool\
  #libva-dev\
 # openssh-server\
 # pkg-config\
 # python\
 # python-dev\
 # python-pip\
 # xutils-dev\
 # wget \
  libpthread-stubs0-dev

# install MPI
#RUN wget https://www.open-mpi.org/software/ompi/v2.0/downloads/openmpi-2.0.2.tar.gz
#RUN tar -xzf openmpi-2.0.2.tar.gz
#RUN cd ./openmpi-2.0.2 && ./configure CC=gcc CXX=g++ FC=gfortran && make -j 8 all && make install
#RUN (echo "LD_LIBRARY_PATH=/usr/local/lib"; echo "") >> /etc/environment
#ENV LD_LIBRARY_PATH=/usr/local/lib

# needed by mesa
RUN pip install mako

# build mesa
WORKDIR /usr/local
# this link will expire as mesa gets older and then become stable in an old release
# download, unpack, and remove tar file...keeps image smaller and reduces number of layers
RUN wget mesa.freedesktop.org/archive/older-versions/13.x/13.0.6/mesa-13.0.6.tar.gz && tar xvzf mesa-13.0.6.tar.gz && rm mesa-13.0.6.tar.gz

WORKDIR /usr/local/mesa-13.0.6

RUN autoreconf -fi
RUN ./configure \
    --enable-osmesa\
    --disable-glx \
    --disable-driglx-direct\ 
    --disable-dri\ 
    --disable-egl \
    --with-gallium-drivers=swrast 
#    --enable-gallium-osmesa \
#    --enable-gallium-llvm=yes \
#    --with-llvm-shared-libs \
#    CXXFLAGS="-O2 -g -DDEFAULT_SOFTWARE_DEPTH_BITS=31" \
#    CFLAGS="-O2 -g -DDEFAULT_SOFTWARE_DEPTH_BITS=31" \
#    --disable-xvmc \
#    --disable-dri \
#    --with-dri-drivers="" \
#    --with-gallium-drivers="swrast" \
#    --enable-texture-float \
#    --disable-shared-glapi \
#    --with-egl-platforms="" \
#    --prefix=/work/apps/mesa/9.2.2/llvmpipe

RUN make -j 8; make install

#RUN ln -s /usr/local/mesa-11.2.1/lib/gallium/libOSMesa.so /usr/local/lib

# build glu
ENV C_INCLUDE_PATH '/usr/local/mesa-13.0.6/include'
ENV CPLUS_INCLUDE_PATH '/usr/local/mesa-13.0.6/include'
WORKDIR /usr/local
RUN git clone http://anongit.freedesktop.org/git/mesa/glu.git

WORKDIR /usr/local/glu
RUN ./autogen.sh --enable-osmesa
RUN ./configure --enable-osmesa
RUN make -j 8
RUN make install


# get more recent cmake
RUN mkdir /usr/local/cmake-3
WORKDIR /usr/local/cmake-3
RUN wget  https://cmake.org/files/v3.5/cmake-3.5.2-Linux-x86_64.tar.gz
RUN tar -xzf cmake-3.5.2-Linux-x86_64.tar.gz
ENV PATH /usr/local/cmake-3/cmake-3.5.2-Linux-x86_64/bin:$PATH



# checkout paraview
WORKDIR /usr/local

RUN git clone https://gitlab.kitware.com/paraview/paraview.git
WORKDIR /usr/local/paraview

RUN git checkout v5.2.0

RUN git submodule init
RUN git submodule update

RUN mkdir /usr/local/paraview.bin

# build paraview
WORKDIR /usr/local/paraview.bin
RUN cmake \
  -DBUILD_TESTING=OFF \
  -DCMAKE_BUILD_TYPE=Release \
  -DPARAVIEW_ENABLE_CATALYST=ON  \
  -DPARAVIEW_ENABLE_PYTHON=ON \
  -DPARAVIEW_BUILD_QT_GUI=OFF \
  -DVTK_USE_X=OFF \
  -DOPENGL_INCLUDE_DIR=/usr/local/mesa-13.0.6/include \
  -DOPENGL_gl_LIBRARY=/usr/local/mesa-13.0.6/lib/libOSMesa.so \
  -DVTK_OPENGL_HAS_OSMESA=ON \
  -DOSMESA_INCLUDE_DIR=/usr/local/mesa-13.0.6/include \
  -DOSMESA_LIBRARY=/usr/local/mesa-13.0.6/lib/libOSMesa.so \
  -DPARAVIEW_USE_MPI=ON \
  /usr/local/paraview
 
RUN make -j 8
RUN make install
RUN cp /usr/local/lib/paraview-5.2/*.* /usr/local/lib/



