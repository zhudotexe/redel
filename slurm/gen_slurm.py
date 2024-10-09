TEMPLATE = """\
#!/bin/bash
#
#SBATCH --partition=p_nlp
#SBATCH --job-name=rd-{config}-{bench}-{model_class}
#SBATCH --output=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --error=/nlpgpu/data/andrz/logs/%j.%x.log
#SBATCH --time=7-0
#SBATCH --nodes=1
#SBATCH -c {cpus}
#SBATCH --mem={mem}
#SBATCH --gpus={gpus}
#SBATCH --mail-user=andrz@seas.upenn.edu
#SBATCH --mail-type=END,FAIL
{gpuconstraint}

source slurm/env.sh
export VLLM_WORKER_MULTIPROC_METHOD=spawn

{bench_extras}
python bench_{bench}.py \
--config {config} \
--large-model {large_model} \
--small-model {small_model} \
--save-dir /nlpgpu/data/andrz/redel/experiments/{bench}/{model_class}
"""
BENCHES = ["fanoutqa", "travelplanner", "webarena"]
CONFIGS = [
    "full",
    "root-fc",
    "baseline",
    "small-leaf",
    "small-all",
    "small-baseline",
    "short-context",
    "short-baseline",
]
MODELS = [
    # model class, large, small, size
    # ("openai", "gpt-4o-2024-05-13", "gpt-3.5-turbo-0125", 0),
    ("mistral", "mistralai/Mistral-Large-Instruct-2407", "mistralai/Mistral-Small-Instruct-2409", 8),
]


def main():
    for model_class, large_model, small_model, size in MODELS:
        cpus = min(16, max(1, size * 4))
        mem = str(min(400, max(32, 64 * size))) + "G"
        gpus = size
        gpuconstraint = "#SBATCH --constraint=48GBgpu" if size else ""

        for bench in BENCHES:
            # WA needs extra env vars
            bench_extras = "source slurm/webarena-env.sh" if bench == "webarena" else ""

            for idx, config in enumerate(CONFIGS):
                # no short context settings for TP
                if bench == "travelplanner" and idx > 5:
                    continue

                content = TEMPLATE.format(
                    config=config,
                    bench=bench,
                    model_class=model_class,
                    cpus=cpus,
                    mem=mem,
                    gpus=gpus,
                    gpuconstraint=gpuconstraint,
                    large_model=large_model,
                    small_model=small_model,
                    bench_extras=bench_extras,
                )
                with open(f"slurm/{model_class}/{bench}-{idx+1}-{config}.sh", "w") as f:
                    f.write(content)


if __name__ == "__main__":
    main()
