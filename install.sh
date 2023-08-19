#!/usr/bin/env python
#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # no color

isPackageNotInstalled() {
  $1 --version &> /dev/null
  if [ $? -eq 0 ]; then
    echo "$1: Already installed"
  elif [[ $(uname -p) == 'arm' ]]; then
    install_dir=$HOME/miniconda
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh
    bash  Miniconda3-latest-MacOSX-arm64.sh -b -p  $install_dir
    export PATH=$install_dir/bin:$PATH
  else
    install_dir=$HOME/anaconda3
    wget https://repo.anaconda.com/archive/Anaconda3-2020.11-Linux-x86_64.sh
    bash Anaconda3-2020.11-Linux-x86_64.sh -b -p  $install_dir
    export PATH=$install_dir/bin:$PATH

  fi
}

isPackageNotInstalled conda

conda init bash
. ~/.bashrc
conda env create -f environment.yml
conda activate propius

if [ "$1" == "--cuda" ]; then
    wget https://developer.download.nvidia.com/compute/cuda/10.2/Prod/local_installers/cuda_10.2.89_440.33.01_linux.run
    sudo apt-get purge nvidia-* -y
    sudo sh -c "echo 'blacklist nouveau\noptions nouveau modeset=0' > /etc/modprobe.d/blacklist-nouveau.conf"
    sudo update-initramfs -u
    sudo sh cuda_10.2.89_440.33.01_linux.run --override --driver --toolkit --samples --silent
    export PATH=$PATH:/usr/local/cuda-10.2/
    conda install cudatoolkit=10.2 -y
fi

echo "Downloading FEMNIST dataset(about 327M)..."
wget -O ./datasets/femnist.tar.gz https://fedscale.eecs.umich.edu/dataset/femnist.tar.gz

echo "Dataset downloaded, now decompressing..."
tar -xf ./datasets/femnist.tar.gz -C ./datasets

echo "Removing compressed file..."
rm -f ./datasets/femnist.tar.gz

echo -e "${GREEN}FEMNIST dataset downloaded!${NC}"
