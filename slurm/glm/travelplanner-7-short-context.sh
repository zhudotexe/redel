#!/bin/bash
#
#SBATCH --partition=dgx-b200
#SBATCH --job-name=rd-short-context-travelplanner-glm
#SBATCH --output=/vast/projects/ccb/lab/andrz/logs/%j.%x.log
#SBATCH --error=/vast/projects/ccb/lab/andrz/logs/%j.%x.log
#SBATCH --time=7-0
#SBATCH --nodes=1
#SBATCH -c 16
#SBATCH --mem=512G
#SBATCH --gpus=4
#SBATCH --mail-user=andrz@seas.upenn.edu
#SBATCH --mail-type=END,FAIL


source slurm/env.sh
export VLLM_WORKER_MULTIPROC_METHOD=spawn
python bench_travelplanner.py --config short-context --model-class glm --large-model zai-org/GLM-4.6-FP8 --small-model None --save-dir /vast/projects/ccb/lab/andrz/redel/experiments/travelplanner/glm/short-context --engine-timeout 1800
