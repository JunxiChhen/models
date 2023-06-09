# Copyright (c) 2023 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
#
# THIS IS A GENERATED DOCKERFILE.
#
# This file was assembled from multiple pieces, whose use is documented
# throughout. Please refer to the TensorFlow dockerfiles documentation
# for more information.

ARG MAX_PYT_BASE_IMAGE="intel/intel-extension-for-pytorch"
ARG MAX_PYT_BASE_TAG="xpu-max"

FROM ${MAX_PYT_BASE_IMAGE}:${MAX_PYT_BASE_TAG}

RUN curl -fsSL https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS-2023.PUB | apt-key add -
RUN echo "deb [trusted=yes] https://apt.repos.intel.com/oneapi all main " > /etc/apt/sources.list.d/oneAPI.list

RUN apt-get update && \
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates \
    intel-oneapi-mpi-devel=2021.9.0-43482 \
    intel-oneapi-ccl=2021.9.0-43543 \
    && \
  rm -rf /var/lib/apt/lists/*

WORKDIR /workspace/pytorch-max-series-resnet50v1-5-training

COPY quickstart/image_recognition/pytorch/resnet50v1_5/training/gpu/README.md README.md 
COPY models/image_recognition/pytorch/resnet50v1_5/training/gpu models/image_recognition/pytorch/resnet50v1_5/training/gpu
COPY quickstart/image_recognition/pytorch/resnet50v1_5/training/gpu/training_plain_format.sh quickstart/training_plain_format.sh
COPY quickstart/image_recognition/pytorch/resnet50v1_5/training/gpu/ddp_training_plain_format_nchw.sh quickstart/ddp_training_plain_format_nchw.sh

COPY LICENSE licenses/LICENSE
COPY third_party licenses/third_party
