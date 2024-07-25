API Reference
=============

.. autoclass:: redel.ReDel

    .. attribute:: kanis
        :type: dict[str, BaseKani]

        A mapping of ID to BaseKani of *all* the kanis in the system, regardless of tree depth.

    .. attribute:: root_kani
        :type: ReDelKani | None

        A reference to the root node. Guaranteed to exist after :meth:`query` or :meth:`chat_in_terminal` is called;
        can be ``None`` before then.

    .. automethod:: get_config

    .. automethod:: chat_in_terminal

    .. automethod:: query

    .. automethod:: dispatch

    .. automethod:: add_listener

    .. automethod:: remove_listener

    .. automethod:: close

.. autoclass:: redel.ToolConfig
    :members:

.. autoclass:: redel.ToolBase
    :members:

.. autoclass:: redel.DelegationBase
    :members:

.. autoclass:: redel.state.RunState
    :members:

.. autoclass:: redel.state.AIFunctionState
    :members:
    :exclude-members: model_config, model_fields, model_computed_fields
    :class-doc-from: class

Default Events
--------------
Most events contain an ``id`` attribute, which refers to the ID of the kani that the event refers to.

.. autoclass:: redel.BaseEvent
    :members:
    :exclude-members: model_config, model_fields, model_computed_fields
    :class-doc-from: class

.. autoclass:: redel.events.KaniSpawn
    :members:
    :exclude-members: model_config, model_fields, model_computed_fields
    :class-doc-from: class

.. autoclass:: redel.events.KaniStateChange
    :members:
    :exclude-members: model_config, model_fields, model_computed_fields
    :class-doc-from: class

.. autoclass:: redel.events.TokensUsed
    :members:
    :exclude-members: model_config, model_fields, model_computed_fields
    :class-doc-from: class

.. autoclass:: redel.events.KaniMessage
    :members:
    :exclude-members: model_config, model_fields, model_computed_fields
    :class-doc-from: class

.. autoclass:: redel.events.RootMessage
    :members:
    :exclude-members: model_config, model_fields, model_computed_fields
    :class-doc-from: class

.. autoclass:: redel.events.RoundComplete
    :members:
    :exclude-members: model_config, model_fields, model_computed_fields
    :class-doc-from: class

Visualizer
----------

.. autoclass:: redel.server.VizServer

    .. automethod:: serve

Utilities
---------

.. autofunction:: redel.embeddings.get_embeddings

.. autoclass:: redel.embeddings.EmbeddingResult
    :members:

.. autoclass:: redel.utils.AutogenerateTitle

.. autofunction:: redel.utils.read_jsonl

Bundled Tools
-------------

.. autoclass:: redel.tools.browsing.Browsing

    .. automethod:: search

    .. automethod:: visit_page

.. autoclass:: redel.tools.email.Email

    .. automethod:: send_email

Bundled Delegation Schemes
--------------------------

.. autoclass:: redel.delegation.delegate_one.DelegateOne

    .. automethod:: delegate

.. autoclass:: redel.delegation.delegate_and_wait.DelegateWait

    .. automethod:: delegate

    .. automethod:: wait

Internals
---------

.. autoclass:: redel.base_kani.BaseKani
    :members: last_user_message, last_assistant_message, set_run_state, run_state, cleanup, close

    .. attribute:: state
        :type: RunState

        The run state of this kani.

        * ``RunState.STOPPED``: This kani is not currently running anything or waiting on a child.
        * ``RunState.RUNNING``: This kani is currently generating text.
        * ``RunState.WAITING``: This kani is waiting for the results of a sub-kani.
        * ``RunState.ERRORED``: This kani has run into a fatal error. Its internal state is indeterminate.

    .. attribute:: depth
        :type: int

        How deep in the computation tree this kani is. Will be 0 for the root node, 1 for children of the root, etc.

    .. attribute:: parent
        :type: BaseKani | None

        The parent of this kani, if it is not the root.

    .. attribute:: children
        :type: dict[str, BaseKani]

        A mapping of kani ids to kanis of all the immediate children of this kani.

    .. attribute:: id
        :type: str

        The internal ID of this kani.

    .. attribute:: name
        :type: str

        The human-readable name given to this kani.

    .. attribute:: app
        :type: ReDel

        A reference to the ReDel session this kani is running in.

.. autoclass:: redel.kanis.ReDelKani
    :members:
