#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-small-leaf-webarena-openai
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
source slurm/webarena-env.sh
curl -X GET ${RESTART_URL}
sleep 300
python bench_webarena.py --config small-leaf --model-class openai --large-model gpt-4o-2024-05-13 --small-model gpt-3.5-turbo-0125 --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/openai/small-leaf 
