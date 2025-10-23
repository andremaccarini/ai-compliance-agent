# ingest.py — document ingestion and FAISS index builder

import os, json, glob
from tqdm import tqdm
import numpy as np
import faiss
from models.embedding import get_embedding_model
from ingestion.splitters import split_text
import yaml

# ---------------------------------------------------------------------------
# Load configuration (paths and embedding model)
# ---------------------------------------------------------------------------

CFG = yaml.safe_load(open('configs/config.yaml', 'r'))

INDEX_PATH = CFG['retrieval']['index_path']
META_PATH  = CFG['retrieval']['metadata_path']
EMB_MODEL  = CFG['retrieval']['embedding_model']


# File patterns for ingestion (policies and laws)
DOC_GLOBS = ['data/policies/*.md', 'data/laws/*.md']


def load_documents():

    """
    Read all markdown files matching DOC_GLOBS and return as dict list.

    Returns:
        List[dict]: [{'path': str, 'text': str}, ...]
    """

    docs = []
    for pattern in DOC_GLOBS:
        for path in glob.glob(pattern):
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
            docs.append({'path': path, 'text': text})
    return docs

def build_index():

    """
    Split, embed, and index all loaded documents into FAISS for semantic retrieval.

    Process:
        1. Split each document into overlapping chunks.
        2. Convert each chunk to a vector embedding.
        3. Build an inner-product FAISS index.
        4. Save both index and metadata to disk.
    """

    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    model = get_embedding_model(EMB_MODEL)

    vectors = []
    metadatas = []

    # Iterate over each document and embed its chunks
    for doc in tqdm(load_documents(), desc='Splitting & embedding'):
        chunks = split_text(doc['text'], max_chars=1200, overlap=150)
        for i, chunk in enumerate(chunks):
            vec = model.encode(chunk, normalize_embeddings=True)
            vectors.append(vec)
            metadatas.append({
                'doc_path': doc['path'],
                'chunk_id': i,
                'text': chunk
            })

    if not vectors:
        raise RuntimeError('No documents found to index.')

    # Stack all vectors into a single matrix (float32 required by FAISS)
    mat = np.vstack(vectors).astype('float32')

    # Create a simple Inner Product index (IP ≈ cosine when normalized)
    index = faiss.IndexFlatIP(mat.shape[1])
    index.add(mat)
    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, 'w', encoding='utf-8') as f:
        json.dump(metadatas, f, ensure_ascii=False, indent=2)

    print(f'Indexed {len(metadatas)} chunks -> {INDEX_PATH}')
    print(f'Metadata saved -> {META_PATH}')

# ---------------------------------------------------------------------------
# CLI entrypoint — allows running `python -m ingestion.ingest`
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    build_index()
