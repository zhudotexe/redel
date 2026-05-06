#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-q3
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

# launch kiwix
free_port=$(python -c 'import socket; s=socket.socket(); s.bind(("", 0)); print(s.getsockname()[1]); s.close()')
export KIWIX_HOST_FOQA="http://127.0.0.1:$free_port"
experiments/fanoutqa/_wikipedia/kiwix-tools/kiwix-serve --port "$free_port" --threads 32 experiments/fanoutqa/_wikipedia/wikipedia_en_all_nopic_2023-09.zim &

python bench_fanoutqa.py \
  --config root-fc \
  --model-class qwen3.5 \
  --large-model Qwen/Qwen3.5-122B-A10B \
  --small-model Qwen/Qwen3-4B-Thinking-2507 \
  --save-dir /nlpgpu/data/andrz/redel/experiments/fanoutqa/rdrl-v3/qwen3.5 \
  --engine-timeout 1800
