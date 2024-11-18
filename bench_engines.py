import argparse
import dataclasses
import pathlib

from kani.engines import BaseEngine

from redel import DelegationBase
from redel.delegation import DelegateOne

parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True)
parser.add_argument("--model-class", required=True)
parser.add_argument("--large-model", required=True)
parser.add_argument("--small-model", required=True)
parser.add_argument("--save-dir", type=pathlib.Path, required=True)
parser.add_argument("--engine-timeout", type=int, default=600)


@dataclasses.dataclass
class ExperimentConfig:
    config: str
    model_class: str

    root_engine: BaseEngine
    delegate_engine: BaseEngine
    delegation_scheme: DelegationBase | None
    root_has_tools: bool
    save_dir: pathlib.Path
    engine_timeout: int


def get_engine(model_class: str, model_id: str, context_size: int = None):
    # ==== OPENAI ====
    if model_class == "openai":
        from kani.engines.openai import OpenAIEngine

        if model_id == "gpt-4o-2024-05-13":
            return OpenAIEngine(model="gpt-4o-2024-05-13", temperature=0, max_context_size=context_size)
        if model_id == "gpt-3.5-turbo-0125":
            return OpenAIEngine(model="gpt-3.5-turbo-0125", temperature=0, max_context_size=context_size)
    # ==== MISTRAL ====
    if model_class == "mistral":
        from kani.ext.vllm import VLLMEngine
        from kani.prompts.impl import MISTRAL_V3_PIPELINE
        from kani.prompts.impl.mistral import MistralFunctionCallingAdapter
        from vllm import SamplingParams

        if model_id == "mistralai/Mistral-Large-Instruct-2407":
            model = VLLMEngine(
                model_id="mistralai/Mistral-Large-Instruct-2407",
                prompt_pipeline=MISTRAL_V3_PIPELINE,
                max_context_size=context_size,
                model_load_kwargs={
                    "tensor_parallel_size": 8,
                    "tokenizer_mode": "auto",
                    # for more stability
                    "gpu_memory_utilization": 0.8,
                    "enforce_eager": True,
                    "enable_prefix_caching": True,
                },
                sampling_params=SamplingParams(temperature=0.7, max_tokens=2048),
            )
            return MistralFunctionCallingAdapter(model)
        if model_id == "mistralai/Mistral-Small-Instruct-2409":  # todo how to serve 2 models concurrently
            model = VLLMEngine(
                model_id="mistralai/Mistral-Small-Instruct-2409",
                prompt_pipeline=MISTRAL_V3_PIPELINE,
                max_context_size=context_size,
                model_load_kwargs={
                    "tensor_parallel_size": 8,
                    "tokenizer_mode": "auto",
                    "enforce_eager": True,
                },
                sampling_params=SamplingParams(temperature=0.7, max_tokens=2048),
            )
            return MistralFunctionCallingAdapter(model)
    # ==== CLAUDE ====
    if model_class == "claude":
        from kani.engines.anthropic import AnthropicEngine

        if model_id == "claude-3-5-sonnet-20241022":
            return AnthropicEngine(
                model="claude-3-5-sonnet-20241022", temperature=0, max_context_size=context_size or 150000
            )
        if model_id == "claude-3-5-haiku-20241022":
            return AnthropicEngine(
                model="claude-3-5-haiku-20241022", temperature=0, max_context_size=context_size or 150000
            )
    # ===== QWEN =====
    if model_class == "qwen":
        from utils.qwen import QwenFunctionCallingAdapter
        from kani.ext.vllm import VLLMEngine
        from vllm import SamplingParams

        if model_id == "Qwen/Qwen2.5-72B-Instruct":
            model = VLLMEngine(
                model_id="Qwen/Qwen2.5-72B-Instruct",
                max_context_size=context_size or 32768,
                model_load_kwargs={
                    "tensor_parallel_size": 8,
                    # for more stability
                    # "gpu_memory_utilization": 0.8,
                    # "enforce_eager": True,
                    "enable_prefix_caching": True,
                },
                sampling_params=SamplingParams(
                    # default from model card
                    repetition_penalty=1.05,
                    temperature=0.7,
                    top_p=0.8,
                    top_k=20,
                    # stability
                    max_tokens=2048,
                    min_tokens=1,
                ),
            )
            return QwenFunctionCallingAdapter(model)
        if model_id == "Qwen/Qwen2.5-7B-Instruct":
            model = VLLMEngine(
                model_id="Qwen/Qwen2.5-7B-Instruct",
                max_context_size=context_size or 32768,
                model_load_kwargs={
                    "tensor_parallel_size": 8,
                    # for more stability
                    "enable_prefix_caching": True,
                },
                sampling_params=SamplingParams(
                    # default from model card
                    repetition_penalty=1.05,
                    temperature=0.7,
                    top_p=0.8,
                    top_k=20,
                    # stability
                    max_tokens=2048,
                    min_tokens=1,
                ),
            )
            return QwenFunctionCallingAdapter(model)
    # ==== COHERE HF ====
    if model_class == "cohere-hf":
        from kani.ext.vllm import CommandRVLLMEngine
        from vllm import SamplingParams

        if model_id == "CohereForAI/c4ai-command-r-plus-08-2024":
            return CommandRVLLMEngine(
                model_id="CohereForAI/c4ai-command-r-plus-08-2024",
                max_context_size=context_size or 128000,
                model_load_kwargs={
                    "tensor_parallel_size": 8,
                    # for more stability
                    "gpu_memory_utilization": 0.8,
                    "enforce_eager": True,
                    "enable_prefix_caching": True,
                },
                sampling_params=SamplingParams(temperature=0.7, max_tokens=2048, min_tokens=1),
            )
        if model_id == "CohereForAI/c4ai-command-r-08-2024":
            return CommandRVLLMEngine(
                model_id="CohereForAI/c4ai-command-r-08-2024",
                max_context_size=context_size or 128000,
                model_load_kwargs={
                    "tensor_parallel_size": 8,
                    # for more stability
                    "enable_prefix_caching": True,
                },
                sampling_params=SamplingParams(temperature=0.7, max_tokens=2048, min_tokens=1),
            )
    # todo: cohere
    raise ValueError("unknown engine")


