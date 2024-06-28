import httpx
from browser_env import (
    Action,
)  # this is from webarena - their pkg is namespaced weirdly


class WebArenaClient:
    """This class provides a client for a given single run of WebArena.

    It connects to the WebArena interface server included in /experiments/webarena/webarena_iface_server.py.
    By default, this server is hosted on port 20685.

    This is used to share a browser state & trajectory list with a full ReDel tree, as well as any other
    experiment-scoped state in WebArena.
    """

    def __init__(self, config_file: str, http: httpx.AsyncClient):
        self.http = http
        self.config_file = config_file

    @classmethod
    async def setup_from_config(cls, config_file: str):
        """Create a new harness from the given config file and reset the environment."""
        inst = cls(config_file, httpx.AsyncClient(timeout=120, base_url="http://127.0.0.1:20685"))
        await inst.reset()
        return inst

    # ==== api ====
    async def reset(self):
        resp = await self.http.post("/reset", json={"config_file": self.config_file})
        resp.raise_for_status()

    async def action(self, action: Action):
        """Save the action to the trajectory, take it, save the resulting state, and return the result."""
        resp = await self.http.post("/action", json={"action": action})
        resp.raise_for_status()

    async def get_prompt(self, task: str) -> str:
        """Get the prompt at the current state:
        {observation}
        URL: {url}
        OBJECTIVE: {objective}
        [ERROR: {extra}] (if set)
        """
        resp = await self.http.post("/prompt", json={"task": task})
        resp.raise_for_status()
        data = resp.json()
        return data["prompt"]

    async def end(self, answer: str):
        """Called once when the system finishes its task."""
        resp = await self.http.post("/end", json={"answer": answer})
        resp.raise_for_status()

    async def score(self) -> int:
        """Get the score."""
        resp = await self.http.post("/score")
        resp.raise_for_status()
        data = resp.json()
        return data["score"]

    async def maybe_save_trace(self, path: str):
        """If the server has tracing enabled, save it to the given path."""
        resp = await self.http.post("/save_trace", json={"path": path})
        resp.raise_for_status()
