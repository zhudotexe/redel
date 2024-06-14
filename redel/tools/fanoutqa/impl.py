from typing import Literal, TypedDict

import fanoutqa
from kani import ChatMessage, ai_function

from redel.base_kani import BaseKani
from redel.events import BaseEvent
from .retrieval import BM25Corpus, OpenAICorpus


# custom events
class FOQAArticleRetrieved(BaseEvent):
    type: Literal["foqa_article_retrieved"] = "foqa_article_retrieved"
    id: str
    article_title: str
    article_pageid: int
    article_revid: int


class FOQAEngineUpgrade(BaseEvent):
    type: Literal["foqa_engine_upgrade"] = "foqa_engine_upgrade"
    id: str
    old_ctx_len: int
    new_ctx_len: int


class FOQARetrievalType(BaseEvent):
    type: Literal["foqa_retrieval_type"] = "foqa_retrieval_type"
    id: str
    retrieved_tokens: int
    max_search_tokens: int
    retrieval_type: str  # full_doc_short, full_doc_long, bm25, embedding


# config
class FanOutQAConfig(TypedDict, total=False):
    do_long_engine_upgrade: bool
    retrieval_type: Literal["bm25", "openai"]


# ai function
class FanOutQAMixin(BaseKani):
    def __init__(self, *args, foqa_config: FanOutQAConfig = None, **kwargs):
        super().__init__(*args, **kwargs)
        if foqa_config is None:
            foqa_config = {}
        self.do_long_engine_upgrade = foqa_config.get("do_long_engine_upgrade", True)
        self.retrieval_type = foqa_config.get("retrieval_type", "bm25")

    @property
    def max_search_tokens(self):
        # trial2: engine's max ctx size / (# of parallel fcs + 1)
        return self.engine.max_context_size // (len(self.last_assistant_message.tool_calls) + 1)
        # trial1: half engine's max ctx size
        # return self.engine.max_context_size // 2

    @ai_function()
    def search(self, query: str):
        """Search Wikipedia for an article with the given title, and get its content. If no such article is found, return similar article names."""
        query = query.strip()
        matches = fanoutqa.wiki_search(query)
        for match in matches:
            if match.title.lower() == query.lower():
                found_article = match
                break
        else:
            similar_searches = "\n".join(f"- {m.title}" for m in matches)
            return (
                "No page with that title exists. Try searching for one of these similar articles"
                f" instead:\n{similar_searches}"
            )

        # found match
        prompt = f"<document>\n<title>{found_article.title}</title>\n{{}}</document>"
        self.app.dispatch(
            FOQAArticleRetrieved(
                id=self.id,
                article_title=found_article.title,
                article_pageid=found_article.pageid,
                article_revid=found_article.revid,
            )
        )

        # if the content fits in the context, return that
        wiki_content = fanoutqa.wiki_content(found_article)
        full_content = prompt.format(f"<content>\n{wiki_content}\n</content>\n")
        if (retrieved_tokens := self.message_token_len(ChatMessage.user(full_content))) <= self.max_search_tokens:
            self.app.dispatch(
                FOQARetrievalType(
                    id=self.id,
                    retrieval_type="full_doc_short",
                    retrieved_tokens=retrieved_tokens,
                    max_search_tokens=self.max_search_tokens,
                )
            )
            return full_content

        # else, upgrade the engine to long_engine and try again
        if self.do_long_engine_upgrade:
            self.app.dispatch(
                FOQAEngineUpgrade(
                    id=self.id,
                    old_ctx_len=self.engine.max_context_size,
                    new_ctx_len=self.app.long_engine.max_context_size,
                )
            )
            self.engine = self.app.long_engine
            if (retrieved_tokens := self.message_token_len(ChatMessage.user(full_content))) <= self.max_search_tokens:
                self.app.dispatch(
                    FOQARetrievalType(
                        id=self.id,
                        retrieval_type="full_doc_long",
                        retrieved_tokens=retrieved_tokens,
                        max_search_tokens=self.max_search_tokens,
                    )
                )
                return full_content

        # else, retrieve as many fragments as fit in the context window
        if self.retrieval_type == "bm25":
            corpus = BM25Corpus([found_article], doc_len=1024)
        else:
            corpus = OpenAICorpus([found_article], doc_len=1024, embedding_model="text-embedding-3-small")
        user_query = self.last_user_message.text
        retrieved_docs = []
        for doc in corpus.best(user_query):
            formatted = f"<fragment>\n{doc.content}\n</fragment>\n"
            content = prompt.format("".join(retrieved_docs) + formatted)
            doc_len = self.engine.message_len(ChatMessage.user(content))
            if doc_len > self.max_search_tokens:
                break
            retrieved_docs.append(formatted)

        # return
        out = prompt.format("".join(retrieved_docs))
        retrieved_tokens = self.engine.message_len(ChatMessage.user(out))
        self.app.dispatch(
            FOQARetrievalType(
                id=self.id,
                retrieval_type=self.retrieval_type,
                retrieved_tokens=retrieved_tokens,
                max_search_tokens=self.max_search_tokens,
            )
        )
        return out
