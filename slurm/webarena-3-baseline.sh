#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-wa-baseline
#
#SBATCH --output=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --error=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --time=7-0
#SBATCH -c 1
#SBATCH --mem=128G
#SBATCH --mail-user=andrz@seas.upenn.edu
#SBATCH --mail-type=END,FAIL

source slurm/env.sh
source slurm/webarena-env.sh
srun python bench_webarena.py baseline
