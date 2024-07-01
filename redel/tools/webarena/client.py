from multiprocessing.connection import Connection
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from browser_env import Action


class WebArenaClient:
    """This class provides a client for a given single run of WebArena.

    It interfaces with the WebArena process using a provided pipe.

    This is used to share a browser state & trajectory list with a full ReDel tree, as well as any other
    experiment-scoped state in WebArena.
    """

    def __init__(self, config_file: str, pipe: Connection):
        self.pipe = pipe
        self.config_file = config_file

    @classmethod
    def setup_from_config(cls, config_file: str, pipe: Connection):
        """Create a new harness from the given config file and reset the environment."""
        inst = cls(config_file, pipe)
        inst.reset()
        return inst

    def send_command(self, cmd: str, **data):
        """Send a command and retrieve its response."""
        msg = {"cmd": cmd, "data": data}
        self.pipe.send(msg)
        retval = self.pipe.recv()
        if isinstance(retval, Exception):
            raise retval
        return retval

    # ==== api ====
    def reset(self):
        return self.send_command("reset", config_file=self.config_file)

    def action(self, action: "Action"):
        """Save the action to the trajectory, take it, save the resulting state, and return the result."""
        return self.send_command("action", action=action)

    def get_prompt(self, task: str) -> str:
        """Get the prompt at the current state:
        {observation}
        URL: {url}
        OBJECTIVE: {objective}
        [ERROR: {extra}] (if set)
        """
        return self.send_command("get_prompt", task=task)

    def end(self, answer: str):
        """Called once when the system finishes its task."""
        return self.send_command("end", answer=answer)

    def score(self) -> int:
        """Get the score."""
        return self.send_command("score")

    def maybe_save_trace(self, path: str):
        """If the server has tracing enabled, save it to the given path."""
        return self.send_command("save_trace", path=path)
