Delegation
==========
Delegation is how an agent actually spawns another sub-agent to handle a part of its task.

In ReDel, a delegation scheme is a special type of tool that an agent can call with instructions as an argument. These
instructions are sent to a new sub-agent, which can either complete them if they are simple enough, or break them up
into smaller parts and recursively delegate again.

As discussed in the previous section, different LLMs have different function calling capabilities, so there is not
a one-size-fits-all delegation scheme. In this section, we'll cover the bundled delegation schemes, and how to create
your own.

You can also use a custom delegation scheme to:

* provide a custom prompt to the delegator
* add special behaviour, like a parent node being able to "converse" with a child node across multiple chat rounds
* add custom events to the delegation process for later analysis

What is a delegation scheme?
----------------------------
As mentioned above, a delegation scheme is a special kind of tool that provides a method that:

* creates a new agent
* provides instructions to that agent
* calls the agent's :external+kani:meth:`kani.Kani.full_round_stream` method
* buffers the agent's response and returns it to the caller
* cleans up after the agent.

It's fully responsible for the full lifecycle of the sub-agent after requesting it from the system. If an agent can
be reused, you'll need to store your agent instances as state in your tool (see the previous section).

All delegation schemes should inherit from :class:`.DelegationBase`. This class provides all the same attributes
as :class:`.ToolBase`, plus an additional utility to create new agent instances:

.. autoclass:: redel.delegation.DelegationBase
    :members:
    :noindex:

Essentially, you can think of a delegation method as running a single query in a non-recursive system.

Here's an annotated example of what a delegation scheme looks like:

.. code-block:: python

    from kani import ChatRole, ai_function
    from redel.delegation import DelegationBase
    from redel.state import RunState

    class DelegateOne(DelegationBase):
        @ai_function()
        async def delegate(instructions: str):
            """(Insert your prompt for the model here.)"""

            # request a new agent instance from the system
            subagent = await self.create_delegate_kani(instructions)

            # set the state of the delegator agent to be waiting on the delegate
            with self.kani.run_state(RunState.WAITING):
                # buffer the delegate's response as a list of strings, filtering for
                # ASSISTANT messages
                # use full_round_stream so that the app automatically dispatches
                # streaming events
                result = []
                async for stream in subagent.full_round_stream(instructions):
                    msg = await stream.message()
                    if msg.role == ChatRole.ASSISTANT and msg.content:
                        result.append(msg.content)

                # clean up any of the delegate's ephemeral state and return result to caller
                await subagent.cleanup()
                return "\n".join(result)

Bundled Delegation Schemes
--------------------------
ReDel comes bundled with two delegation schemes: :class:`redel.delegation.delegate_one.DelegateOne` and
:class:`redel.delegation.delegate_and_wait.DelegateWait`.

DelegateOne
^^^^^^^^^^^
When a model calls the provided ``delegate()`` method, it immediately blocks the calling/delegator model's execution
until the sub-agent returns its result. Effectively, this can be thought of as running a process in the foreground.

This delegation scheme is well-suited for LLMs with parallel function calling. When called in parallel, ReDel will
allow all of the spawned sub-agents to run in parallel, and return their results once they all complete, in the same
order as they were requested.

DelegateWait
^^^^^^^^^^^^
In this scheme, when a model calls the provided ``delegate()`` method, it does not immediately block that model's
execution. Instead, it spawns the sub-agent in the *background* and begins its execution. To retrieve a sub-agent's
result, the parent model must call ``wait()`` with the ID returned to it, or a special value to wait on the next
completing child or all completing children.

This scheme is well-suited for LLMs without parallel function calling, as it lets these models spawn multiple agents
in parallel by calling ``delegate()`` multiple times before calling ``wait()``.
