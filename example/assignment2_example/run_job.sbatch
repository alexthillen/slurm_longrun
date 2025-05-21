#!/bin/bash
#SBATCH --account=a-large-sc
#SBATCH --job-name=sbatch_longrun_example_assignment2
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=1
#SBATCH --time=00:03:00
#SBATCH --output=run_example_assignment2.log
#SBATCH --error=run_example_assignment2.err
#SBATCH --partition=debug
#SBATCH --environment=/iopsstor/scratch/cscs/athillen/assignment-2/ngc_pt_jan.toml
#SBATCH --export=ALL

set -eo pipefail
echo "START TIME: $(date)"

srun bash -c "python $SLURM_SUBMIT_DIR/example/assignment2_example/assignment_2/train.py \
    --learning-rate 5e-5 \
    --training-steps 1000 \
    --batch-size 1 \
    --lr-warmup-steps 100"

echo "END TIME: $(date)"
