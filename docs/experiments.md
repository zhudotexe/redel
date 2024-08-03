# EMNLP Demo Experiments

Of course, the question remains: is using recursive multi-agent systems actually better than just improving a single
model? To test this, we ran three different benchmarks and compared the performance of various configurations of
ReDel systems. The benchmarks we ran were:

- FanOutQA, a multi-hop, multi-document information seeking benchmark with open-domain search
- TravelPlanner, a real-world planning benchmark for language agents
- WebArena, an autonomous agent benchmark with diverse tasks in a realistic web environment

All of our experiment code is open-source on the `demo/emnlp` branch of the ReDel repository:
https://github.com/zhudotexe/redel/tree/demo/emnlp

## System Configurations

We tested the following system configurations:

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

For each benchmark, we also provided the system with benchmark-specific tools (e.g. Wikipedia search for FanOutQA,
database search for TravelPlanner, and browser click/type actions for WebArena).

## Results

| System ID      | FanOutQA (GPTScore) | TravelPlanner (SR) | WebArena (SR) |
|----------------|---------------------|--------------------|---------------|
| full           | **0.494**           | **2.778**          | **0.203**     |
| root-fc        | 0.429               | 0.000              | 0.188         |
| baseline       | 0.394               | 0.000              | 0.162         |
| small-leaf     | 0.255               | 0.556              | 0.122         |
| small-all      | 0.087               | 0.000              | 0.092         |
| small-baseline | 0.077               | 0.000              | 0.085         |
| short-context  | 0.426               | ---                | 0.129         |
| short-baseline | 0.361               | ---                | 0.122         |

We find that overall, recursive delegation systems perform better than their baseline systems in every single benchmark.

From these high-level results, we can conclude that:

- Adding recursive delegation on top of a model improves its performance as tasks get harder
- To fully take advantage of delegation, it is often important to remove tools from the root node to avoid the root node
  overcommitting
- Recursive delegation allows you to use a "strong" model as the root and "weaker" models as delegates to gain a major
  performance boost over a system comprised entirely of a weaker model
- Recursive delegation can help in long-context tasks by removing the requirement for a single model to process
  everything in serial

We will release a deeper dive into the results in a future paper.

## Reproducing Experiments

In the `demo/emnlp` branch of the ReDel repository, we include the logs of every single experiment run in
the `experiments/` directory. You can load any of these runs in the visualization to view what the ReDel system did!

The experiments directory is broken down into the following
structure: `experiments/BENCHMARK_NAME/BENCHMARK_SPLIT/[RUN_ID]/SYSTEM_ID/QUERY_ID`, where:

- `BENCHMARK_NAME` is the name of the benchmark (fanoutqa, travelplanner, or webarena)
- `BENCHMARK_SPLIT` is the split of the benchmark we ran (usually the dev/validation split)
- `RUN_ID` is an internal split in the FanOutQA experiment to analyze an edge-case behaviour wrt parallel function
  calling and long contexts
- `SYSTEM_ID` is the system under test, configured as in the table below
- `QUERY_ID` is the benchmark-specific ID of a single run (loadable in the visualizer).

To reproduce the experiments included in this repository, we include scripts to run each benchmark.

Follow these steps to setup the environment, then follow the instructions in each benchmark. We recommend setting up
a virtual environment for this project.

1. First, you'll need to clone this repository and check out the `demo/emnlp`
   branch: `git clone -b demo/emnlp https://github.com/zhudotexe/redel`
2. Install the necessary dependencies: `pip install -r requirements.txt`

### FanOutQA

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

### TravelPlanner

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

### WebArena

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
