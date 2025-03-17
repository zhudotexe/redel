"""
Example server for the ReDel web interface.

Environment Variables:
- OPENAI_API_KEY
- ANTHROPIC_API_KEY (optional)

Configuration:
- root engine: gpt-4o
- delegate engine: gpt-4o
- tools:
    - Browsing (always included in delegates)
        - long engine: claude-3-opus (for summarizing long webpages, if ANTHROPIC_API_KEY is set)
"""

import logging

from kani import AIFunction, ChatMessage
from kani.engines import Completion
from kani.engines.openai import OpenAIEngine
from kani.engines.openai.translation import translate_functions, translate_messages
from openai.types.responses import ResponseOutputItem, WebSearchToolParam

from redel import AUTOGENERATE_TITLE, ReDel
from redel.delegation import DelegateOne
from redel.server import VizServer


# openai responses engine, basic impl
class OpenAIResponsesEngine(OpenAIEngine):
    def __init__(self, *args, web_search_config: WebSearchToolParam = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.web_search_config = web_search_config

    async def predict(
        self, messages: list[ChatMessage], functions: list[AIFunction] | None = None, **hyperparams
    ) -> Completion:
        if functions:
            tool_specs = translate_functions(functions)
        else:
            tool_specs = []
        if self.web_search_config:
            tool_specs.append(self.web_search_config)

        if not tool_specs:
            tool_specs = None
        # translate to openai spec - group any tool messages together and ensure all free ToolCall IDs are bound
        translated_messages = translate_messages(messages)
        # make API call
        completion = await self.client.responses.create(
            model=self.model, input=translated_messages, tools=tool_specs, **self.hyperparams, **hyperparams
        )
        # translate into Kani spec and return
        cmpl = Completion(
            message=openai_response_to_kani_cm(completion.output),
            prompt_tokens=completion.usage.input_tokens,
            completion_tokens=completion.usage.output_tokens,
        )
        self.set_cached_message_len(cmpl.message, cmpl.completion_tokens)
        return cmpl


def openai_response_to_kani_cm(output_items: list[ResponseOutputItem]) -> ChatMessage:
    """Translate an OpenAI ChatCompletionMessage into a kani ChatMessage."""
    texts = []
    for output in output_items:
        if output.type == "message":
            for content in output.content:
                if content.type == "output_text":
                    text = content.text
                    for annotation in sorted(content.annotations, key=lambda a: a.end_index, reverse=True):
                        text = (
                            text[: annotation.end_index + 1]
                            + f" ({annotation.url}) "
                            + text[annotation.end_index + 1 :]
                        )
                    texts.append(text)

    content = "".join(texts)
    return ChatMessage.assistant(content)


# Define the engines
engine = OpenAIResponsesEngine(web_search_config={"type": "web_search_preview"}, temperature=0.8, top_p=0.95)

# Define the configuration for each interactive session
ai = ReDel(
    root_engine=engine,
    delegate_engine=engine,
    delegation_scheme=DelegateOne,
    title=AUTOGENERATE_TITLE,
    tool_configs={},
)

# configure and start the server
server = VizServer(ai)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server.serve()
