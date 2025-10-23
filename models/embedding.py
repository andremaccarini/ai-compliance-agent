from sentence_transformers import SentenceTransformer


def get_embedding_model(model_name: str = 'sentence-transformers/all-MiniLM-L6-v2'):

    """
    Load and return a sentence-transformers embedding model.

    Args:
        model_name: name or path of the pretrained model (default = MiniLM-L6-v2).

    Returns:
        SentenceTransformer: model instance ready to encode text into embeddings.

    Notes:
        - Used by ingestion (to embed documents) and by retrieval (to embed queries).
        - MiniLM-L6-v2 is small and efficient for local FAISS-based search.
    """

    return SentenceTransformer(model_name)
