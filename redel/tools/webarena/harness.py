import json

from browser_env import (
    Action,
    ScriptBrowserEnv,
    StateInfo,
    Trajectory,
    create_stop_action,
)  # this is from webarena - their pkg is namespaced weirdly
from browser_env.env_config import URL_MAPPINGS


class WebArenaHarness:
    """This class provides a harness for a single run of WebArena.
    This is used to share a browser state & trajectory list with a full ReDel tree, as well as any other
    experiment-scoped state in WebArena.
    """

    def __init__(self, config, env: ScriptBrowserEnv):
        self.config = config
        self.intent = config["intent"]
        self.env = env
        self.trajectory: Trajectory = []
        self.obs = None
        self.info = None
        self.last_action_success = None

    @classmethod
    def setup_from_config(cls, config_file: str, env: ScriptBrowserEnv):
        """Create a new harness from the given config file and reset the environment."""
        with open(config_file) as f:
            config = json.load(f)
        inst = cls(config, env)
        # initialize the state
        inst.last_action_success = True
        inst.obs, inst.info = env.reset(options={"config_file": config_file})
        inst.save_state_to_trajectory()
        return inst

    def save_state_to_trajectory(self):
        """Save the browser state to the trajectory. Called after setup and each action."""
        state_info: StateInfo = {"observation": self.obs, "info": self.info}
        self.trajectory.append(state_info)

    def action(self, action: Action):
        """Save the action to the trajectory, take it, save the resulting state, and return the result."""
        self.trajectory.append(action)
        self.obs, self.last_action_success, _, _, self.info = self.env.step(action)
        self.save_state_to_trajectory()
        return self.obs, self.last_action_success, self.info

    def get_prompt(self, task: str, error: str = None) -> str:
        """Get the prompt at the current state:
        {observation}
        URL: {url}
        OBJECTIVE: {objective}
        [ERROR: {extra}] (if set)
        """
        obs = self.obs["text"]
        page = self.info["page"]
        url = self.map_url_to_real(page.url)

        raw = f"BROWSER STATE:\n{obs}\nURL: {url}\nOBJECTIVE: {task}"
        if not error:
            return raw
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
