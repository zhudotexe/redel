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
import multiprocessing
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from pickle import UnpicklingError

import tqdm
from kani import ChatRole
from kani.engines.openai import OpenAIEngine

from redel import Kanpai, events
from redel.tools.webarena.client import WebArenaClient
from redel.tools.webarena.delegate_one import WebArenaDelegate1Mixin
from redel.tools.webarena.patches import patch_to_support_webarena
from redel.tools.webarena.root import WebArenaRootMixin
from redel.utils import read_jsonl

patch_to_support_webarena()

from browser_env.auto_login import get_site_comb_from_filepath
from redel.tools.webarena.impl import WebArenaMixin
from redel.tools.webarena.subprocess import wa_entrypoint
from redel.tools.webarena.utils import map_url_to_real

LOG_BASE = Path(__file__).parent / "experiments/webarena"
experiment_config = sys.argv[-1]
log = logging.getLogger("bench_webarena")

# ==== webarena config ====
START_IDX = 0
END_IDX = 812
SKIP = 3  # 0, 812, 3 = 270 trials for small

# ==== redel config ====
delegation_scheme = WebArenaDelegate1Mixin
log_dir = LOG_BASE / "test" / experiment_config
trace_dir = LOG_BASE / "traces/test" / experiment_config
# gross but whatever
# - **full**: no root FC, gpt-4o everything
if experiment_config == "full":
    root_engine = OpenAIEngine(model="gpt-4o", temperature=0, parallel_tool_calls=False)
    delegate_engine = root_engine
    root_has_tools = False
# - **root-fc**: root FC, gpt-4o everything
elif experiment_config == "root-fc":
    root_engine = OpenAIEngine(model="gpt-4o", temperature=0, parallel_tool_calls=False)
    delegate_engine = root_engine
    root_has_tools = True
# - **baseline**: root FC, no delegation, gpt-4o
elif experiment_config == "baseline":
    root_engine = OpenAIEngine(model="gpt-4o", temperature=0, parallel_tool_calls=False)
    delegate_engine = root_engine
    root_has_tools = True
    delegation_scheme = None
# - **small-leaf**: no root FC, gpt-4o root, gpt-3.5-turbo leaves
elif experiment_config == "small-leaf":
    root_engine = OpenAIEngine(model="gpt-4o", temperature=0, parallel_tool_calls=False)
    delegate_engine = OpenAIEngine(model="gpt-3.5-turbo", temperature=0, parallel_tool_calls=False)
    root_has_tools = False
#     - **small-all**: no root FC, gpt-3.5-turbo everything
elif experiment_config == "small-all":
    root_engine = OpenAIEngine(model="gpt-3.5-turbo", temperature=0, parallel_tool_calls=False)
    delegate_engine = root_engine
    root_has_tools = False
#     - **small-baseline**: root FC, no delegation, gpt-3.5-turbo
elif experiment_config == "small-baseline":
    root_engine = OpenAIEngine(model="gpt-3.5-turbo", temperature=0, parallel_tool_calls=False)
    delegate_engine = root_engine
    root_has_tools = True
    delegation_scheme = None
# - **short-context**: no root FC, gpt-4o everything, limit to 8192 ctx
elif experiment_config == "short-context":
    root_engine = OpenAIEngine(model="gpt-4o", temperature=0, max_context_size=8192, parallel_tool_calls=False)
    delegate_engine = root_engine
    root_has_tools = False
#     - **short-baseline**: root FC, no delegation, gpt-4o, 8192 ctx
elif experiment_config == "short-baseline":
    root_engine = OpenAIEngine(model="gpt-4o", temperature=0, max_context_size=8192, parallel_tool_calls=False)
    delegate_engine = root_engine
    root_has_tools = True
    delegation_scheme = None
else:
    raise ValueError("invalid experiment config")

SYSTEM_PROMPT = """\
You are an autonomous intelligent agent tasked with navigating a web browser. You will be given web-based tasks. These tasks will be accomplished through the use of specific functions you can call.

Here's the information you'll have:
The user's objective: This is the task you're trying to complete.
The current web page's accessibility tree: This is a simplified representation of the webpage, providing key information.
The current web page's URL: This is the page you're currently navigating.
The open tabs: These are the tabs you have open.

Homepage:
If you want to visit other websites, check out the homepage at http://homepage.com. It has a list of websites you can visit.
"""
SYSTEM_PROMPT = map_url_to_real(SYSTEM_PROMPT)

SYSTEM_PROMPT_ROOT = (
    SYSTEM_PROMPT + "\nYou should always call `submit_answer` with just your final answer once you are done."
)

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


