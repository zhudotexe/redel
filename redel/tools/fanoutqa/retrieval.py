"""This module contains a baseline implementation of a retriever for use with long Wikipedia articles"""

import abc
from dataclasses import dataclass
from typing import Iterable

import numpy as np
from fanoutqa import wiki_content
from fanoutqa.models import Evidence
from fanoutqa.norm import normalize
from rank_bm25 import BM25Plus

from redel.embeddings import get_embeddings


@dataclass
class RetrievalResult:
    title: str
    """The title of the article this fragment comes from."""

    content: str
    """The content of the fragment."""


class Corpus(abc.ABC):
    def best(self, q: str) -> Iterable[RetrievalResult]:
        raise NotImplementedError


class BM25Corpus(Corpus):
    """
    A corpus of wiki docs. Indexes the docs on creation, normalizing the text beforehand with lemmatization.

    Splits the documents into chunks no longer than a given length, preferring splitting on paragraph and sentence
    boundaries. Documents will be converted to Markdown.

    Uses BM25+ (Lv and Zhai, 2011), a TF-IDF based approach to retrieve document fragments.

    To retrieve chunks corresponding to a query, iterate over ``Corpus.best(query)``.

    .. code-block:: python

        # example of how to use in the Evidence Provided setting
        prompt = "..."
        corpus = fanoutqa.retrieval.Corpus(q.necessary_evidence)
        for fragment in corpus.best(q.question):
            # use your own structured prompt format here
            prompt += f"# {fragment.title}\\n{fragment.content}\\n\\n"
    """

    def __init__(self, documents: list[Evidence], doc_len: int = 2048):
        """
        :param documents: The list of evidences to index
        :param doc_len: The maximum length, in characters, of each chunk
        """

        self.documents = []
        normalized_corpus = []
        for doc in documents:
            title = doc.title
            content = wiki_content(doc)
            for chunk in chunk_text(content, max_chunk_size=doc_len):
                self.documents.append(RetrievalResult(title, chunk))
                normalized_corpus.append(self.tokenize(chunk))

        self.index = BM25Plus(normalized_corpus)

    @staticmethod
    def tokenize(text: str):
        return normalize(text).split(" ")

    def best(self, q: str) -> Iterable[RetrievalResult]:
        """Yield the best matching fragments to the given query."""

        tok_q = self.tokenize(q)
        scores = self.index.get_scores(tok_q)
        idxs = np.argsort(scores)[::-1]
        for idx in idxs:
            yield self.documents[idx]


class OpenAICorpus(Corpus):
    def __init__(self, documents: list[Evidence], embedding_model: str, doc_len: int = 2048):
        """
        :param documents: The list of evidences to index
        :param embedding_model: The embedding model to use
        :param doc_len: The maximum length, in characters, of each chunk
        """
        self.documents = []
        self.embedding_model = embedding_model

        # chunk docs
        for doc in documents:
            title = doc.title
            content = wiki_content(doc)
            for chunk in chunk_text(content, max_chunk_size=doc_len):
                self.documents.append(RetrievalResult(title, chunk))

        # create embeddings
        self.embeddings = get_embeddings([d.content for d in self.documents], self.embedding_model)

    def best(self, q: str) -> Iterable[RetrievalResult]:
        """Yield the best matching fragments to the given query."""
        (q_emb,) = get_embeddings([q], self.embedding_model)

        scores = [(self.documents[emb.idx], q_emb.embedding.dot(emb.embedding)) for emb in self.embeddings]
        for doc, score in sorted(scores, key=lambda pair: pair[1], reverse=True):
            yield doc


def chunk_text(text, max_chunk_size=1024, chunk_on=("\n\n", "\n", ". ", ", ", " "), chunker_i=0):
    """
    Recursively chunks *text* into a list of str, with each element no longer than *max_chunk_size*.
    Prefers splitting on the elements of *chunk_on*, in order.
    """

    if len(text) <= max_chunk_size:  # the chunk is small enough
        return [text]
    if chunker_i >= len(chunk_on):  # we have no more preferred chunk_on characters
        # optimization: instead of merging a thousand characters, just use list slicing
        return [text[:max_chunk_size], *chunk_text(text[max_chunk_size:], max_chunk_size, chunk_on, chunker_i + 1)]

    # split on the current character
    chunks = []
    split_char = chunk_on[chunker_i]
    for chunk in text.split(split_char):
        chunk = f"{chunk}{split_char}"
        if len(chunk) > max_chunk_size:  # this chunk needs to be split more, recurse
            chunks.extend(chunk_text(chunk, max_chunk_size, chunk_on, chunker_i + 1))
        elif chunks and len(chunk) + len(chunks[-1]) <= max_chunk_size:  # this chunk can be merged
            chunks[-1] += chunk
        else:
            chunks.append(chunk)

    # if the last chunk is just the split_char, yeet it
    if chunks[-1] == split_char:
        chunks.pop()

    # remove extra split_char from last chunk
    chunks[-1] = chunks[-1][: -len(split_char)]
    return chunks
