#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-all-travelplanner-mistral
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
python bench_travelplanner.py --config full --model-class mistral --large-model mistralai/Mistral-Large-Instruct-2407 --small-model mistralai/Mistral-Small-Instruct-2409 --save-dir /nlpgpu/data/andrz/redel/experiments/travelplanner/mistral/full --engine-timeout 1800
python bench_travelplanner.py --config root-fc --model-class mistral --large-model mistralai/Mistral-Large-Instruct-2407 --small-model mistralai/Mistral-Small-Instruct-2409 --save-dir /nlpgpu/data/andrz/redel/experiments/travelplanner/mistral/root-fc --engine-timeout 1800
python bench_travelplanner.py --config baseline --model-class mistral --large-model mistralai/Mistral-Large-Instruct-2407 --small-model mistralai/Mistral-Small-Instruct-2409 --save-dir /nlpgpu/data/andrz/redel/experiments/travelplanner/mistral/baseline --engine-timeout 1800
python bench_travelplanner.py --config small-leaf --model-class mistral --large-model mistralai/Mistral-Large-Instruct-2407 --small-model mistralai/Mistral-Small-Instruct-2409 --save-dir /nlpgpu/data/andrz/redel/experiments/travelplanner/mistral/small-leaf --engine-timeout 1800
python bench_travelplanner.py --config small-all --model-class mistral --large-model mistralai/Mistral-Large-Instruct-2407 --small-model mistralai/Mistral-Small-Instruct-2409 --save-dir /nlpgpu/data/andrz/redel/experiments/travelplanner/mistral/small-all --engine-timeout 1800
python bench_travelplanner.py --config small-baseline --model-class mistral --large-model mistralai/Mistral-Large-Instruct-2407 --small-model mistralai/Mistral-Small-Instruct-2409 --save-dir /nlpgpu/data/andrz/redel/experiments/travelplanner/mistral/small-baseline --engine-timeout 1800
python bench_travelplanner.py --config short-context --model-class mistral --large-model mistralai/Mistral-Large-Instruct-2407 --small-model mistralai/Mistral-Small-Instruct-2409 --save-dir /nlpgpu/data/andrz/redel/experiments/travelplanner/mistral/short-context --engine-timeout 1800
python bench_travelplanner.py --config short-baseline --model-class mistral --large-model mistralai/Mistral-Large-Instruct-2407 --small-model mistralai/Mistral-Small-Instruct-2409 --save-dir /nlpgpu/data/andrz/redel/experiments/travelplanner/mistral/short-baseline --engine-timeout 1800
