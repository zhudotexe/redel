import functools
import hashlib
from dataclasses import dataclass
from typing import Iterable

import numpy as np
from openai import OpenAI

from redel import config
from redel.utils import batched

VECTOR_CACHE_DIR = config.REDEL_CACHE_DIR / "embeddings"
VECTOR_CACHE_DIR.mkdir(exist_ok=True, parents=True)


# this is a function to init lazily only if we need it
@functools.cache
def get_embedding_client():
    return OpenAI()


@dataclass
class EmbeddingResult:
    idx: int
    """The index of the input text in its input list."""
    embedding: np.ndarray
    """The embedding returned by the server (an array of floats)."""


def get_embeddings(qs: list[str], model: str) -> list[EmbeddingResult]:
    """Get the embeddings for the inputs, caching them."""
    result = []
    uncached = []
    uncached_to_normal_idx = {}
    fp_cache = {}

    # find cached vecs
    for idx, text in enumerate(qs):
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        cache_dir = VECTOR_CACHE_DIR / model
        cache_dir.mkdir(exist_ok=True)
        fp = cache_dir / f"{text_hash}.npy"
        if fp.exists():
            try:
                vec = np.load(fp)
                result.append(EmbeddingResult(idx=idx, embedding=vec))
            except Exception:
                fp_cache[text] = fp
                uncached_to_normal_idx[len(uncached)] = idx
                uncached.append(text)
        else:
            fp_cache[text] = fp
            uncached_to_normal_idx[len(uncached)] = idx
            uncached.append(text)

    # embed uncached vecs
    if uncached:
        for emb in _get_embeddings_openai_batch(uncached, model):
            text = uncached[emb.idx]
            idx = uncached_to_normal_idx[emb.idx]
            vec = emb.embedding
            fp = fp_cache[text]
            np.save(fp, vec)
            result.append(EmbeddingResult(idx=idx, embedding=vec))

    assert len(result) == len(qs)
    return sorted(result, key=lambda r: r.idx)


def _get_embeddings_openai_batch(texts: list[str], model) -> Iterable[EmbeddingResult]:
    batch_size = 2048
    embed_client = get_embedding_client()

    for batchnum, batch in enumerate(batched(texts, batch_size)):
        for emb in embed_client.embeddings.create(input=list(batch), model=model).data:
            vec = np.array(emb.embedding, dtype=np.float64)
            yield EmbeddingResult(idx=batchnum * batch_size + emb.index, embedding=vec)
