Tools
=====
Modern LLMs have the ability to use tools provided to them. By prompting the LLM with a list of tools, what each one
does, and what input data each tool expects, an LLM can generate calls to these tools (this process is also called
"function calling").

Different LLMs may have different tool calling capabilities, depending on how they were trained. For example, some
models (e.g. ``gpt-4o``) can call multiple tools in parallel, while others (e.g. ``gpt-4``) can only call one at a time.

What is a tool?
---------------
In ReDel, a tool is a group of functions, written in Python, that is exposed to an agent. The agent may generate
requests to call appropriate functions, which interact with the environment (e.g. searching the Internet).

From a code perspective, a tool is a class that inherits from :class:`.ToolBase`, that has one or more methods decorated
with :external+kani:doc:`@ai_function() <function_calling>`.

.. code-block:: python
    :caption: An example of a basic tool exposing an HTTP GET function.

    import requests
    from kani import ai_function
    from redel import ToolBase

    class MyHTTPTool(ToolBase):
        @ai_function()
        def get(self, url: str):
            """Get the contents of a webpage, and return the raw HTML."""
            resp = requests.get(url)
            return resp.text

You can define tools in any Python file, and the method body can be anything you want - it's implemented in pure Python,
and won't be sent to the underlying language model, so there's no need to worry about its complexity or length. Anything
you can accomplish in a normal Python script, you can also do in a method body.

.. note::
    If you're familiar with Kani, it's almost exactly like defining a custom Kani, except that you inherit from
    ``ToolBase`` instead of ``Kani``.

.. note::
    Methods can be either asynchronous or synchronous. Synchronous methods will automatically be run in a threadpool
    when called by an LLM.

.. tip::
    For more information on function calling and what you can do with functions, see
    :external+kani:doc:`function_calling`!

Providing tools to a system
---------------------------
To provide a tool to a ReDel system, you should include it in the system's ``tool_configs`` dictionary.

Let's say we defined the ``MyHTTPTool`` tool above in a file ``my_tool.py``. To include it in a ReDel system, you would
configure it like:

.. code-block:: python

    from my_tool import MyHTTPTool

    system = ReDel(
        ...,
        tool_configs={
            MyHTTPTool: {"always_include": True},
        }
    )

The ``always_include`` configuration option means that every delegate node in the configured system will have access
to your tool. For more information, read :ref:`tool_config` and :class:`.ToolConfig`.

Providing arguments to your tool
--------------------------------
In many cases, your tool will need to be stateful in some way - maybe you need some sort of API key, share some
resource, or you just want to configure your tool using an argument. You can define instance attributes and constructor
arguments in normal Python when defining your tool, but should take care to pass ``*args`` and ``**kwargs`` to
``super().__init__(*args, **kwargs)`` in the constructor.

For example, to save an instance attribute from an argument, you might define your tool as such:

.. code-block:: python
    :caption: An example of a basic tool that takes an argument in the constructor and saves it.

    class MyStatefulTool(ToolBase):
        def __init__(self, *args, my_arg: str, **kwargs):
            super().__init__(*args, **kwargs)
            self.my_arg = my_arg

        # @ai_function()s below can reference self.my_arg...

In your ReDel system's ``tool_configs``, you can then specify what value to pass to ``my_arg``:

.. code-block:: python
    :caption: Configuring a ReDel system to pass a keyword argument to a tool when it's bound to an agent.
    :emphasize-lines: 6

    system = ReDel(
        ...,
        tool_configs={
            MyStatefulTool: {
                "always_include": True,
                "kwargs": {"my_arg": "This is a cool tool!"},
            },
        }
    )

.. note::
    Each agent will have its own instance of a tool - they are not shared. To share state across multiple agents,
    use class variables or pass in a reference to an external singleton as a constructor parameter.

Accessing the LLM and system
----------------------------
Sometimes, your tool will need access to the agent it's bound to, or the broader ReDel system. Inheriting from
:class:`.ToolBase` gives your functions access to these in the :attr:`.ToolBase.kani` and :attr:`.ToolBase.app`
attributes, respectively.

A common use case is to reference the message history of an agent, or dispatch a custom event in the system (also see
:doc:`events`):

.. code-block:: python
    :caption: An example of a tool that accesses the chat history and dispatches a custom event.

    # define a custom event -- see Events & Logging for more info
    class MyEvent(BaseEvent):
        type: Literal["my_custom_event"] = "my_custom_event"
        data: str

    class MyThirdTool(ToolBase):
        @ai_function()
        def do_something(self):
            last_message = self.kani.chat_history[-1]
            self.app.dispatch(MyEvent(data="Look at this cool event!"))
            return "The thing has been completed successfully."

Tool setup and teardown
-----------------------
The :class:`.ToolBase` class your tool inherits from also provides three overridable methods to perform setup and
teardown of any resources your tool might need: :meth:`.ToolBase.setup`, :meth:`.ToolBase.cleanup`, and
:meth:`.ToolBase.close`. You can use these to hook into your tool's lifecycle and gracefully clean up shared resources.

.. code-block:: python
    :caption: An example of a tool using the lifecycle hooks for graceful setup and teardown.

    class MyResourcefulTool(ToolBase):
        async def setup(self):
            self.my_file = open("/path/to/file.txt", "w")

        async def close(self):
            self.my_file.close()

        # @ai_function()s below can write to self.my_file...
