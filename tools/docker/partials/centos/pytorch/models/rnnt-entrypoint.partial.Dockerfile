ENV PATH="~/anaconda3/bin:${PATH}"
ENV LD_PRELOAD="/workspace/lib/tcmalloc/lib/libtcmalloc.so:/root/anaconda3/envs/pytorch/lib/libiomp5.so:$LD_PRELOAD"
ENV MALLOC_CONF="oversize_threshold:1,background_thread:true,metadata_thp:auto,dirty_decay_ms:9000000000,muzzy_decay_ms:9000000000"
ENV BASH_ENV=/root/.bash_profile
WORKDIR /workspace/
RUN yum install -y numactl mesa-libGL && \
    yum clean all && \
    echo "source activate pytorch" >> /root/.bash_profile