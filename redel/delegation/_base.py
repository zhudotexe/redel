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

        Example (implementation of ``delegate_one``):

        .. code-block:: python

            @ai_function()
            async def delegate(instructions: str):
                # initialize the instance
                helper = await self.create_delegate_kani(instructions)

                # set the state of the delegator to be waiting on the delegate
                with self.kani.run_state(RunState.WAITING):
                    # buffer the delegate's response as a list of strings, filtering for ASSISTANT messages
                    # use full_round_stream so that the app automatically dispatches streaming events
                    result = []
                    async for stream in helper.full_round_stream(instructions, max_function_rounds=5):
                        msg = await stream.message()
                        if msg.role == ChatRole.ASSISTANT and msg.content:
                            result.append(msg.content)

                    # clean up any of the delegate's ephemeral state and return result to caller
                    await helper.cleanup()
                    return "\n".join(result)
        """
        return await self.kani.create_delegate_kani(instructions)
