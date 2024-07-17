from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redel.app import ReDel
    from redel.kanis import ReDelKani


class ToolBase:
    """This class is a base that all tool implementations should inherit from.

    It provides an interface to the tools in the group to access the application it's running in (for emitting events)
    and the kani it's bound to (for access to the chat state), as well as common setup/teardown hooks.
    """

    def __init__(self, app: "ReDel", kani: "ReDelKani"):
        self.app: "ReDel" = app
        """The app session this tool is running in."""
        self.kani: "ReDelKani" = kani
        """The kani this tool is bound to."""

    async def setup(self):
        """Called once per bound instance in an async context for each time this tool is bound to a new kani.

        Override this method to perform any necessary async setup.
        """
        pass

    async def cleanup(self):
        """Called each time the kani this tool is bound to completes its task.

        Override this method to clean up any ephemeral chat round-scoped resources if needed, but maintain any other
        state as the bound kani might still run again.
        """
        pass

    async def close(self):
        """Called once per bound instance when the app closes the session.

        Override this method to gracefully clean up all resources attached to this tool.
        """
        pass
