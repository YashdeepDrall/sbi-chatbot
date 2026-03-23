model = None


def get_model():
    global model
    if model is None:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2")
    return model


def generate_embedding(text):
    embedding = get_model().encode(text)

    return embedding
