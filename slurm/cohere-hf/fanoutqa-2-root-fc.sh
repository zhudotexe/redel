#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-root-fc-fanoutqa-cohere-hf
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
python bench_fanoutqa.py --config root-fc --model-class cohere-hf --large-model CohereForAI/c4ai-command-r-plus-08-2024 --small-model CohereForAI/c4ai-command-r-08-2024 --save-dir /nlpgpu/data/andrz/redel/experiments/fanoutqa/cohere-hf/root-fc --engine-timeout 1800
