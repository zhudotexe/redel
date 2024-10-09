#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-wa-short-context
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
srun python bench_webarena.py --config short-context --large-model gpt-4o-2024-05-13 --small-model gpt-3.5-turbo-0125 --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/test/short-context
