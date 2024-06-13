#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-foqa-3
#
#SBATCH --output=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --error=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --time=7-0
#SBATCH -c 1
#SBATCH --mem=32G
#SBATCH --mail-user=$USER@seas.upenn.edu
#SBATCH --mail-type=END

source slurm/env.sh
srun python bench_fanoutqa.py full
srun python bench_fanoutqa.py root-fc
srun python bench_fanoutqa.py baseline
