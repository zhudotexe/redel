#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-all-webarena-gpt-oss
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
dockerd-rootless.sh &
DOCKER_PID=$!
sleep 15
source slurm/webarena-env.sh
bash slurm/webarena-startup.sh
sleep 600
python bench_webarena.py --config full --model-class gpt-oss --large-model openai/gpt-oss-120b --small-model openai/gpt-oss-20b --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/gpt-oss/full --engine-timeout 1800
bash slurm/webarena-startup.sh
sleep 600
python bench_webarena.py --config root-fc --model-class gpt-oss --large-model openai/gpt-oss-120b --small-model openai/gpt-oss-20b --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/gpt-oss/root-fc --engine-timeout 1800
bash slurm/webarena-startup.sh
sleep 600
python bench_webarena.py --config baseline --model-class gpt-oss --large-model openai/gpt-oss-120b --small-model openai/gpt-oss-20b --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/gpt-oss/baseline --engine-timeout 1800
bash slurm/webarena-startup.sh
sleep 600
python bench_webarena.py --config small-leaf --model-class gpt-oss --large-model openai/gpt-oss-120b --small-model openai/gpt-oss-20b --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/gpt-oss/small-leaf --engine-timeout 1800
bash slurm/webarena-startup.sh
sleep 600
python bench_webarena.py --config small-all --model-class gpt-oss --large-model openai/gpt-oss-120b --small-model openai/gpt-oss-20b --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/gpt-oss/small-all --engine-timeout 1800
bash slurm/webarena-startup.sh
sleep 600
python bench_webarena.py --config small-baseline --model-class gpt-oss --large-model openai/gpt-oss-120b --small-model openai/gpt-oss-20b --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/gpt-oss/small-baseline --engine-timeout 1800
bash slurm/webarena-startup.sh
sleep 600
python bench_webarena.py --config short-context --model-class gpt-oss --large-model openai/gpt-oss-120b --small-model openai/gpt-oss-20b --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/gpt-oss/short-context --engine-timeout 1800
bash slurm/webarena-startup.sh
sleep 600
python bench_webarena.py --config short-baseline --model-class gpt-oss --large-model openai/gpt-oss-120b --small-model openai/gpt-oss-20b --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/gpt-oss/short-baseline --engine-timeout 1800
bash slurm/webarena-startup.sh
sleep 600
kill $DOCKER_PID