import asyncio
from contextlib import nullcontext

import aiolimiter
from kani import AIFunction, ChatMessage
from kani.engines.base import BaseCompletion, BaseEngine


class RatelimitedEngine(BaseEngine):
    def __init__(
        self,
        engine: BaseEngine,
        *args,
        max_concurrency: int = None,
        rpm_limiter: aiolimiter.AsyncLimiter = None,
        tpm_limiter: aiolimiter.AsyncLimiter = None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.engine = engine

        if max_concurrency is None:
            self.concurrency_semaphore = nullcontext()
        else:
            self.concurrency_semaphore = asyncio.Semaphore(max_concurrency)
        self.rpm_limiter = rpm_limiter
        self.tpm_limiter = tpm_limiter

    async def predict(
        self, messages: list[ChatMessage], functions: list[AIFunction] | None = None, **hyperparams
    ) -> BaseCompletion:
        if self.rpm_limiter:
            await self.rpm_limiter.acquire()
        if self.tpm_limiter:
            n_toks = self.function_token_reserve(functions) + sum(self.message_len(m) for m in messages)
            await self.tpm_limiter.acquire(n_toks)
        async with self.concurrency_semaphore:
            return await self.engine.predict(messages, functions, **hyperparams)

    def __getattr__(self, item):
        return getattr(self.engine, item)
