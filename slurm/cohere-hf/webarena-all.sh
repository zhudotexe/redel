#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-all-webarena-cohere-hf
#SBATCH --output=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --error=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --time=7-0
#SBATCH --nodes=1
#SBATCH -c 16
#SBATCH --mem=400G
#SBATCH --gpus=8
#SBATCH --mail-user=andrz@seas.upenn.edu
#SBATCH --mail-type=END,FAIL
#SBATCH --nodelist=nlpgpu04,nlpgpu05,nlpgpu08
#SBATCH --constraint=48GBgpu

source slurm/env.sh
export VLLM_WORKER_MULTIPROC_METHOD=spawn
dockerd-rootless.sh &
DOCKER_PID=$!
sleep 15
source slurm/webarena-env.sh
bash slurm/webarena-startup.sh
sleep 600
python bench_webarena.py --config full --model-class cohere-hf --large-model CohereForAI/c4ai-command-r-plus-08-2024 --small-model CohereForAI/c4ai-command-r-08-2024 --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/cohere-hf/full --engine-timeout 1800
curl -X GET ${RESTART_URL}
sleep 600
python bench_webarena.py --config root-fc --model-class cohere-hf --large-model CohereForAI/c4ai-command-r-plus-08-2024 --small-model CohereForAI/c4ai-command-r-08-2024 --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/cohere-hf/root-fc --engine-timeout 1800
curl -X GET ${RESTART_URL}
sleep 600
python bench_webarena.py --config baseline --model-class cohere-hf --large-model CohereForAI/c4ai-command-r-plus-08-2024 --small-model CohereForAI/c4ai-command-r-08-2024 --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/cohere-hf/baseline --engine-timeout 1800
curl -X GET ${RESTART_URL}
sleep 600
python bench_webarena.py --config small-leaf --model-class cohere-hf --large-model CohereForAI/c4ai-command-r-plus-08-2024 --small-model CohereForAI/c4ai-command-r-08-2024 --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/cohere-hf/small-leaf --engine-timeout 1800
curl -X GET ${RESTART_URL}
sleep 600
python bench_webarena.py --config small-all --model-class cohere-hf --large-model CohereForAI/c4ai-command-r-plus-08-2024 --small-model CohereForAI/c4ai-command-r-08-2024 --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/cohere-hf/small-all --engine-timeout 1800
curl -X GET ${RESTART_URL}
sleep 600
python bench_webarena.py --config small-baseline --model-class cohere-hf --large-model CohereForAI/c4ai-command-r-plus-08-2024 --small-model CohereForAI/c4ai-command-r-08-2024 --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/cohere-hf/small-baseline --engine-timeout 1800
curl -X GET ${RESTART_URL}
sleep 600
python bench_webarena.py --config short-context --model-class cohere-hf --large-model CohereForAI/c4ai-command-r-plus-08-2024 --small-model CohereForAI/c4ai-command-r-08-2024 --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/cohere-hf/short-context --engine-timeout 1800
curl -X GET ${RESTART_URL}
sleep 600
python bench_webarena.py --config short-baseline --model-class cohere-hf --large-model CohereForAI/c4ai-command-r-plus-08-2024 --small-model CohereForAI/c4ai-command-r-08-2024 --save-dir /nlpgpu/data/andrz/redel/experiments/webarena/cohere-hf/short-baseline --engine-timeout 1800
curl -X GET ${RESTART_URL}
sleep 600
kill $DOCKER_PID