"""Embedding-based retriever. Same interface as Retriever, different matching."""
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from app.retriever import chunk_text, doc_title


@dataclass
class Chunk:
    id: int
    source: str
    text: str


class EmbedRetriever:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.chunks: list[Chunk] = []
        self.matrix = None

    def add_document(self, source: str, text: str) -> int:
        self.chunks = [c for c in self.chunks if c.source != source]  # replace, don't duplicate
        new = chunk_text(text)
        for t in new:
            self.chunks.append(Chunk(len(self.chunks), source, t))
        self.matrix = self.model.encode(
            [f"{doc_title(c.source)}. {c.text}" for c in self.chunks])
        return len(new)

    def front_chunks(self, n: int = 1) -> list[Chunk]:
        """The first n chunks of every document (cover, contents, introduction)."""
        count, out = {}, []
        for c in self.chunks:
            if count.get(c.source, 0) < n:
                count[c.source] = count.get(c.source, 0) + 1
                out.append(c)
        return out

    def search(self, query: str, k: int = 4):
        if not self.chunks:
            return []
        qv = self.model.encode([query])
        scores = cosine_similarity(qv, self.matrix)[0]
        top = scores.argsort()[::-1][:k]
        return [(self.chunks[i], float(scores[i])) for i in top]
