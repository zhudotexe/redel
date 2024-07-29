Glossary
========

.. glossary::
    :sorted:

    agent
        A large language model with tool usage, usually used to accomplish some sort of task. In this documentation,
        often referred to as a `Kani <https://kani.readthedocs.io/en/latest/>`_.

    delegate (verb)
        To assign a subtask to a delegate node.

    delegate node
        An agent in a recursive multi-agent system spawned by another agent. Usually, these nodes are also capable of
        spawning additional agents. It is responsible for either accomplishing the task given to it if the task is small
        enough, or decomposing it further and delegating additional subtasks.

    multi-agent system
        An application that uses multiple large language models (LLMs) working together to accomplish complex tasks or
        answer complex questions beyond the capabilities of a single LLM.

    recursive multi-agent system
        A multi-agent system that uses a tool to give agents the ability to spawn additional agents to handle
        smaller parts of a task it is given.

    root node
        The agent in a recursive multi-agent system that the human user interfaces with. Often, the root node is not
        provided with any tools except delegation, and is responsible only for decomposing the task given to it by the
        user.

    tool
        (In ReDel) A group of functions, written in Python, that is exposed to an agent. The agent may generate requests
        to call appropriate functions, which interact with the environment (e.g. searching the Internet).

    tool usage
        (In NLP) The ability, of a LLM, to comprehend the descriptions and purposes of tools given to it, and generate
        data for the tool to use as input.

        Synonymous with "function calling".
