#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-all-travelplanner-claude
#SBATCH --output=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --error=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --time=7-0
#SBATCH --nodes=1
#SBATCH -c 1
#SBATCH --mem=32G
#SBATCH --gpus=0
#SBATCH --mail-user=andrz@seas.upenn.edu
#SBATCH --mail-type=END,FAIL


source slurm/env.sh
export VLLM_WORKER_MULTIPROC_METHOD=spawn
python bench_travelplanner.py --config full --model-class claude --large-model claude-3-5-sonnet-20241022 --small-model claude-3-5-haiku-20241022 --save-dir /nlpgpu/data/andrz/redel/experiments/travelplanner/claude/full
python bench_travelplanner.py --config root-fc --model-class claude --large-model claude-3-5-sonnet-20241022 --small-model claude-3-5-haiku-20241022 --save-dir /nlpgpu/data/andrz/redel/experiments/travelplanner/claude/root-fc
python bench_travelplanner.py --config baseline --model-class claude --large-model claude-3-5-sonnet-20241022 --small-model claude-3-5-haiku-20241022 --save-dir /nlpgpu/data/andrz/redel/experiments/travelplanner/claude/baseline
python bench_travelplanner.py --config small-leaf --model-class claude --large-model claude-3-5-sonnet-20241022 --small-model claude-3-5-haiku-20241022 --save-dir /nlpgpu/data/andrz/redel/experiments/travelplanner/claude/small-leaf
python bench_travelplanner.py --config small-all --model-class claude --large-model claude-3-5-sonnet-20241022 --small-model claude-3-5-haiku-20241022 --save-dir /nlpgpu/data/andrz/redel/experiments/travelplanner/claude/small-all
python bench_travelplanner.py --config small-baseline --model-class claude --large-model claude-3-5-sonnet-20241022 --small-model claude-3-5-haiku-20241022 --save-dir /nlpgpu/data/andrz/redel/experiments/travelplanner/claude/small-baseline
python bench_travelplanner.py --config short-context --model-class claude --large-model claude-3-5-sonnet-20241022 --small-model claude-3-5-haiku-20241022 --save-dir /nlpgpu/data/andrz/redel/experiments/travelplanner/claude/short-context
python bench_travelplanner.py --config short-baseline --model-class claude --large-model claude-3-5-sonnet-20241022 --small-model claude-3-5-haiku-20241022 --save-dir /nlpgpu/data/andrz/redel/experiments/travelplanner/claude/short-baseline