#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-foqa-score
#SBATCH --output=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --error=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --time=2-0
#SBATCH --nodes=1
#SBATCH -c 16
#SBATCH --mem=256G
#SBATCH --gpus=8
#SBATCH --mail-user=andrz@seas.upenn.edu
#SBATCH --mail-type=END,FAIL
#SBATCH --constraint=48GBgpu

# usage: sbatch slurm/score_fanoutqa_vllm.sh org/model-id path/to/results.jsonl

set -euxo pipefail

source slurm/env.sh
source slurm/fanout-eval-env.sh
export VLLM_WORKER_MULTIPROC_METHOD=spawn
export PYTHONUNBUFFERED=1

NUM_GPUS=$(nvidia-smi --list-gpus | wc -l)
MODEL_NAME="${1:-Qwen/Qwen3-4B}"
echo "launching vllm judge with model MODEL_NAME"

# launch vllm and wait for healthy
vllm serve "$MODEL_NAME" \
  --tensor-parallel-size $NUM_GPUS \
  --max-model-len 16384 \
  --enable-chunked-prefill \
  --max-num-batched-tokens 8192 &
VLLM_PID=$!
export FANOUTQA_JUDGE_MODEL="$MODEL_NAME"
export FANOUTQA_OPENAI_API_KEY=dummy
export FANOUTQA_OPENAI_API_BASE="http://127.0.0.1:8000/v1"

until curl --output /dev/null --silent --fail "$FANOUTQA_OPENAI_API_BASE/health"; do
    printf '.'
    sleep 5
done

# score
python score_fanoutqa.py "${@:2}"

# cleanup vllm
kill $VLLM_PID
# ding dong I am done
printf '\a'
