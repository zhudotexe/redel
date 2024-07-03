"""
Since the WebArena ScriptBrowserEnv is incompatible with asynchronous applications, we need to run the env in a separate
process, which ReDel will communicate with over HTTP.

This Flask server exposes all the necessary interfaces for running WebArena.

Statefulness: This server is STATEFUL between calls to `/reset`, and NOT parallel-safe. If parallel runs are needed,
launch an instance of this server for each run.
"""

from typing import Any, TYPE_CHECKING, TypedDict

from .patches import patch_to_support_webarena

patch_to_support_webarena()

from .utils import map_url_to_real
from browser_env import Action, ScriptBrowserEnv, StateInfo, Trajectory, create_stop_action
from evaluation_harness import evaluator_router

if TYPE_CHECKING:
    from multiprocessing.connection import Connection

# ===== wa config ====
WA_HEADLESS = True
WA_TRACE = True


# ===== commands =====
class WASubprocessCommand(TypedDict, total=False):
    cmd: str
    data: Any


# ===== state =====
class State:
    """Store the state of a trial in this class."""

    def __init__(self, env: ScriptBrowserEnv):
        self.env = env
        self.config_file = None
        self.trajectory: Trajectory = []
        self.obs = None
        self.info = None
        self.last_action_success = None

    def save_state_to_trajectory(self):
        """Save the browser state to the trajectory. Called after setup and each action."""
        state_info: StateInfo = {"observation": self.obs, "info": self.info}
        self.trajectory.append(state_info)

    def reset(self, config_file: str):
        """Reset the WA env to the initial state for this trial."""
        self.config_file = config_file
        self.trajectory = []
        self.last_action_success = True
        self.obs, self.info = self.env.reset(options={"config_file": config_file})
        self.save_state_to_trajectory()

    def action(self, action: Action):
        """Save the action to the trajectory, take it, save the resulting state, and return the result."""
        self.trajectory.append(action)
        self.obs, self.last_action_success, _, _, self.info = self.env.step(action)
        self.save_state_to_trajectory()
        # return self.obs, self.last_action_success, self.info

    def get_prompt(self, task: str) -> str:
        """Get the prompt at the current state:
        {observation}
        URL: {url}
        OBJECTIVE: {objective}
        [ERROR: {extra}] (if not last_action_success)
        """
        obs = self.obs["text"]
        page = self.info["page"]
        url = map_url_to_real(page.url)

        raw = f"BROWSER STATE:\n{obs}\nURL: {url}\nOBJECTIVE: {task}"
        if self.last_action_success:
            return raw
        error = self.info["fail_error"]
        return f"{raw}\nERROR: {error}"

    def end(self, answer: str):
        """Called once when the system finishes its task."""
        self.trajectory.append(create_stop_action(answer))

    def get_score(self):
        evaluator = evaluator_router(self.config_file)
        score = evaluator(
            trajectory=self.trajectory,
            config_file=self.config_file,
            page=self.env.page,
            client=self.env.get_page_client(self.env.page),
        )
        return score

    def save_trace(self, path: str):
        if WA_TRACE:
            self.env.save_trace(path)


def wa_entrypoint(pipe: "Connection"):
    """Main entrypoint for the subprocess.

    Creates the environment and listens for commands from the pipe until a STOP command is received.

    POSTCONDITION: Every received command will send back exactly one response.
    RESTRICTION: No commands will be sent in parallel.
    """
    wa_env = ScriptBrowserEnv(
        headless=WA_HEADLESS,
        observation_type="accessibility_tree",
        current_viewport_only=True,
        viewport_size={
            "width": 2560,
            "height": 1440,
        },
        save_trace_enabled=WA_TRACE,
        sleep_after_execution=0.0,
    )
    state = State(wa_env)
    running = True

    while running:
        # recv
        retval = None
        data: WASubprocessCommand = pipe.recv()

        # process
        try:
            match data:
                case {"cmd": "stop"}:
                    running = False
                case {"cmd": "reset", "data": {"config_file": config_file}}:
                    retval = state.reset(config_file)
                case {"cmd": "action", "data": {"action": action}}:
                    retval = state.action(action)
                case {"cmd": "get_prompt", "data": {"task": task}}:
                    retval = state.get_prompt(task)
                case {"cmd": "end", "data": {"answer": answer}}:
                    retval = state.end(answer)
                case {"cmd": "score"}:
                    retval = state.get_score()
                case {"cmd": "save_trace", "data": {"path": path}}:
                    retval = state.save_trace(path)
                case {"cmd": "ping"}:
                    retval = "pong"
                case other:
                    print(f"!!! UNKNOWN COMMAND IN WA IPC !!!\n{other}")
                    raise ValueError("Unknown command")
        except Exception as e:
            retval = e

        # return
        pipe.send(retval)

    # clean up
    wa_env.close()
