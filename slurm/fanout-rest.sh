#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-foqa-rest
#
#SBATCH --output=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --error=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --time=7-0
#SBATCH -c 1
#SBATCH --mem=32G
#SBATCH --mail-user=andrz@seas.upenn.edu
#SBATCH --mail-type=END

source slurm/env.sh
srun python bench_fanoutqa.py small-leaf
srun python bench_fanoutqa.py small-all
srun python bench_fanoutqa.py small-baseline
srun python bench_fanoutqa.py short-context
srun python bench_fanoutqa.py short-baseline
