#!/bin/bash

set -e

"${SHELL}" <(curl -Ls micro.mamba.pm/install.sh) < /dev/null

conda init --all
micromamba shell init -s bash

micromamba env create -f build_tools/circle/doc_environment.yml -n sklearn-dev --yes
echo "micromamba activate sklearn-dev" >> $HOME/.bashrc

# Note that `micromamba activate sklearn-dev` doesn't work, it must be run by the
# user (same applies to `conda activate`)

# Enables users to activate environment without having to specify the full path
echo "envs_dirs:
  - /home/codespace/micromamba/envs" > /opt/conda/.condarc
