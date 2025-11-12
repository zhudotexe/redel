import dataclasses
import os


CLUSTERS = {
    "nlpgpu": {
        "project_home": "/nlpgpu/data/andrz",
        "partition": "p_nlp",
        "max_mem_gb": 400,
        "mem_per_gpu": 64,
        "gpu_constraints": "#SBATCH --constraint=48GBgpu",
    },
    "betty": {
        "project_home": "/vast/projects/ccb/lab/andrz",
        "partition": "dgx-b200",
        "max_mem_gb": 512,
        "mem_per_gpu": 180,
        "gpu_constraints": "",
    }
}

HEADER_TEMPLATE = """\
#!/bin/bash
#
#SBATCH --partition={partition}
#SBATCH --job-name=rd-{config}-{bench}-{model_class}
#SBATCH --output={project_home}/logs/%j.%x.log
#SBATCH --error={project_home}/logs/%j.%x.log
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
{bench_startup}
"""
RUN_TEMPLATE = """\
python bench_{bench}.py \
--config {config} \
--model-class {model_class} \
--large-model {large_model} \
--small-model {small_model} \
--save-dir {project_home}/redel/experiments/{bench}/{model_class}/{config} \
{engine_extras}
{bench_extras}
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


@dataclasses.dataclass
class ModelConfig:
    model_class: str
    large: str
    small: str | None
    size: int
    extras: str
    benches: list[str] = dataclasses.field(default_factory=lambda: BENCHES)
    cluster: str = "nlpgpu"


MODELS = [
    # model class, large, small, size, extras
    ModelConfig(model_class="openai", large="gpt-4o-2024-05-13", small="gpt-3.5-turbo-0125", size=0, extras=""),
    ModelConfig(
        model_class="mistral",
        large="mistralai/Mistral-Large-Instruct-2407",
        small="mistralai/Mistral-Small-Instruct-2409",
        size=8,
        extras="--engine-timeout 1800",  # 30 min timeout per trial
    ),
    ModelConfig(
        model_class="claude", large="claude-3-5-sonnet-20241022", small="claude-3-5-haiku-20241022", size=0, extras=""
    ),
    ModelConfig(
        model_class="qwen",
        large="Qwen/Qwen2.5-72B-Instruct",
        small="Qwen/Qwen2.5-7B-Instruct",
        size=8,
        extras="--engine-timeout 1800",  # 30 min timeout per trial
    ),
    ModelConfig(
        model_class="cohere-hf",
        large="CohereForAI/c4ai-command-r-plus-08-2024",
        small="CohereForAI/c4ai-command-r-08-2024",
        size=8,
        extras="--engine-timeout 1800",  # 30 min timeout per trial
    ),
    # oct25
    ModelConfig(
        model_class="qwen3",
        large="Qwen/Qwen3-30B-A3B-Thinking-2507",
        small="Qwen/Qwen3-4B-Thinking-2507",
        size=8,
        extras="--engine-timeout 1800",  # 30 min timeout per trial
    ),
    ModelConfig(
        model_class="gpt-oss",
        large="openai/gpt-oss-120b",
        small="openai/gpt-oss-20b",
        size=8,
        extras="--engine-timeout 1800",  # 30 min timeout per trial
    ),
    ModelConfig(
        model_class="glm",
        large="zai-org/GLM-4.6-FP8",
        small=None,
        size=4,  # on PARCC
        cluster="betty",
        extras="--engine-timeout 1800",  # 30 min timeout per trial
        benches=["fanoutqa", "travelplanner"]
    ),
]


def main():
    for model in MODELS:
        cluster = CLUSTERS[model.cluster]

        project_home = cluster["project_home"]
        partition = cluster["partition"]
        cpus = min(16, max(1, model.size * 4))
        mem = str(min(cluster["max_mem_gb"], max(32, cluster["mem_per_gpu"] * model.size))) + "G"
        gpus = model.size
        gpuconstraint = cluster["gpu_constraints"] if model.size else ""

        for bench in model.benches:
            # WA needs extra env vars
            if bench == "webarena":
                bench_extras = "bash slurm/webarena-startup.sh\nsleep 600"
                bench_startup = (
                    "dockerd-rootless.sh &\n"
                    "DOCKER_PID=$!\n"
                    "sleep 15\n"
                    "source slurm/webarena-env.sh\n"
                    "bash slurm/webarena-startup.sh\n"
                    "sleep 600"
                )
                footer = "kill $DOCKER_PID"
                if int(mem[:-1]) < 256:
                    mem = "256G"
            else:
                bench_startup = ""
                bench_extras = ""
                footer = ""

            all_commands = []

            for idx, config in enumerate(CONFIGS):
                if model.small is None and "small" in config:
                    continue
                header = HEADER_TEMPLATE.format(
                    partition=partition,
                    project_home=project_home,
                    config=config,
                    bench=bench,
                    model_class=model.model_class,
                    cpus=cpus,
                    mem=mem,
                    gpus=gpus,
                    gpuconstraint=gpuconstraint,
                    bench_startup=bench_startup,
                ).strip()
                content = RUN_TEMPLATE.format(
                    project_home=project_home,
                    bench_extras=bench_extras,
                    config=config,
                    bench=bench,
                    model_class=model.model_class,
                    large_model=model.large,
                    small_model=model.small,
                    engine_extras=model.extras,
                ).strip()
                all_commands.append(content)
                os.makedirs(f"slurm/{model.model_class}", exist_ok=True)
                with open(f"slurm/{model.model_class}/{bench}-{idx + 1}-{config}.sh", "w") as f:
                    f.write(header)
                    f.write("\n")
                    f.write(content)
                    f.write("\n")
                    f.write(footer)

            # write all file
            header = HEADER_TEMPLATE.format(
                partition=partition,
                project_home=project_home,
                config="all",
                bench=bench,
                model_class=model.model_class,
                cpus=cpus,
                mem=mem,
                gpus=gpus,
                gpuconstraint=gpuconstraint,
                bench_startup=bench_startup,
            ).strip()
            with open(f"slurm/{model.model_class}/{bench}-all.sh", "w") as f:
                f.write(header)
                f.write("\n")
                f.write("\n".join(all_commands))
                f.write("\n")
                f.write(footer)


if __name__ == "__main__":
    main()
