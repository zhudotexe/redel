from browser_env import ScriptBrowserEnv, Trajectory  # this is from webarena - their pkg is namespaced weirdly


class WebArenaHarness:
    """This class provides a harness for a single run of WebArena.
    This is used to share a browser state & trajectory list with a full ReDel tree, as well as any other
    experiment-scoped state in WebArena.
    """

    def __init__(self, env: ScriptBrowserEnv, trajectory: Trajectory):
        self.env = env
        self.trajectory = trajectory
