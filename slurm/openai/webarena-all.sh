#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-all-webarena-openai
#SBATCH --output=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --error=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --time=7-0
#SBATCH --nodes=1
#SBATCH -c 1
#SBATCH --mem=256G
#SBATCH --gpus=0
#SBATCH --mail-user=andrz@seas.upenn.edu
#SBATCH --mail-type=END,FAIL
#SBATCH --nodelist=nlpgpu05


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
python bench_webarena.py --config full --model-class openai --large-model gpt-4o-2024-05-13 --small-model gpt-3.5-turbo-0125 --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/openai/full
curl -X GET ${RESTART_URL}
sleep 600
python bench_webarena.py --config root-fc --model-class openai --large-model gpt-4o-2024-05-13 --small-model gpt-3.5-turbo-0125 --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/openai/root-fc
curl -X GET ${RESTART_URL}
sleep 600
python bench_webarena.py --config baseline --model-class openai --large-model gpt-4o-2024-05-13 --small-model gpt-3.5-turbo-0125 --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/openai/baseline
curl -X GET ${RESTART_URL}
sleep 600
python bench_webarena.py --config small-leaf --model-class openai --large-model gpt-4o-2024-05-13 --small-model gpt-3.5-turbo-0125 --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/openai/small-leaf
curl -X GET ${RESTART_URL}
sleep 600
python bench_webarena.py --config small-all --model-class openai --large-model gpt-4o-2024-05-13 --small-model gpt-3.5-turbo-0125 --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/openai/small-all
curl -X GET ${RESTART_URL}
sleep 600
python bench_webarena.py --config small-baseline --model-class openai --large-model gpt-4o-2024-05-13 --small-model gpt-3.5-turbo-0125 --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/openai/small-baseline
curl -X GET ${RESTART_URL}
sleep 600
python bench_webarena.py --config short-context --model-class openai --large-model gpt-4o-2024-05-13 --small-model gpt-3.5-turbo-0125 --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/openai/short-context
curl -X GET ${RESTART_URL}
sleep 600
python bench_webarena.py --config short-baseline --model-class openai --large-model gpt-4o-2024-05-13 --small-model gpt-3.5-turbo-0125 --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/openai/short-baseline
kill $DOCKER_PID