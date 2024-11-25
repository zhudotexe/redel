#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-short-baseline-webarena-cohere-hf
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
source slurm/webarena-env.sh
curl -X GET ${RESTART_URL}
sleep 300
python bench_webarena.py --config short-baseline --model-class cohere-hf --large-model CohereForAI/c4ai-command-r-plus-08-2024 --small-model CohereForAI/c4ai-command-r-08-2024 --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/cohere-hf/short-baseline --engine-timeout 1800