#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-full-travelplanner-qwen3
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
python bench_travelplanner.py --config full --model-class qwen3 --large-model Qwen/Qwen3-235B-A22B-Thinking-2507 --small-model Qwen/Qwen3-4B-Thinking-2507 --save-dir /nlpgpu/data/andrz/redel/experiments/travelplanner/qwen3/full --engine-timeout 1800
