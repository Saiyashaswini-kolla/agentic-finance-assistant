"""Compare TF-IDF vs embedding retrieval: does the top chunk (top-1) or one of the 4 chunks
the pipeline actually sends to the model (top-4) contain the needed fact?
Run: python -m eval.compare   (embeddings need: pip install sentence-transformers)
Retrieval has no randomness, so re-running gives the same numbers. Only more questions help.
"""
from app.retriever import Retriever
from eval.cases import CASES
from eval.eval import load_corpus

ANSWERABLE = [c for c in CASES if c["expect"]]


def wilson(k, n, z=1.96):
    """Rough 95% interval for a hit rate k/n."""
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return (c - m) / d, (c + m) / d


def evaluate(retriever):
    load_corpus(retriever)
    hits = []
    for c in ANSWERABLE:
        top = [chunk.text for chunk, _ in retriever.search(c["q"], 4)]
        hits.append((any(c["expect"] in t for t in top[:1]),
                     any(c["expect"] in t for t in top[:4])))
    return hits


def report(label, hits):
    n = len(hits)
    k1 = sum(h[0] for h in hits)
    k2 = sum(h[1] for h in hits)
    lo, hi = wilson(k1, n)
    print(f"{label}: top-1 hit {k1}/{n} (95% range {lo:.0%}-{hi:.0%}), top-4 hit {k2}/{n}")
    for kind in ("same", "para"):
        idx = [i for i, c in enumerate(ANSWERABLE) if c["kind"] == kind]
        print(f"   {kind:>4}-wording questions: top-1 {sum(hits[i][0] for i in idx)}/{len(idx)}")
    for i, c in enumerate(ANSWERABLE):
        if not hits[i][0]:
            print(f"   missed at top-1: {c['q']}")
    print()


if __name__ == "__main__":
    results = {"TF-IDF": evaluate(Retriever())}
    try:
        from app.embed_retriever import EmbedRetriever
        results["Embeddings"] = evaluate(EmbedRetriever())
    except ImportError:
        print("Embeddings skipped: run  pip install sentence-transformers")
    for label, hits in results.items():
        report(label, hits)
    if len(results) == 2:
        a, b = results["TF-IDF"], results["Embeddings"]
        only_a = sum(x[0] and not y[0] for x, y in zip(a, b))
        only_b = sum(y[0] and not x[0] for x, y in zip(a, b))
        print(f"Only TF-IDF got it right: {only_a} questions. Only embeddings: {only_b} questions.")
