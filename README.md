# ReDel

*A framework for recursive delegation of LLMs*

ReDel is a toolkit for researchers and developers to build, iterate on, and analyze recursive multi-agent systems.

Built using the [kani](https://github.com/zhudotexe/kani) framework, it offers best-in-class support for modern
LLMs with tool usage.

## Features

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

## Quickstart

Requires Python 3.10+

```shell
# install python dependencies
$ pip install -e "redel[all]"
# run web visualization of a ReDel system with web browsing
$ OPENAI_API_KEY="..." python -m redel.server
```

## Screenshots

![The ReDel homepage](docs/_static/home.png)

![Interactive](docs/_static/delegate2.png)

![Loading saved logs](docs/_static/loader.png)

![Replay](docs/_static/replay.png)

## Usage

There are two primary ways to interact with a system: interactively, through the web
interface, or programmatically. The former is particularly useful to debug your system's behaviour, iterate on prompts,
or otherwise provide an interactive experience. The latter is useful for running experiments and batch queries.

See the docs for more usage information at https://redel.readthedocs.io!

### Server

```python
from kani.engines.openai import OpenAIEngine
from redel import AUTOGENERATE_TITLE, ReDel
from redel.server import VizServer
from redel.tools.browsing import Browsing

# Define the LLM engines to use for each node
engine = OpenAIEngine(model="gpt-4", temperature=0.8, top_p=0.95)

# Define the configuration for each interactive session
redel_proto = ReDel(
    root_engine=engine,
    delegate_engine=engine,
    title=AUTOGENERATE_TITLE,
    tool_configs={
        Browsing: {"always_include": True},
    },
)

# configure and start the server
server = VizServer(redel_proto)
server.serve()
```

### Programmatic

```python
import asyncio
from kani import ChatRole
from kani.engines.openai import OpenAIEngine
from redel import ReDel, events
from redel.tools.browsing import Browsing

# Define the LLM engines to use for each node
engine = OpenAIEngine(model="gpt-4", temperature=0.8, top_p=0.95)

# Define the configuration for the session
ai = ReDel(
    root_engine=engine,
    delegate_engine=engine,
    title="Airspeed of a swallow",
    tool_configs={
        Browsing: {"always_include": True},
    },
)


# ReDel is async, so define an async function and use asyncio.run()
async def main():
    async for event in ai.query("What is the airspeed velocity of an unladen swallow?"):
        if isinstance(event, events.RootMessage) and event.msg.role == ChatRole.ASSISTANT:
            if event.msg.text:
                print(event.msg.text)


asyncio.run(main())
```

## EMNLP Demo Experiments

> [!NOTE]
> This section is specific to the `demo/emnlp` branch of this repository. You can switch branches in the top-left of
> the GitHub UI or by using this link: https://github.com/zhudotexe/redel/tree/demo/emnlp

This repository includes the logs of every single experiment run included in our paper in
the `experiments/` directory. You can load any of these runs in the visualization to view what the ReDel system did!

The experiments directory is broken down into the following
structure: `experiments/BENCHMARK_NAME/BENCHMARK_SPLIT/[RUN_ID]/SYSTEM_ID/QUERY_ID`, where:

- `BENCHMARK_NAME` is the name of the benchmark (fanoutqa, travelplanner, or webarena)
- `BENCHMARK_SPLIT` is the split of the benchmark we ran (usually the dev/validation split)
- `RUN_ID` is an internal split in the FanOutQA experiment to analyze an edge-case behaviour wrt parallel function
  calling and long contexts
- `SYSTEM_ID` is the system under test, configured as in the table below
- `QUERY_ID` is the benchmark-specific ID of a single run (loadable in the visualizer).

### System Configurations

| System ID      | Root Model    | Delegate Model | Root Functions? | Delegation? | Root Context | Delegate Context |
|----------------|---------------|----------------|-----------------|-------------|--------------|------------------|
| full           | gpt-4o        | gpt-4o         | no              | yes         | 128000       | 128000           |
| root-fc        | gpt-4o        | gpt-4o         | yes             | yes         | 128000       | 128000           |
| baseline       | gpt-4o        | N/A            | yes             | no          | 128000       | N/A              |
| small-leaf     | gpt-4o        | gpt-3.5-turbo  | no              | yes         | 128000       | 16385            |
| small-all      | gpt-3.5-turbo | gpt-3.5-turbo  | no              | yes         | 16385        | 16385            |
| small-baseline | gpt-3.5-turbo | N/A            | yes             | no          | 16385        | N/A              |
| short-context  | gpt-4o        | gpt-4o         | no              | yes         | 8192         | 8192             |
| short-baseline | gpt-4o        | N/A            | yes             | no          | 8192         | N/A              |

### Reproducing Experiments

To reproduce the experiments included in this repository, we include scripts to run each benchmark.

Follow these steps to setup the environment, then follow the instructions in each benchmark. We recommend setting up
a virtual environment for this project.

1. First, you'll need to clone this repository and check out the `demo/emnlp`
   branch: `git clone -b demo/emnlp https://github.com/zhudotexe/redel`
2. Install the necessary dependencies: `pip install -r requirements.txt`

#### FanOutQA

*output path: `experiments/fanoutqa/dev/trial2/SYSTEM_ID`*

**Run**

```shell
python bench_fanoutqa.py <full|root-fc|baseline|small-leaf|small-all|small-baseline|short-context|short-baseline>
```

This will run the given system on the FanOutQA dev set in the Open Book setting.

**Evaluate**

Set the `FANOUTQA_OPENAI_API_KEY` environment variable to a valid OpenAI API key. You can
use `export FANOUTQA_OPENAI_API_KEY=$OPENAI_API_KEY` to copy an existing API key from environment variables.

```shell
python score_fanoutqa.py experiments/fanoutqa/**/results.jsonl
```

This will output a `score.json` file in the output path with the final scores.

#### TravelPlanner

*output path: `experiments/travelplanner/validation/SYSTEM_ID`*

**Setup**

1. Install the TravelPlanner database:
    1. Download the database
       from [this link](https://drive.google.com/file/d/1pF1Sw6pBmq2sFkJvm-LzJOqrmfWoQgxE/view?usp=drive_link)
    2. Extract the zip file in `redel/tools/travelplanner`. This should create a directory named `db`.
2. In another directory, clone our fork of the TravelPlanner repository. This will be used for scoring, and includes the
   fixes discussed in our paper.
    1. `git clone https://github.com/zhudotexe/TravelPlanner`

**Run**

```shell
python bench_travelplanner.py <full|root-fc|baseline|small-leaf|small-all|small-baseline>
```

Note: This benchmark does not test the `short-ctx` systems since this benchmark doesn't have a long-context requirement.

**Evaluate**

```shell
python score_travelplanner.py experiments/travelplanner/**/results.jsonl
```

This script will write files in the correct format for the TravelPlanner evaluation in the output path, and
print the command to run to score the results.

You should now switch to the TravelPlanner repository you cloned in the setup step and run the commands output by this
script.

#### WebArena

*output path: `experiments/webarena/test/SYSTEM_ID`*

**Setup**

We reproduce some of the scripts and data contained in the WebArena repository in this repo under the terms of the
Apache-2.0 license, contained in `experiments/webarena/vendor/LICENSE`.

First, you'll need to set up your own WebArena environment.
See https://github.com/web-arena-x/webarena/blob/main/environment_docker/README.md for instructions.

Next, run the following to setup the webarena configuration:

```shell
# setup env vars (see https://github.com/web-arena-x/webarena/blob/main/environment_docker/README.md for env setup)
export SHOPPING="<your_shopping_site_domain>:7770"
export SHOPPING_ADMIN="<your_e_commerce_cms_domain>:7780/admin"
export REDDIT="<your_reddit_domain>:9999"
export GITLAB="<your_gitlab_domain>:8023"
export MAP="<your_map_domain>:3000"
export WIKIPEDIA="<your_wikipedia_domain>:8888/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing"
export HOMEPAGE="<your_homepage_domain>:4399"
# generate config files
python experiments/webarena/generate_test_data.py
```

You'll also need to ensure Playwright is installed:

```shell
playwright install chromium
```

**Run**

First, make sure you have reset your WebArena environment
(see https://github.com/web-arena-x/webarena/blob/main/environment_docker/README.md#environment-reset).

Then, launch the WebArena environment.

As the default WebArena script is incompatible with asyncio, ReDel launches a separate process to handle the
WebArena environment, which it communicates with over a pipe. This is done automatically.

Finally, run the bench script:

```shell
python bench_webarena.py <full|root-fc|baseline|small-leaf|small-all|small-baseline|short-context|short-baseline>
```

## License

We release ReDel under the terms of the MIT license, included in `LICENSE`. ReDel is intended for academic and personal
use only. To use ReDel for commercial purposes, please contact us.
