# retriever.py - vector retrieval module (FAISS + embeddings)

import json
import numpy as np
import faiss
import yaml
from models.embedding import get_embedding_model


# Load configuration parameters from config.yaml
CFG = yaml.safe_load(open('configs/config.yaml', 'r'))
INDEX_PATH = CFG['retrieval']['index_path']
META_PATH  = CFG['retrieval']['metadata_path']
EMB_MODEL  = CFG['retrieval']['embedding_model']
TOP_K      = int(CFG['retrieval'].get('top_k', 4))


# Lazy-loaded global objects to avoid reloading FAISS/model on every query
_index = None
_meta  = None
_model = None



def _load():

    """
    Lazy-load the FAISS index, metadata, and embedding model.
    Called implicitly by search() to ensure dependencies are ready.
    """

    global _index, _meta, _model
    if _index is None:
        _index = faiss.read_index(INDEX_PATH)
    if _meta is None:
        _meta = json.load(open(META_PATH, 'r', encoding='utf-8'))
    if _model is None:
        _model = get_embedding_model(EMB_MODEL)

def search(query: str, k: int = TOP_K):

    """
    Run a semantic search over the local FAISS index.

    Args:
        query: user text to retrieve relevant policy excerpts for.
        k:     number of nearest chunks to return (defaults to config TOP_K).

    Returns:
        List[dict]: each hit has score, doc_path, chunk_id, and text.
    """

    _load()
    qvec = _model.encode([query], normalize_embeddings=True).astype('float32')
    scores, idxs = _index.search(qvec, k)
    hits = []
    for score, idx in zip(scores[0], idxs[0]):
        if idx == -1: 
            continue
        md = _meta[int(idx)]
        md_out = {
            'score': float(score),
            'doc_path': md['doc_path'],
            'chunk_id': md['chunk_id'],
            'text': md['text'],
        }
        hits.append(md_out)
    return hits

def format_citations(hits):

    """
    Extract lightweight citation info from retrieved chunks.

    - Attempts to detect an 'Art. X' pattern in the chunk text.
    - Returns a compact structure to render inline or in a citations block.

    Args:
        hits: output from search().

    Returns:
        List[dict]: each item has source (filename), article (if found),
                    chunk_id, and score.
    """

    results = []

    import re

    for h in hits:
        # Try to capture "Art. 12" style markers to improve citation quality
        article = None
        m = re.search(r'Art\.\s*(\d+)', h['text'])
        if m:
            article = m.group(1)
        results.append({
            'source': h['doc_path'].split('/')[-1],
            'article': article,
            'chunk_id': h['chunk_id'],
            'score': h['score']
        })
    return results
