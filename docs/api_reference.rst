API Reference
=============

.. autoclass:: redel.ReDel

    .. automethod:: chat_in_terminal

    .. automethod:: query

    .. automethod:: dispatch

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

Internals
---------

.. autoclass:: redel.base_kani.BaseKani
    :members: last_user_message, last_assistant_message, set_run_state, run_state, cleanup, close

.. autoclass:: redel.kanis.ReDelKani
    :members:

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
