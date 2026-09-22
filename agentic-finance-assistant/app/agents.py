"""Three cooperating agents: retrieval -> analysis -> report."""
import re
from app.llm import complete
from app.retriever import Retriever


# Questions about the document as a whole ("who published this?", "what does it cover?").
# Their words rarely appear in the body text, so keyword search misses the opening pages.
_ABOUT_DOC = re.compile(
    r"\b(publish\w*|issued by|author|who wrote|which company|what company|"
    r"company'?s? name|name of (the|this) (company|report)|"
    r"what is this (report|document)|(report|document) (is )?about|"
    r"title of|which quarter|which period|what period)\b", re.I)


def retrieval_agent(query: str, retriever: Retriever, k: int = None) -> list[dict]:
    if k is None:  # send more evidence for larger document collections, capped so
        n = len(retriever.chunks)  # cost and prompt size stay bounded on very large ones
        k = 4 if n <= 20 else min(4 + n // 15, 30)
    hits = retriever.search(query, k)
    if _ABOUT_DOC.search(query) and hasattr(retriever, "front_chunks") and retriever.chunks:
        last = retriever.chunks[-1].source  # the most recently uploaded document
        score_of = {c.id: s for c, s in hits}
        front = [(c, score_of.get(c.id, 0.0)) for c in retriever.front_chunks(3) if c.source == last]
        front_ids = {c.id for c, _ in front}
        rest = [h for h in hits if h[0].id not in front_ids][:2]
        hits = front + rest
    return [
        {"n": i + 1, "source": c.source, "score": round(s, 3), "text": c.text}
        for i, (c, s) in enumerate(hits)
    ]


def _format_evidence(evidence: list[dict]) -> str:
    return "\n\n".join(f"[{e['n']}] ({e['source']}) {e['text']}" for e in evidence)


def _strip_bad_citations(text: str, evidence: list[dict]) -> str:
    """Keep only citations that point at real evidence. Handles [1] and [1, 2]."""
    valid = {e["n"] for e in evidence}
    # Remove brackets the model filled with words, e.g. "[The evidence does not answer this.]"
    text = re.sub(r"\s?\[(?:the )?evidence[^\]\n]*\]", "", text, flags=re.I)

    def fix(m):
        keep = [n for n in re.findall(r"\d+", m.group(1)) if int(n) in valid]
        return (" [" + ", ".join(keep) + "]") if keep else ""

    return re.sub(r"\s?\[(\d+(?:\s*,\s*\d+)*)\]", fix, text)


def analysis_agent(query: str, evidence: list[dict]) -> str:
    if not evidence:
        return "No relevant evidence found."
    system = ("You are a financial analyst. Use ONLY the numbered evidence. "
              "Write up to 5 bullet findings, each ending with its citation, one number per "
              "bracket, like [1] or [1][2]. Each bullet must restate a fact that is actually "
              "written in the evidence it cites - this includes plain facts such as names, "
              "titles, dates and periods, not just numbers. "
              "For any numeric figure: copy it exactly as written, do not calculate, round, "
              "or add descriptions such as 'double-digit' or 'nearly half'; give the unit the "
              "evidence states (for example 'millions of SDRs'); and name the entity or "
              "department it belongs to. If the question does not name an entity, give the "
              "figures for each entity in the evidence and do not say or imply the list is "
              "complete. Do not add breakdowns that were not asked for. "
              "Never say a fact is repeated or mentioned elsewhere. "
              "Only reply 'The evidence does not answer this.' if the evidence truly contains "
              "nothing relevant to the question - not merely because it lacks a number.")
    out = complete(system, f"Question: {query}\n\nEvidence:\n{_format_evidence(evidence)}")
    if out:
        return _strip_bad_citations(out, evidence)
    # Offline fallback: first sentence of each evidence chunk
    lines = []
    for e in evidence[:4]:
        first = re.split(r"(?<=[.!?])\s", e["text"])[0]
        lines.append(f"- {first} [{e['n']}]")
    return "\n".join(lines)


def report_agent(query: str, findings: str, evidence: list[dict]) -> str:
    if not evidence:
        return (f"## Summary\nNo relevant evidence was found for: {query}\n\n"
                "## Key Findings\nNo relevant evidence found.\n\n"
                "## Sources\n(none)")
    if findings.strip().lower().startswith("the evidence does not answer this"):
        return (f"## Summary\nThe evidence does not answer this question: {query}\n\n"
                "## Key Findings\nNo relevant evidence found.\n\n"
                "## Risks\nNone stated in the evidence.\n\n"
                "## Sources\n(none)")
    system = ("You write concise investment memos in markdown with sections: "
              "Summary, Key Findings, Risks. Use only the findings and keep their citations "
              "exactly as written. Under Risks, list only risks that appear in the findings; "
              "if there are none, write: None stated in the evidence. "
              "Add no facts, numbers or commentary beyond the findings.")
    out = complete(system, f"Question: {query}\n\nFindings:\n{findings}", max_tokens=1200)
    if not out:
        out = (f"## Summary\nResearch on: {query}\n\n## Key Findings\n{findings}\n\n"
               "## Risks\nOffline mode: no model-generated risk analysis.")
    out = _strip_bad_citations(out, evidence)
    cited = {int(n) for m in re.findall(r"\[(\d+(?:\s*,\s*\d+)*)\]", out)
             for n in re.findall(r"\d+", m)}
    sources = "\n".join(f"[{e['n']}] {e['source']}" for e in evidence if e["n"] in cited)
    return f"{out}\n\n## Sources\n{sources or '(none)'}"


def run_pipeline(query: str, retriever: Retriever) -> dict:
    evidence = retrieval_agent(query, retriever)
    findings = analysis_agent(query, evidence)
    memo = report_agent(query, findings, evidence)
    return {"query": query, "evidence": evidence, "findings": findings, "memo": memo}