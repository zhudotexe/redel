#!/bin/zsh

source slurm/webarena-env.sh
python bench_webarena.py --config baseline --model-class openai --large-model gpt-4o-mini --small-model gpt-4o-mini --save-dir experiments/webarena/dev/baseline
