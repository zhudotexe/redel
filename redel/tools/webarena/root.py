from kani import ChatRole, ai_function

from redel.base_kani import BaseKani


class WebArenaRootMixin(BaseKani):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.answer = None

    @ai_function()
    def submit_answer(self, answer: str = None):
        """
        Call this function when you believe the task is complete. If the objective is to find a text-based answer, provide the answer. If you believe the task is impossible to complete, provide the answer as "N/A".
        """
        self.answer = answer
