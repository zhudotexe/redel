"""
Run the webarena experiments.

Usage: python bench_webarena.py <full|root-fc|baseline|small-leaf|small-all|small-baseline|short-context|short-baseline>

- **full**: no root FC, gpt-4o everything
- **root-fc**: root FC, gpt-4o everything
- **baseline**: root FC, no delegation, gpt-4o
- **small-leaf**: no root FC, gpt-4o root, gpt-3.5-turbo leaves
    - **small-all**: no root FC, gpt-3.5-turbo everything
    - **small-baseline**: root FC, no delegation, gpt-3.5-turbo
- **short-context**: no root FC, gpt-4o everything, limit to 8192 ctx
    - **short-baseline**: root FC, no delegation, gpt-4o, 8192 ctx
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import tqdm
from browser_env import ScriptBrowserEnv
from browser_env.auto_login import get_site_comb_from_filepath
from evaluation_harness import evaluator_router
from kani import ChatRole
from kani.engines.openai import OpenAIEngine

from redel import Kanpai, events
from redel.delegation.delegate_one import Delegate1Mixin
from redel.tools.webarena.harness import WebArenaHarness
from redel.tools.webarena.impl import WebArenaMixin
from redel.utils import read_jsonl

LOG_BASE = Path(__file__).parent / "experiments/webarena"
experiment_config = sys.argv[-1]
log = logging.getLogger("bench_webarena")

# ==== config ====
START_IDX = 0
END_IDX = 812
delegation_scheme = Delegate1Mixin
log_dir = LOG_BASE / "test" / experiment_config
# gross but whatever
# - **full**: no root FC, gpt-4o everything
if experiment_config == "full":
    root_engine = OpenAIEngine(model="gpt-4o", temperature=0)
    delegate_engine = root_engine
    long_engine = root_engine
    root_has_tools = False
# - **root-fc**: root FC, gpt-4o everything
elif experiment_config == "root-fc":
    root_engine = OpenAIEngine(model="gpt-4o", temperature=0)
    delegate_engine = root_engine
    long_engine = root_engine
    root_has_tools = True
# - **baseline**: root FC, no delegation, gpt-4o
elif experiment_config == "baseline":
    root_engine = OpenAIEngine(model="gpt-4o", temperature=0)
    delegate_engine = root_engine
    long_engine = root_engine
    root_has_tools = True
    delegation_scheme = None
# - **small-leaf**: no root FC, gpt-4o root, gpt-3.5-turbo leaves
elif experiment_config == "small-leaf":
    root_engine = OpenAIEngine(model="gpt-4o", temperature=0)
    delegate_engine = OpenAIEngine(model="gpt-3.5-turbo", temperature=0)
    long_engine = root_engine
    root_has_tools = False
#     - **small-all**: no root FC, gpt-3.5-turbo everything
elif experiment_config == "small-all":
    root_engine = OpenAIEngine(model="gpt-3.5-turbo", temperature=0)
    delegate_engine = root_engine
    long_engine = root_engine
    root_has_tools = False
#     - **small-baseline**: root FC, no delegation, gpt-3.5-turbo
elif experiment_config == "small-baseline":
    root_engine = OpenAIEngine(model="gpt-3.5-turbo", temperature=0)
    delegate_engine = root_engine
    long_engine = root_engine
    root_has_tools = True
    delegation_scheme = None
# - **short-context**: no root FC, gpt-4o everything, limit to 8192 ctx
elif experiment_config == "short-context":
    root_engine = OpenAIEngine(model="gpt-4o", temperature=0, max_context_size=8192)
    delegate_engine = root_engine
    long_engine = root_engine
    root_has_tools = False
#     - **short-baseline**: root FC, no delegation, gpt-4o, 8192 ctx
elif experiment_config == "short-baseline":
    root_engine = OpenAIEngine(model="gpt-4o", temperature=0, max_context_size=8192)
    delegate_engine = root_engine
    long_engine = root_engine
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
print("saving to:", log_dir.resolve())
print("============================")

# ==== webarena setup ====
wa_env = ScriptBrowserEnv(
    headless=True,
    observation_type="accessibility_tree",
    current_viewport_only=False,
    viewport_size={
        "width": 1280,
        "height": 720,
    },
    save_trace_enabled=False,
    sleep_after_execution=0,
)


# ==== main ====
async def run_one_trial(config_file: Path):
    # load config, update login cookies, save temp copy
    with open(config_file) as f:
        _c = json.load(f)
        intent = _c["intent"]
        task_id = _c["task_id"]
        # automatically login
        if _c["storage_state"]:
            cookie_file_name = os.path.basename(_c["storage_state"])
            comb = get_site_comb_from_filepath(cookie_file_name)
            temp_dir = tempfile.mkdtemp()
            # subprocess to renew the cookie
            subprocess.run([
                "python",
                "experiments/webarena/auto_login.py",
                "--auth_folder",
                temp_dir,
                "--site_list",
                *comb,
            ])
            _c["storage_state"] = f"{temp_dir}/{cookie_file_name}"
            assert os.path.exists(_c["storage_state"])
            # write a temp copy of the config file
            config_file = f"{temp_dir}/{os.path.basename(config_file)}"
            with open(config_file, "w") as f:
                json.dump(_c, f)

    # setup webarena env for the given trial
    harness = WebArenaHarness(config_file=config_file, env=wa_env)

    # setup redel
    ai = Kanpai(
        root_engine=root_engine,
        delegate_engine=delegate_engine,
        long_engine=long_engine,
        root_system_prompt=None,
        delegate_system_prompt=None,
        delegation_scheme=delegation_scheme,
        tool_configs={
            WebArenaMixin: {
                "always_include": True,
                "kwargs": {"webarena_harness": harness},
            },
        },
        root_has_tools=root_has_tools,
        title=f"webarena: {intent} ({task_id})",
        log_dir=log_dir / str(task_id),
        clear_existing_log=True,
    )

    # run query
    log.info(f"Config file: {config_file}")
    log.info(f"Intent: {intent}")
    out = []
    async for event in ai.query(harness.get_prompt(task=intent)):
        if isinstance(event, events.RootMessage) and event.msg.role == ChatRole.ASSISTANT:
            log.info(event.msg)
            if event.msg.text:
                out.append(event.msg.text)
    harness.end()

    # score
    evaluator = evaluator_router(config_file)
    score = evaluator(
        trajectory=harness.trajectory,
        config_file=config_file,
        page=wa_env.page,
        client=wa_env.get_page_client(wa_env.page),
    )

    await ai.close()
    return "\n\n".join(out), score, ai.logger.log_dir, _c


async def run():
    # check for existing results
    results_fp = log_dir / "results.jsonl"
    existing_results = set()
    if results_fp.exists():
        for r in read_jsonl(results_fp):
            existing_results.add(r["id"])

    # run on test set trials
    results_file = open(results_fp, "a")
    for task_id in tqdm.tqdm(range(START_IDX, END_IDX)):
        # skip if already set
        if task_id in existing_results:
            continue

        # run trial
        trial_config_path = LOG_BASE / f"config/{task_id}.json"
        try:
            result, score, result_log_dir, wa_config = await asyncio.wait_for(
                run_one_trial(trial_config_path), timeout=600
            )
            log.info(result)
            results_file.write(
                json.dumps({
                    "id": task_id,
                    "score": score,
                    "answer": result,
                    "intent": wa_config["intent"],
                    "log_dir": str(result_log_dir.resolve()),
                })
            )
            results_file.write("\n")
        except Exception as e:
            log.exception(e)
    results_file.close()


async def main():
    logging.basicConfig(level=logging.WARNING)
    log.setLevel(logging.INFO)
    log_dir.mkdir(parents=True, exist_ok=True)
    await run()


if __name__ == "__main__":
    asyncio.run(main())