def wa_ensure_auth(config_file: Path) -> Path:
    """If the given config file requires auth, do the login and save a temp copy with updated cookies."""
    # load config, update login cookies, save temp copy
    with open(config_file) as f:
        _c = json.load(f)
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
            config_file = Path(f"{temp_dir}/{os.path.basename(config_file)}")
            with open(config_file, "w") as f:
                json.dump(_c, f)
    return config_file


# ==== main ====
async def run_one_trial(config_file: Path, wa_client: WebArenaClient):
    # read the config
    with open(config_file) as f:
        config = json.load(f)
        intent = config["intent"]
        task_id = config["task_id"]

    # setup redel
    ai = Kanpai(
        root_engine=root_engine,
        delegate_engine=delegate_engine,
        root_system_prompt=SYSTEM_PROMPT_ROOT,
        delegate_system_prompt=SYSTEM_PROMPT,
        delegation_scheme=delegation_scheme,
        tool_configs={
            WebArenaMixin: {
                "always_include": True,
                "kwargs": {"webarena_client": wa_client},
            },
            WebArenaRootMixin: {
                "always_include_root": True,
                "kwargs": {"webarena_client_root": wa_client},
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
    idx = 0
    async for event in ai.query(wa_client.get_prompt(task=intent)):
        idx += 1
        if isinstance(event, events.RootMessage) and event.msg.role == ChatRole.ASSISTANT:
            log.info(event.msg)
            if event.msg.text:
                out.append(event.msg.text)
        # ping the subprocess every 20 events to ensure we don't get in a weird state where the asyncio cancel error
        # is overwritten by a broken pipe from the subprocess shutting down
        if not idx % 20:
            assert wa_client.send_command("ping") == "pong"
    log.info(f"Saved answer: {ai.root_kani.answer}")
    answer = ai.root_kani.answer or "\n\n".join(out)
    wa_client.end(answer)

    # score, save trace
    score = wa_client.score()
    wa_client.maybe_save_trace(str((trace_dir / f"{str(task_id)}.zip").resolve()))

    await ai.close()
    return answer, "\n\n".join(out), score, ai.logger.log_dir, config


async def run():
    # ==== webarena setup ====
    # As the default WebArena script is incompatible with asyncio, ReDel runs WebArena as a separate process,
    # which it communicates with synchronously using a pipe.
    # This isn't optimal but it works. [1]
    # [1]: I don't know if it works yet.
    (wa_send, wa_recv) = multiprocessing.Pipe()
    wa_process = multiprocessing.Process(target=wa_entrypoint, args=(wa_recv,))
    wa_process.start()

    # ==== experiment setup ====
    # check for existing results
    results_fp = log_dir / "results.jsonl"
    existing_results = set()
    if results_fp.exists():
        for r in read_jsonl(results_fp):
            existing_results.add(r["id"])

    # run on test set trials
    results_file = open(results_fp, "a")
    for task_id in tqdm.tqdm(range(START_IDX, END_IDX, SKIP)):
        # skip if already set
        if task_id in existing_results:
            continue

        # run trial
        trial_config_path = LOG_BASE / f"config/{task_id}.json"
        try:
            # ensure the subprocess is alive
            wa_send.send({"cmd": "ping"})
            assert wa_send.recv() == "pong"
            # setup webarena env for the given trial
            trial_config_path = wa_ensure_auth(trial_config_path)
            wa_client = WebArenaClient.setup_from_config(config_file=str(trial_config_path.resolve()), pipe=wa_send)
            # run
            answer, root_output, score, result_log_dir, wa_config = await asyncio.wait_for(
                run_one_trial(trial_config_path, wa_client), timeout=600
            )
            log.info(root_output)
            results_file.write(
                json.dumps({
                    "id": task_id,
                    "score": score,
                    "answer": answer,
                    "root_output": root_output,
                    "intent": wa_config["intent"],
                    "log_dir": str(result_log_dir.resolve()),
                })
            )
            results_file.write("\n")
            results_file.flush()
        except (asyncio.TimeoutError, EOFError, UnpicklingError, BrokenPipeError):
            log.exception("Unrecoverable child process error caught - restarting WA process forcefully!!!")
            # kill and restart the child process - asyncio timeouts/cancellation bork the multiprocessing
            wa_process.kill()
            wa_process.join()
            (wa_send, wa_recv) = multiprocessing.Pipe()
            wa_process = multiprocessing.Process(target=wa_entrypoint, args=(wa_recv,))
            wa_process.start()
        except Exception as e:
            log.exception(e)

    # clean up
    results_file.close()
    wa_send.send({"cmd": "stop"})
    wa_process.join()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    log.setLevel(logging.INFO)
    log_dir.mkdir(parents=True, exist_ok=True)
    trace_dir.mkdir(parents=True, exist_ok=True)
    asyncio.run(run())
