#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-root-fc-travelplanner-openai
#SBATCH --output=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --error=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --time=7-0
#SBATCH --nodes=1
#SBATCH -c 1
#SBATCH --mem=32G
#SBATCH --gpus=0
#SBATCH --mail-user=andrz@seas.upenn.edu
#SBATCH --mail-type=END,FAIL


source slurm/env.sh
export VLLM_WORKER_MULTIPROC_METHOD=spawn

python bench_travelplanner.py --config root-fc --model-class openai --large-model gpt-4o-2024-05-13 --small-model gpt-3.5-turbo-0125 --save-dir /nlpgpu/data/andrz/redel/experiments/travelplanner/openai/root-fc 
