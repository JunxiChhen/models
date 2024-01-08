#!/usr/bin/env bash
#
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
#

# setup.sh
#  - install OS pkgs
#  - should create virtual env & install pip  requirement.txt
#  - git clones & applying patches

set -e
apt-get update && apt-get install -y python3-venv protobuf-compiler
python3 -m venv $PWD/venv
. ./venv/bin/activate

pip uninstall google-auth-oauthlib tb-nightly -y
pip install -r requirements.txt



