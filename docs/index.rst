ReDel
=====

ReDel is a toolkit for researchers and developers to build, iterate on, and analyze recursive multi-agent systems.

Built using the `kani <https://kani.readthedocs.io/en/latest/>`_ framework, it offers best-in-class support for modern
LLMs with tool usage.

Features
--------

- **Modular design** - ReDel makes it easy to experiment by providing a modular interface for creating tools, different
  delegation methods, and logs for later analysis.
- **Event-driven architecture** - Granular logging and a central event system makes it easy to listen for signals
  from anywhere in your system. Every event is automatically logged so you can run your favorite data analysis tools.
- **Bundled visualization** - Multi-agent systems can be hard to reason about from a human perspective. We provide a
  web-based visualization that allows you to interact with a configured system directly or view replays of saved runs
  (e.g. your own experiments!).
- **Built with open, unopinionated tech** - ReDel won't force you to learn bizarre library-specific tooling and isn't
  built by a big tech organization with their own motives. Everything in ReDel is implemented in pure, idiomatic Python
  and permissively licensed.

Screenshots
-----------

.. image:: _static/home.png

.. image:: _static/delegate2.png

.. image:: _static/loader.png

.. image:: _static/replay.png

Quickstart (EMNLP Demo)
-----------------------

Want to see what ReDel can do? To get started, we recommend cloning this repository.

You'll need Python 3.10 or higher, as well as node.js 16 or higher.

.. code-block:: console

    # clone the repository
    $ git clone -b demo/emnlp https://github.com/zhudotexe/redel.git
    $ cd redel

    # install python dependencies
    $ pip install -e ".[all]"
    $ playwright install chrome

    # build visualizer
    $ cd viz
    $ npm i
    $ npm run build
    $ cd ..

    # run web visualization of a ReDel system with web browsing
    $ OPENAI_API_KEY="..." python server.py

Then, open http://127.0.0.1:8000 in your browser. You'll be able to start new chats with a ReDel instance configured
with a web browsing tool, as well as view the replays of various systems on the FanOutQA, TravelPlanner, and WebArena
benchmarks.

.. toctree::
    :maxdepth: 2
    :caption: Docs

    install
    redel
    tools
    delegation
    events
    viz
    experiments.md
    glossary
    api_reference
    genindex
