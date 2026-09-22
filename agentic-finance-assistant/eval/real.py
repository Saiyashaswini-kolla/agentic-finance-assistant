"""Test on your own REAL reports instead of the fictional ones.
1. Put PDFs (or .txt files) in  data/real/
2. Write questions in  eval/real_cases.py
Run from the inner project folder:
    python -m eval.real peek                 # how does the text of each file look?
    python -m eval.real check                # does each expected snippet exist in the reports?
    python -m eval.real retrieval            # TF-IDF vs embeddings (no Gemini needed)
    python -u -m eval.real grounded 0 10     # groundedness with Gemini, questions 0-9
"""
import os
import re
import sys
import time
from pathlib import Path
from app import llm
from app.agents import run_pipeline
from app.retriever import Retriever
from eval.compare import wilson
from eval.eval import score
from eval.real_cases import REAL_CASES

DIR = Path("data/real")


def read_file(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)
    return path.read_text(errors="ignore")


def files():
    return [f for f in sorted(DIR.glob("*")) if f.suffix.lower() in (".pdf", ".txt")]


def load_real(retriever):
    for f in files():
        n = retriever.add_document(f.name, read_file(f))
        print(f"  loaded {f.name}: {n} chunks")


def norm(s: str) -> str:
    return " ".join(s.lower().split())


def need_cases():
    if not REAL_CASES:
        print("No questions yet. Add them to eval/real_cases.py first.")
        raise SystemExit(1)
    if not files():
        print("No files in data/real. Put your PDFs there first.")
        raise SystemExit(1)


def peek():
    for f in files():
        text = read_file(f)
        pages = len(__import__("pypdf").PdfReader(str(f)).pages) if f.suffix.lower() == ".pdf" else "-"
        print(f"\n== {f.name}: pages {pages}, {len(text.split())} words")
        print(text[:500].replace("\n", " "))


def check():
    need_cases()
    corpus = norm(" ".join(read_file(f) for f in files()))
    bad = [c for c in REAL_CASES if c["expect"] and norm(c["expect"]) not in corpus]
    for c in bad:
        print("NOT FOUND in the text:", c["expect"], "  <-", c["q"])
    print(f"{len(REAL_CASES) - len(bad)}/{len(REAL_CASES)} expected snippets found")


def hit_rates(retriever, label):
    print(f"{label}:")
    load_real(retriever)
    cases = [c for c in REAL_CASES if c["expect"]]
    h1 = h4 = 0
    for c in cases:
        top = [norm(ch.text) for ch, _ in retriever.search(c["q"], 4)]
        e = norm(c["expect"])
        a = any(e in t for t in top[:1])
        b = any(e in t for t in top[:4])
        h1 += a
        h4 += b
        if not b:
            print("   missed in top 4:", c["q"])
    n = len(cases)
    lo, hi = wilson(h1, n)
    print(f"   top-1 {h1}/{n} (95% range {lo:.0%}-{hi:.0%}), top-4 {h4}/{n}\n")


def retrieval():
    need_cases()
    hit_rates(Retriever(), "TF-IDF")
    try:
        from app.embed_retriever import EmbedRetriever
        hit_rates(EmbedRetriever(), "Embeddings")
    except ImportError:
        print("Embeddings skipped: pip install sentence-transformers")


def has_answer(memo: str, alts) -> bool:
    body = memo.split("## Sources")[0].lower().replace(",", "")
    return any(re.search(r"(?<![\w.])" + re.escape(a.lower().replace(",", "")) + r"(?!\w)", body)
               for a in alts)


def refused(memo: str) -> bool:
    m = memo.lower()
    return "does not answer" in m or "no relevant evidence" in m


def grounded(start, end):
    need_cases()
    r = Retriever()
    load_real(r)
    live = bool(os.getenv("GEMINI_API_KEY"))
    subset = REAL_CASES[start:end]
    bad = 0
    right = wrong = ref_ok = ref_bad = 0
    for i, c in enumerate(subset):
        if live and i:
            time.sleep(9)
        result = run_pipeline(c["q"], r)
        s = score(result)
        ok = not (s["unsupported_numbers"] or s["unsupported_words"] or s["bad_citations"]
                  or s["misattributed_numbers"])
        bad += not ok
        if c["expect"] is None:
            good = refused(result["memo"])
            ref_ok += good
            ref_bad += not good
            verdict = "REFUSED (good)" if good else "ANSWERED AN UNANSWERABLE QUESTION"
        else:
            good = has_answer(result["memo"], c.get("answer", []))
            right += good
            wrong += not good
            verdict = "ANSWER FOUND" if good else "ANSWER MISSING"
        print(("PASS" if ok else "FAIL"), "|", verdict, "|", c["q"], s)
    print(f"\n{len(subset) - bad}/{len(subset)} grounded (no invented numbers or citations)")
    print(f"Correct answer present: {right}/{right + wrong} answerable | "
          f"refused correctly: {ref_ok}/{ref_ok + ref_bad} unanswerable")
    print(f"Gemini calls ok: {llm.STATS['ok']}, failed: {llm.STATS['failed']}")
    if live and llm.STATS["failed"]:
        print("WARNING: some answers fell back to offline mode, so this is NOT a valid AI result.")
        raise SystemExit(2)
    raise SystemExit(1 if bad else 0)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "retrieval"
    if mode == "peek":
        peek()
    elif mode == "check":
        check()
    elif mode == "retrieval":
        retrieval()
    elif mode == "grounded":
        s = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        e = int(sys.argv[3]) if len(sys.argv) > 3 else len(REAL_CASES)
        grounded(s, e)
    else:
        print(__doc__)