def get_experiment_config(delegation_scheme=DelegateOne) -> ExperimentConfig:
    args = parser.parse_args()
    experiment_config = args.config
    model_class = args.model_class
    large_model_id = args.large_model
    small_model_id = args.small_model
    save_dir = args.save_dir
    # - **full**: no root FC, gpt-4o everything
    if experiment_config == "full":
        root_engine = get_engine(model_class, large_model_id)
        delegate_engine = root_engine
        root_has_tools = False
    # - **root-fc**: root FC, gpt-4o everything
    elif experiment_config == "root-fc":
        root_engine = get_engine(model_class, large_model_id)
        delegate_engine = root_engine
        root_has_tools = True
    # - **baseline**: root FC, no delegation, gpt-4o
    elif experiment_config == "baseline":
        root_engine = get_engine(model_class, large_model_id)
        delegate_engine = root_engine
        root_has_tools = True
        delegation_scheme = None
    # - **small-leaf**: no root FC, gpt-4o root, gpt-3.5-turbo leaves
    elif experiment_config == "small-leaf":
        root_engine = get_engine(model_class, large_model_id)
        delegate_engine = get_engine(model_class, small_model_id)
        root_has_tools = False
    #     - **small-all**: no root FC, gpt-3.5-turbo everything
    elif experiment_config == "small-all":
        root_engine = get_engine(model_class, small_model_id)
        delegate_engine = root_engine
        root_has_tools = False
    #     - **small-baseline**: root FC, no delegation, gpt-3.5-turbo
    elif experiment_config == "small-baseline":
        root_engine = get_engine(model_class, small_model_id)
        delegate_engine = root_engine
        root_has_tools = True
        delegation_scheme = None
    # - **short-context**: no root FC, gpt-4o everything, limit to 8192 ctx
    elif experiment_config == "short-context":
        root_engine = get_engine(model_class, large_model_id, context_size=8192)
        delegate_engine = root_engine
        root_has_tools = False
    #     - **short-baseline**: root FC, no delegation, gpt-4o, 8192 ctx
    elif experiment_config == "short-baseline":
        root_engine = get_engine(model_class, large_model_id, context_size=8192)
        delegate_engine = root_engine
        root_has_tools = True
        delegation_scheme = None
    else:
        raise ValueError("invalid experiment config")

    print("========== CONFIG ==========")
    print("root engine:", root_engine.model)
    print("root ctx:", root_engine.max_context_size)
    print("root tools:", root_has_tools)
    print("delegation scheme:", delegation_scheme)
    if delegation_scheme:
        print("delegate engine:", delegate_engine.model)
        print("delegate ctx:", delegate_engine.max_context_size)
    print("saving to:", save_dir.resolve())
    print("============================")

    return ExperimentConfig(
        config=experiment_config,
        model_class=model_class,
        root_engine=root_engine,
        delegate_engine=delegate_engine,
        delegation_scheme=delegation_scheme,
        root_has_tools=root_has_tools,
        save_dir=save_dir,
        engine_timeout=args.engine_timeout,
    )
