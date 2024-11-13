#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-short-baseline-webarena-mistral
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
python bench_webarena.py --config short-baseline --model-class mistral --large-model mistralai/Mistral-Large-Instruct-2407 --small-model mistralai/Mistral-Small-Instruct-2409 --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/mistral/short-baseline --engine-timeout 1800
