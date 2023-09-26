from aiolimiter import AsyncLimiter
from kani.engines.openai import OpenAIEngine


class RatelimitedOpenAIEngine(OpenAIEngine):
    def __init__(self, *args, max_rate=3, **kwargs):
        super().__init__(*args, **kwargs)
        self.limiter = AsyncLimiter(max_rate)

    async def predict(self, *args, **kwargs):
        async with self.limiter:
            return await super().predict(*args, **kwargs)
