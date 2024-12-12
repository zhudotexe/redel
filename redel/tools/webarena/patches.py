"""
Patches to support including WebArena as a dependency without breaking everything.
Thanks to Ajay for providing these.

MIT License
-----------

Copyright (c) 2024 Ajay Patel
Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""

import contextlib
import subprocess
import sys
import warnings
from functools import cache

import openai
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import ChatCompletionMessage, Choice


@contextlib.contextmanager
def ignore_webarena_warnings():
    """WebArena throws some warnings we can silence to make output logs cleaner."""
    from beartype.roar import BeartypeDecorHintPep585DeprecationWarning

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=BeartypeDecorHintPep585DeprecationWarning)
        warnings.filterwarnings(
            "ignore",
            category=UserWarning,
            message='Field "model_id" has conflict.*',
            module="pydantic._internal._fields",
        )
        yield None


@cache
def _patch_openai_to_support_older_version():
    sys.modules["openai.error"] = sys.modules["openai"]
    openai.error = openai
    openai.ChatCompletion = openai.chat.completions
    ChatCompletion.__getitem__ = ChatCompletion.__getattribute__
    Choice.__getitem__ = Choice.__getattribute__
    ChatCompletionMessage.__getitem__ = ChatCompletionMessage.__getattribute__


def patch_to_support_webarena():
    """Applies patches to make running WebArena easier."""

    # WebArena relies on using the older OpenAI API
    _patch_openai_to_support_older_version()

    # Get the WebArena scores
    # with ignore_webarena_warnings():
    #     import evaluation_harness  # isort: skip # noqa
    #
    #     _evaluator_router = evaluation_harness.evaluator_router
    #
    #     def new_evaluator_router(config_file, *args, **kwargs):
    #         evaluator_obj = _evaluator_router(config_file, *args, **kwargs)
    #         evaluator_cls = evaluator_obj.__class__
    #
    #         class InterceptScoreCls(evaluator_cls):
    #             def __init__(self):
    #                 pass
    #
    #             def __call__(self, *args, **kwargs):
    #                 score = super().__call__(*args, **kwargs)
    #                 test_num = config_file.split("/")[-1].split(".")[0]
    #                 all_results = {}
    #                 lock = FileLock("./results/all_results.json.flock")
    #                 with lock:
    #                     try:
    #                         with open("./results/all_results.json", "r") as f:
    #                             all_results = json.load(f)
    #                     except OSError:
    #                         all_results = {}
    #                     with open("./results/all_results.json", "w+") as f:
    #                         all_results[test_num] = score
    #                         json.dump(all_results, f, indent=4)
    #
    #                     # Log prompts
    #                     if not dd:
    #                         from ._datadreamer_support import call_llm_history
    #
    #                         with open(f"./results/prompts/{test_num}.json", "w+") as f:
    #                             json.dump(
    #                                 {"score": score, "prompts": call_llm_history},
    #                                 f,
    #                                 indent=4,
    #                             )
    #
    #                     # Log progress and statistics
    #                     num_runs = len(all_results)
    #                     total_tests = int(
    #                         check_output(
    #                             "ls config_files/ | grep json | grep -v test | wc -l",
    #                             shell=True,
    #                         )
    #                     )
    #                     passed_runs = sum([int(score == 1.0) for score in all_results.values()])
    #                     passed_runs_nums = [int(test_num) for test_num, score in all_results.items() if score == 1.0]
    #                     failed_runs = sum([int(score == 0.0) for score in all_results.values()])
    #                     logger.info(
    #                         f"Tests Progress: {num_runs} / {total_tests} test(s)."
    #                         f" {passed_runs} passed run(s)."
    #                         f" {failed_runs} failed run(s)."
    #                         f" Passing tests: {str(passed_runs_nums)}."
    #                     )
    #                 return score
    #
    #         new_evaluator_obj = InterceptScoreCls()
    #         new_evaluator_obj.__dict__.update(evaluator_obj.__dict__)
    #
    #         return new_evaluator_obj
    #
    #     evaluation_harness.evaluator_router = new_evaluator_router

    # WebArena runs a subprocess to login to get cookies
    # which spews logs / warnings, so we silence them
    # _subprocess_run = subprocess.run
    #
    # def subprocess_run(*args, **kwargs):
    #     if any("auto_login.py" in a for a in args[0]):
    #         kwargs["stdout"] = subprocess.PIPE
    #         kwargs["stderr"] = subprocess.PIPE
    #     return _subprocess_run(*args, **kwargs)
    #
    # subprocess.run = lambda *args, **kwargs: subprocess_run(*args, **kwargs)

    # WebArena's get_bounding_client_rect method is very slow
    with ignore_webarena_warnings():
        from browser_env.processors import TextObervationProcessor
        from playwright.sync_api import CDPSession

        # Marks up the Accessibility Tree to allow us to mark ignored nodes
        _client_send = CDPSession.send

        def new_client_send(self, method, *args, **kwargs):
            results = _client_send(self, method, *args, **kwargs)
            if method == "Accessibility.getFullAXTree":
                for node in results["nodes"]:
                    if node["ignored"]:
                        # If the node is ignored, mark it with ID #-999
                        node["backendDOMNodeId"] = -999
            return results

        CDPSession.send = new_client_send

        _get_bounding_client_rect = TextObervationProcessor.get_bounding_client_rect

        # Skip nodes marked as ignored to speed up and use DOM.getBoxModel to get
        # the size of nodes we need to get the size of because it's way faster
        def new_get_bounding_client_rect(client, backend_node_id):
            backend_node_id = int(backend_node_id)
            new = {"result": {"value": {"x": 0, "y": 0, "width": 0, "height": 0}}}
            if backend_node_id != -999:
                try:
                    box_model = client.send("DOM.getBoxModel", {"backendNodeId": backend_node_id})["model"]
                    new = {
                        "result": {
                            "value": {
                                "x": box_model["border"][0],
                                "y": box_model["border"][1],
                                "width": box_model["width"],
                                "height": box_model["height"],
                            }
                        }
                    }
                except Exception as e:
                    if "Protocol error" not in str(e):
                        raise e from None

            ############################################################################
            ############################################################################
            # orig = _get_bounding_client_rect(client, backend_node_id)
            # orig = {
            #     "result": {
            #         "value": {
            #             "x": orig["result"]["value"]["x"],
            #             "y": orig["result"]["value"]["y"],
            #             "width": round(orig["result"]["value"]["width"]),
            #             "height": round(orig["result"]["value"]["height"]),
            #         }
            #     }
            # }
            # orig_value = orig["result"]["value"]
            # new_value = new["result"]["value"]

            # def isclose(orig, new):
            #     assert abs(orig - new) <= 2

            # isclose(orig_value["x"], new_value["x"])
            # isclose(orig_value["y"], new_value["y"])
            # isclose(orig_value["width"], new_value["width"])
            # isclose(orig_value["height"], new_value["height"])
            ############################################################################
            ############################################################################

            return new

        TextObervationProcessor.get_bounding_client_rect = staticmethod(new_get_bounding_client_rect)
