#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-short-baseline-webarena-claude
#SBATCH --output=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --error=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --time=7-0
#SBATCH --nodes=1
#SBATCH -c 1
#SBATCH --mem=256G
#SBATCH --gpus=0
#SBATCH --mail-user=andrz@seas.upenn.edu
#SBATCH --mail-type=END,FAIL
#SBATCH --nodelist=nlpgpu04,nlpgpu05,nlpgpu08


source slurm/env.sh
export VLLM_WORKER_MULTIPROC_METHOD=spawn
dockerd-rootless.sh &
DOCKER_PID=$!
sleep 15
source slurm/webarena-env.sh
bash slurm/webarena-startup.sh
sleep 600
curl -X GET ${RESTART_URL}
sleep 600
python bench_webarena.py --config short-baseline --model-class claude --large-model claude-3-5-sonnet-20241022 --small-model claude-3-5-haiku-20241022 --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/claude/short-baseline
kill $DOCKER_PID