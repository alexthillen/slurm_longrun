#!/bin/bash
#SBATCH --account=a-large-sc
#SBATCH --job-name=sbatch_longrun_example
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=1
#SBATCH --time=00:02:00
#SBATCH --output=run_job.log
#SBATCH --error=run_job.err
#SBATCH --partition=debug # normal
#SBATCH --environment=./ngc_pt_jan.toml 

set -eo pipefail

python $SLURM_SUBMIT_DIR/my_script.py

