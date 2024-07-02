from kani import ChatMessage, ChatRole, ai_function

from redel.base_kani import BaseKani
from redel.tools.webarena.client import WebArenaClient


class WebArenaRootMixin(BaseKani):
    def __init__(self, *args, webarena_client_root: WebArenaClient, **kwargs):
        super().__init__(*args, **kwargs)
        self.webarena = webarena_client_root
        self.answer = None

    async def add_to_history(self, message: ChatMessage):
        # HACK: if the message is a USER message and does not contain the webarena state prompt,
        # prepend it here
        # this is used to ensure that messages sent to the delegates allow them to see the state
        if (
            message.role == ChatRole.FUNCTION
            and message.name == "delegate"
            and not message.text.startswith("BROWSER STATE:")
        ):
            task = self.last_user_message.text
            browser_content = self.webarena.get_prompt(task=task)
            message.content = f"{browser_content}\nRESULT: {message.text}"
        return await super().add_to_history(message)

    @ai_function()
    def submit_answer(self, answer: str = None):
        """
        Call this function when you believe the task is complete. If the objective is to find a text-based answer, provide the answer. If you believe the task is impossible to complete, provide the answer as "N/A".
        """
        self.answer = answer
