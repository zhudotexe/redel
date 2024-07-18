from typing import TYPE_CHECKING

from redel.tools import ToolBase

if TYPE_CHECKING:
    from redel.kanis import ReDelKani


class DelegationBase(ToolBase):
    """
    This class is a base that all delegation implementations should inherit from.

    It extends :class:`.ToolBase` with an interface for creating delegate kani instances.
    """

    async def create_delegate_kani(self, instructions: str) -> "ReDelKani":
        r"""
        Call this method to get a fresh :class:`.ReDelKani` instance.

        This method will handle setting up the new kani in the computation graph as well as its tools, engine, and
        always included prompt based on the app configuration. It will *not* launch the kani with the given
        instructions -- this must be done by the calling function.

        The calling function is thus responsible for:

        * Setting the state of the calling kani
        * Providing the instructions to the delegate kani and calling its ``full_round_stream`` method
        * Buffering the delegate's response and returning it to the caller
        * Calling the appropriate cleanup methods of the delegate
        """
        return await self.kani.create_delegate_kani(instructions)
