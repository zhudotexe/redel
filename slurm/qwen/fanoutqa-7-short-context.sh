#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-short-context-fanoutqa-qwen
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

python bench_fanoutqa.py --config short-context --model-class qwen --large-model Qwen/Qwen2.5-72B-Instruct --small-model Qwen/Qwen2.5-7B-Instruct --save-dir /nlpgpu/data/andrz/redel/experiments/fanoutqa/qwen/short-context --engine-timeout 1800
