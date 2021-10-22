### PREPARE:
    gcc >= 5
    Cmake >= 3.19.6
    wget https://repo.continuum.io/archive/Anaconda3-5.0.0-Linux-x86_64.sh -O anaconda3.sh
    chmod +x anaconda3.sh
    ./anaconda3.sh -b -p ~/anaconda3
    ./anaconda3/bin/conda create -yn pytorch
    export PATH=~/anaconda3/bin:$PATH
    source ./anaconda3/bin/activate pytorch
    pip install sklearn onnx
    pip install lark-parser hypothesis
    conda install numpy ninja pyyaml mkl mkl-include setuptools cmake cffi typing_extensions future six requests dataclasses psutil
    export CMAKE_PREFIX_PATH=${CONDA_PREFIX:-"$(dirname $(which conda))/../"}
    export work_space=/home/sdp  (you can get the summary.log in this path where the models performance and accuracy write)   

### build pytorch and intel-pytorch-extension
    git clone https://gitlab.devtools.intel.com/intel-pytorch-extension/pytorch-spr.git pytorch
    git checkout dev
    git submodule sync
    git submodule update --init --recursive
    cd ..
    git clone https://github.com/intel-innersource/frameworks.ai.pytorch.ipex-cpu.git ipex-cpu-dev
    cd ipex-cpu-dev
    git checkout cpu-device
    git submodule sync
    git submodule update --init --recursive
    cd ../pytorch
    python setup.py install
    cd ../ipex-cpu-dev
    python setup.py install

### build jemalloc
    cd ..
    git clone  https://github.com/jemalloc/jemalloc.git    
    cd jemalloc
    git checkout c8209150f9d219a137412b06431c9d52839c7272
    ./autogen.sh
    ./configure --prefix=your_path(eg: /home/tdoux/tdoux/jemalloc/)
    make
    make install

### build vision
    cd ..
    git clone https://github.com/pytorch/vision
    cd vision
    git checkout v0.8.0
    python setup.py install