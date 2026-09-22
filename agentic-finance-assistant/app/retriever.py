"""TF-IDF retriever over document chunks (no external vector DB needed)."""
import re
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class Chunk:
    id: int
    source: str
    text: str


def chunk_text(text: str, size: int = 120) -> list[str]:
    """Pack whole sentences into chunks of about `size` words.
    A sentence is never cut in half (unless it alone is longer than `size`),
    and chunks do not overlap, so the same sentence is never retrieved twice."""
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
    chunks, current, count = [], [], 0
    for sent in sentences:
        n = len(sent.split())
        if current and count + n > size:
            chunks.append(" ".join(current))
            current, count = [], 0
        if n > size:  # one very long sentence: fall back to cutting by words
            words = sent.split()
            chunks.extend(" ".join(words[k:k + size]) for k in range(0, n, size))
            continue
        current.append(sent)
        count += n
    if current:
        chunks.append(" ".join(current))
    return chunks


def doc_title(source: str) -> str:
    """'acme_annual_report.txt' -> 'acme annual report' (context added when indexing)."""
    return re.sub(r"[_\-]+", " ", source.rsplit(".", 1)[0])


class Retriever:
    def __init__(self):
        self.chunks: list[Chunk] = []
        self.vectorizer = None
        self.matrix = None

    def add_document(self, source: str, text: str) -> int:
        self.chunks = [c for c in self.chunks if c.source != source]  # replace, don't duplicate
        new = chunk_text(text)
        for t in new:
            self.chunks.append(Chunk(len(self.chunks), source, t))
        self._fit()
        return len(new)

    def _fit(self):
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(
            [f"{doc_title(c.source)} {c.text}" for c in self.chunks])

    def front_chunks(self, n: int = 1) -> list[Chunk]:
        """The first n chunks of every uploaded document (cover, contents, introduction)."""
        count, out = {}, []
        for c in self.chunks:
            if count.get(c.source, 0) < n:
                count[c.source] = count.get(c.source, 0) + 1
                out.append(c)
        return out

    def search(self, query: str, k: int = 4):
        if not self.chunks:
            return []
        scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix)[0]
        top = scores.argsort()[::-1][:k]
        return [(self.chunks[i], float(scores[i])) for i in top if scores[i] > 0]
