"""
Since the WebArena ScriptBrowserEnv is incompatible with asynchronous applications, we need to run the env in a separate
process, which ReDel will communicate with over HTTP.

This Flask server exposes all the necessary interfaces for running WebArena.

Statefulness: This server is STATEFUL between calls to `/reset`, and NOT parallel-safe. If parallel runs are needed,
launch an instance of this server for each run.
"""

import traceback

from werkzeug.exceptions import HTTPException

from patches import patch_to_support_webarena

patch_to_support_webarena()

from browser_env import Action, ScriptBrowserEnv, StateInfo, Trajectory, create_stop_action
from browser_env.env_config import URL_MAPPINGS
from evaluation_harness import evaluator_router
from flask import Flask, abort, request


# ===== wa config ====
WA_HEADLESS = False
WA_TRACE = True

# ===== flask =====
app = Flask("webarena_iface_server")


@app.errorhandler(HTTPException)
def handle_http_exc(e):
    return {"success": False, "msg": e.description}, e.code


@app.errorhandler(Exception)
def handle_exc(e):
    traceback.print_exception(e)
    return {"success": False, "msg": str(e)}, 500


# ===== wa env global =====
wa_env = ScriptBrowserEnv(
    headless=WA_HEADLESS,
    observation_type="accessibility_tree",
    current_viewport_only=False,
    viewport_size={
        "width": 1280,
        "height": 720,
    },
    save_trace_enabled=WA_TRACE,
    sleep_after_execution=0.0,
)


# ===== state =====
class State:
    """Store the state of a trial in this class."""

    def __init__(self, config_file: str):
        self.config_file = config_file
        self.trajectory: Trajectory = []
        self.obs = None
        self.info = None
        self.last_action_success = True

    def save_state_to_trajectory(self):
        """Save the browser state to the trajectory. Called after setup and each action."""
        state_info: StateInfo = {"observation": self.obs, "info": self.info}
        self.trajectory.append(state_info)

    def init(self):
        """Reset the WA env to the initial state for this trial."""
        self.obs, self.info = wa_env.reset(options={"config_file": self.config_file})
        self.save_state_to_trajectory()

    def action(self, action: Action):
        """Save the action to the trajectory, take it, save the resulting state, and return the result."""
        self.trajectory.append(action)
        self.obs, self.last_action_success, _, _, self.info = wa_env.step(action)
        self.save_state_to_trajectory()
        return self.obs, self.last_action_success, self.info

    def get_prompt(self, task: str) -> str:
        """Get the prompt at the current state:
        {observation}
        URL: {url}
        OBJECTIVE: {objective}
        [ERROR: {extra}] (if not last_action_success)
        """
        obs = self.obs["text"]
        page = self.info["page"]
        url = self.map_url_to_real(page.url)

        raw = f"BROWSER STATE:\n{obs}\nURL: {url}\nOBJECTIVE: {task}"
        if self.last_action_success:
            return raw
        error = self.info["fail_error"]
        return f"{raw}\nERROR: {error}"

    def end(self, answer: str):
        """Called once when the system finishes its task."""
        self.trajectory.append(create_stop_action(answer))

    # ==== adapted from webarena ====
    @staticmethod
    def map_url_to_real(url: str) -> str:
        """Map the urls to their real world counterparts"""
        for i, j in URL_MAPPINGS.items():
            if i in url:
                url = url.replace(i, j)
        return url

    @staticmethod
    def map_url_to_local(url: str) -> str:
        """Map the urls to their local counterparts"""
        for i, j in URL_MAPPINGS.items():
            if j in url:
                url = url.replace(j, i)
            # https
            if j.replace("http", "https") in url:
                url = url.replace(j.replace("http", "https"), i)
        return url


state: State | None = None


# reset
@app.post("/reset")
def reset():
    data = request.get_json()
    config_file = data["config_file"]
    global state
    state = State(config_file=config_file)
    state.init()
    return {"success": True}


# action
@app.post("/action")
def do_action():
    if state is None:
        abort(400, "State must be initialized first")
    data = request.get_json()
    action_dict = data["action"]
    state.action(action_obj)


# prompt
@app.post("/prompt")
def get_prompt():
    if state is None:
        abort(400, "State must be initialized first")
    data = request.get_json()
    task = data["task"]
    return {"success": True, "prompt": state.get_prompt(task)}


# end
@app.post("/end")
def end():
    if state is None:
        abort(400, "State must be initialized first")
    data = request.get_json()
    answer = data["answer"]
    state.end(answer)


# score
@app.post("/score")
def get_score():
    if state is None:
        abort(400, "State must be initialized first")
    evaluator = evaluator_router(state.config_file)
    score = evaluator(
        trajectory=state.trajectory,
        config_file=state.config_file,
        page=wa_env.page,
        client=wa_env.get_page_client(wa_env.page),
    )
    return {"success": True, "score": score}


# save trace
@app.post("/save_trace")
def save_trace():
    data = request.get_json()
    path = data["path"]
    wa_env.save_trace(path)
    return {"success": True, "path": path}


if __name__ == "__main__":
    app.run(debug=False, port=20685, load_dotenv=False)
