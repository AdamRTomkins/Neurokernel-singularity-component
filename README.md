# Neurokernel Component on ShARC

This module will allow a neurokernel component on ShARC, in conjunction with the ShARC singularity container, using the following script

qrsh -P flybrain -q flybrain.q

module load libs/CUDA/7.5.18/binary

singularity shell -B mynvdriver:/nvlib,mynvdriver:/nvbin,/usr/local/packages/libs/CUDA/7.5.18/binary/cuda/bin:/cuda neurokernel.img

export PATH=/usr/local/nvidia/bin:/usr/local/cuda/bin:/miniconda/bin:/miniconda/bin::/cuda:/nvbin:/usr/local/packages/libs/CUDA/7.5.18/binary/cuda/bin:/usr/local/scripts/:/usr/lib64/qt-3.3/bin:/usr/local/sge/live/bin/lx-amd64:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/opt/singularity/bin:/home/co1art/bin:/bin:/sbin:/usr/bin:/usr/sbin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin

cd Neurokernel-singularity-component
python compute.py



