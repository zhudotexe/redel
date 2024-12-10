#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-all-fanoutqa-qwen
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
python bench_fanoutqa.py --config full --model-class qwen --large-model Qwen/Qwen2.5-72B-Instruct --small-model Qwen/Qwen2.5-7B-Instruct --save-dir /nlpgpu/data/andrz/redel/experiments/fanoutqa/qwen/full --engine-timeout 1800
python bench_fanoutqa.py --config root-fc --model-class qwen --large-model Qwen/Qwen2.5-72B-Instruct --small-model Qwen/Qwen2.5-7B-Instruct --save-dir /nlpgpu/data/andrz/redel/experiments/fanoutqa/qwen/root-fc --engine-timeout 1800
python bench_fanoutqa.py --config baseline --model-class qwen --large-model Qwen/Qwen2.5-72B-Instruct --small-model Qwen/Qwen2.5-7B-Instruct --save-dir /nlpgpu/data/andrz/redel/experiments/fanoutqa/qwen/baseline --engine-timeout 1800
python bench_fanoutqa.py --config small-leaf --model-class qwen --large-model Qwen/Qwen2.5-72B-Instruct --small-model Qwen/Qwen2.5-7B-Instruct --save-dir /nlpgpu/data/andrz/redel/experiments/fanoutqa/qwen/small-leaf --engine-timeout 1800
python bench_fanoutqa.py --config small-all --model-class qwen --large-model Qwen/Qwen2.5-72B-Instruct --small-model Qwen/Qwen2.5-7B-Instruct --save-dir /nlpgpu/data/andrz/redel/experiments/fanoutqa/qwen/small-all --engine-timeout 1800
python bench_fanoutqa.py --config small-baseline --model-class qwen --large-model Qwen/Qwen2.5-72B-Instruct --small-model Qwen/Qwen2.5-7B-Instruct --save-dir /nlpgpu/data/andrz/redel/experiments/fanoutqa/qwen/small-baseline --engine-timeout 1800
python bench_fanoutqa.py --config short-context --model-class qwen --large-model Qwen/Qwen2.5-72B-Instruct --small-model Qwen/Qwen2.5-7B-Instruct --save-dir /nlpgpu/data/andrz/redel/experiments/fanoutqa/qwen/short-context --engine-timeout 1800
python bench_fanoutqa.py --config short-baseline --model-class qwen --large-model Qwen/Qwen2.5-72B-Instruct --small-model Qwen/Qwen2.5-7B-Instruct --save-dir /nlpgpu/data/andrz/redel/experiments/fanoutqa/qwen/short-baseline --engine-timeout 1800
