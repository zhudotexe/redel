#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-foqa-eval
#
#SBATCH --output=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --error=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --time=7-0
#SBATCH -c 1
#SBATCH --mem=32G

source slurm/fanout-eval-env.sh
for i in experiments/fanoutqa/test/**/results.jsonl; do
  srun python score_fanoutqa.py $i
done
