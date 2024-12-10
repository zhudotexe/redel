#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-all-webarena-qwen
#SBATCH --output=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --error=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --time=7-0
#SBATCH --nodes=1
#SBATCH -c 16
#SBATCH --mem=400G
#SBATCH --gpus=8
#SBATCH --mail-user=andrz@seas.upenn.edu
#SBATCH --mail-type=END,FAIL
#SBATCH --nodelist=nlpgpu05
#SBATCH --constraint=48GBgpu

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
python bench_webarena.py --config full --model-class qwen --large-model Qwen/Qwen2.5-72B-Instruct --small-model Qwen/Qwen2.5-7B-Instruct --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/qwen/full --engine-timeout 1800
curl -X GET ${RESTART_URL}
sleep 600
python bench_webarena.py --config root-fc --model-class qwen --large-model Qwen/Qwen2.5-72B-Instruct --small-model Qwen/Qwen2.5-7B-Instruct --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/qwen/root-fc --engine-timeout 1800
curl -X GET ${RESTART_URL}
sleep 600
python bench_webarena.py --config baseline --model-class qwen --large-model Qwen/Qwen2.5-72B-Instruct --small-model Qwen/Qwen2.5-7B-Instruct --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/qwen/baseline --engine-timeout 1800
curl -X GET ${RESTART_URL}
sleep 600
python bench_webarena.py --config small-leaf --model-class qwen --large-model Qwen/Qwen2.5-72B-Instruct --small-model Qwen/Qwen2.5-7B-Instruct --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/qwen/small-leaf --engine-timeout 1800
curl -X GET ${RESTART_URL}
sleep 600
python bench_webarena.py --config small-all --model-class qwen --large-model Qwen/Qwen2.5-72B-Instruct --small-model Qwen/Qwen2.5-7B-Instruct --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/qwen/small-all --engine-timeout 1800
curl -X GET ${RESTART_URL}
sleep 600
python bench_webarena.py --config small-baseline --model-class qwen --large-model Qwen/Qwen2.5-72B-Instruct --small-model Qwen/Qwen2.5-7B-Instruct --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/qwen/small-baseline --engine-timeout 1800
curl -X GET ${RESTART_URL}
sleep 600
python bench_webarena.py --config short-context --model-class qwen --large-model Qwen/Qwen2.5-72B-Instruct --small-model Qwen/Qwen2.5-7B-Instruct --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/qwen/short-context --engine-timeout 1800
curl -X GET ${RESTART_URL}
sleep 600
python bench_webarena.py --config short-baseline --model-class qwen --large-model Qwen/Qwen2.5-72B-Instruct --small-model Qwen/Qwen2.5-7B-Instruct --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/qwen/short-baseline --engine-timeout 1800kill $DOCKER_PID