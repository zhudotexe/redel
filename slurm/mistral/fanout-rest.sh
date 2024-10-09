#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-foqa-rest
#
#SBATCH --output=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --error=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --time=7-0
#SBATCH --nodes=1
#SBATCH -c 16
#SBATCH --mem=400G
#SBATCH --gpus=8
#SBATCH --constraint=48GBgpu
#SBATCH --mail-user=andrz@seas.upenn.edu
#SBATCH --mail-type=END

source slurm/env.sh
srun python bench_fanoutqa.py --config small-leaf --large-model mistralai/Mistral-Large-Instruct-2407 --small-model mistralai/Mistral-Small-Instruct-2409 --save-dir /nlpgpu/data/andrz/redel/experiments/fanoutqa/mistral/small-leaf
srun python bench_fanoutqa.py --config small-all --large-model mistralai/Mistral-Large-Instruct-2407 --small-model mistralai/Mistral-Small-Instruct-2409 --save-dir /nlpgpu/data/andrz/redel/experiments/fanoutqa/mistral/small-all
srun python bench_fanoutqa.py --config small-baseline --large-model mistralai/Mistral-Large-Instruct-2407 --small-model mistralai/Mistral-Small-Instruct-2409 --save-dir /nlpgpu/data/andrz/redel/experiments/fanoutqa/mistral/small-baseline
srun python bench_fanoutqa.py --config short-context --large-model mistralai/Mistral-Large-Instruct-2407 --small-model mistralai/Mistral-Small-Instruct-2409 --save-dir /nlpgpu/data/andrz/redel/experiments/fanoutqa/mistral/short-context
srun python bench_fanoutqa.py --config short-baseline --large-model mistralai/Mistral-Large-Instruct-2407 --small-model mistralai/Mistral-Small-Instruct-2409 --save-dir /nlpgpu/data/andrz/redel/experiments/fanoutqa/mistral/short-baseline
