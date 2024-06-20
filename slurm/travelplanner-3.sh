#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-tp-3
#
#SBATCH --output=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --error=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --time=7-0
#SBATCH -c 1
#SBATCH --mem=128G
#SBATCH --mail-user=andrz@seas.upenn.edu
#SBATCH --mail-type=END

source slurm/env.sh
srun python bench_travelplanner.py full
srun python bench_travelplanner.py root-fc
srun python bench_travelplanner.py baseline
