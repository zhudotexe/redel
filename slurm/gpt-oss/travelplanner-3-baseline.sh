#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-baseline-travelplanner-gpt-oss
#SBATCH --output=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --error=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --time=7-0
#SBATCH --nodes=1
#SBATCH -c 16
#SBATCH --mem=400G
#SBATCH --gpus=8
#SBATCH --mail-user=andrz@seas.upenn.edu
#SBATCH --mail-type=END,FAIL
#SBATCH --constraint=48GBgpu

source slurm/env.sh
export VLLM_WORKER_MULTIPROC_METHOD=spawn
python bench_travelplanner.py --config baseline --model-class gpt-oss --large-model openai/gpt-oss-120b --small-model openai/gpt-oss-20b --save-dir /nlpgpu/data/andrz/redel/experiments/travelplanner/gpt-oss/baseline --engine-timeout 1800
