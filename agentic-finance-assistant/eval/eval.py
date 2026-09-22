"""Groundedness check: every number and citation in the memo must trace to evidence.
Run: python -m eval.eval
"""
import os
import re
import sys
import time
from pathlib import Path
from app import llm
from app.agents import run_pipeline
from app.retriever import Retriever
from eval.cases import CASES

QUESTIONS = [c["q"] for c in CASES]
DATA_DIRS = ["data/sample", "data/eval"]


def load_corpus(retriever):
    for d in DATA_DIRS:
        for f in sorted(Path(d).glob("*.txt")):
            retriever.add_document(f.name, f.read_text())


def numbers(text: str) -> set[str]:
    return set(re.findall(r"\d[\d,\.]*", text))


CITE = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")  # matches [1] and [1, 2]

NUMBER_WORDS = re.compile(
    r"\b(?:two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|"
    r"fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|"
    r"forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|billion|half|"
    r"third|fifth|tenth|dozen|double|doubled|doubling|triple|tripled|tripling|halved|"
    r"twofold|threefold|tenfold)\b", re.I)


def norm(n: str) -> str:
    return n.rstrip(".,").replace(",", "")


def clean(nums: set[str]) -> set[str]:
    return {norm(n) for n in nums if norm(n)}


def words(text: str) -> set[str]:
    return {w.lower() for w in NUMBER_WORDS.findall(text)}


def misattributed(body: str, evidence: list, query: str) -> list[str]:
    """Numbers in a cited line that are NOT in the chunk(s) that line cites."""
    by_n = {e["n"]: clean(numbers(e["text"])) for e in evidence}
    skip = {"2025", "2026"} | clean(numbers(query))
    bad = set()
    for line in body.split("\n"):
        cites = {int(n) for m in CITE.findall(line) for n in re.findall(r"\d+", m)}
        if not cites:
            continue
        text = re.sub(r"(?m)^\s*[*\-]?\s*\d+[.)]\s+", "", CITE.sub("", line))
        allowed = set().union(*(by_n.get(n, set()) for n in cites))
        bad |= {n for n in clean(numbers(text)) - skip if n not in allowed}
    return sorted(bad)


def score(result: dict) -> dict:
    evidence_text = " ".join(e["text"] for e in result["evidence"])
    evidence_nums = clean(numbers(evidence_text))
    body = result["memo"].split("## Sources")[0]
    body_no_cites = CITE.sub("", body)
    body_no_cites = re.sub(r"(?m)^\s*\d+[.)]\s+", "", body_no_cites)  # ignore list markers "1. "
    query_nums = clean(numbers(result.get("query", "")))
    memo_nums = clean(numbers(body_no_cites)) - {"2025", "2026"} - query_nums
    unsupported = sorted(n for n in memo_nums if n not in evidence_nums)
    cited = {int(n) for m in CITE.findall(body) for n in re.findall(r"\d+", m)}
    valid = {e["n"] for e in result["evidence"]}
    unsupported_words = sorted(words(body) - words(evidence_text) - words(result.get("query", "")))
    return {"unsupported_numbers": unsupported, "unsupported_words": unsupported_words,
            "bad_citations": sorted(cited - valid),
            "misattributed_numbers": misattributed(body, result["evidence"], result.get("query", ""))}


if __name__ == "__main__":
    # optional: python -m eval.eval 10 15  runs only questions 11-15
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else len(QUESTIONS)
    subset = QUESTIONS[start:end]
    r = Retriever()
    load_corpus(r)
    live = bool(os.getenv("GEMINI_API_KEY"))
    bad = 0
    for i, q in enumerate(subset):
        if live and i:
            time.sleep(9)  # stay under the free tier's 15 calls per minute
        s = score(run_pipeline(q, r))
        ok = not (s["unsupported_numbers"] or s["unsupported_words"] or s["bad_citations"]
                  or s["misattributed_numbers"])
        bad += not ok
        print(("PASS" if ok else "FAIL"), q, s)
    print(f"\n{len(subset) - bad}/{len(subset)} grounded")
    print(f"Gemini calls ok: {llm.STATS['ok']}, failed: {llm.STATS['failed']}")
    if live and llm.STATS["failed"]:
        print("WARNING: some answers fell back to offline mode, so this is NOT a valid AI result.")
        raise SystemExit(2)
    raise SystemExit(1 if bad else 0)
