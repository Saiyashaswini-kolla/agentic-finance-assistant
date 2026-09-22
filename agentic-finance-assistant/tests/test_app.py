from fastapi.testclient import TestClient
from app.main import app
from app.retriever import Retriever, chunk_text

client = TestClient(app)


def test_chunking_overlap():
    words = " ".join(str(i) for i in range(300))
    assert len(chunk_text(words)) >= 3


def test_retriever_finds_relevant_chunk():
    r = Retriever()
    r.add_document("a.txt", "Revenue grew strongly this year due to online sales.")
    r.add_document("b.txt", "The weather was mild and the office cafeteria reopened.")
    assert r.search("revenue growth")[0][0].source == "a.txt"


def test_research_endpoint():
    res = client.post("/research", json={"question": "What are the risks?"})
    assert res.status_code == 200
    assert "## Sources" in res.json()["memo"]


def test_groundedness_flags_number_hidden_inside_another_number():
    from eval.eval import score
    result = {
        "query": "How is debt?",
        "evidence": [{"n": 1, "source": "a", "text": "Debt was 1,470 crore."}],
        "memo": "Revenue grew 47 percent [1]\n\n## Sources\n[1] a",
    }
    assert score(result)["unsupported_numbers"] == ["47"]


def test_groundedness_flags_missing_citation():
    from eval.eval import score
    result = {
        "query": "x",
        "evidence": [],
        "memo": "Nothing found [1]\n\n## Sources\n",
    }
    assert score(result)["bad_citations"] == [1]


def test_groundedness_flags_invented_number_words():
    from eval.eval import score
    result = {
        "query": "q",
        "evidence": [{"n": 1, "source": "a", "text": "Revenue rose 12 percent."}],
        "memo": "Revenue nearly doubled [1]\n\n## Sources\n[1] a",
    }
    assert score(result)["unsupported_words"] == ["doubled"]


def test_invalid_citation_is_removed(monkeypatch):
    import app.agents as ag
    monkeypatch.setattr(ag, "complete", lambda *a, **k: "Debt fell [1] and rose [9].")
    ev = [{"n": 1, "source": "a.txt", "text": "Debt fell."}]
    memo = ag.report_agent("q", "f", ev)
    assert "[9]" not in memo and "[1] a.txt" in memo and "fell [1]" in memo


def test_numbered_list_markers_are_not_flagged():
    from eval.eval import score
    result = {
        "query": "q",
        "evidence": [{"n": 1, "source": "a", "text": "Bad loans fell to 2.1 percent."}],
        "memo": "1. Bad loans fell to 2.1 percent [1]\n2. Nothing else [1]\n\n## Sources\n[1] a",
    }
    assert score(result)["unsupported_numbers"] == []


def test_combined_citation_is_parsed_not_flagged():
    from eval.eval import score
    result = {
        "query": "q",
        "evidence": [{"n": 1, "source": "a", "text": "Debt fell."},
                     {"n": 2, "source": "b", "text": "Debt fell more."}],
        "memo": "Debt fell [1, 2]\n\n## Sources\n[1] a\n[2] b",
    }
    s = score(result)
    assert s["unsupported_numbers"] == [] and s["bad_citations"] == []


def test_invalid_number_inside_combined_citation_is_removed(monkeypatch):
    import app.agents as ag
    monkeypatch.setattr(ag, "complete", lambda *a, **k: "Debt fell [1, 9].")
    ev = [{"n": 1, "source": "a.txt", "text": "Debt fell."}]
    memo = ag.report_agent("q", "f", ev)
    assert "9" not in memo.split("## Sources")[0] and "fell [1]" in memo


def test_chunks_never_cut_a_sentence_in_half():
    text = ("Revenue rose 12 percent to 4,820 crore. Debt fell to 1,150 crore. "
            "The board proposed a dividend of 6 rupees per share. Risks include competition. ") * 5
    chunks = chunk_text(text, size=20)
    assert len(chunks) > 1
    assert all(c.endswith(".") for c in chunks)


def test_sources_list_only_shows_cited_evidence(monkeypatch):
    import app.agents as ag
    monkeypatch.setattr(ag, "complete", lambda *a, **k: "Debt fell [1].")
    ev = [{"n": 1, "source": "a.txt", "text": "Debt fell."},
          {"n": 2, "source": "b.txt", "text": "Unrelated."}]
    memo = ag.report_agent("q", "f", ev)
    sources = memo.split("## Sources")[1]
    assert "a.txt" in sources and "b.txt" not in sources


def test_number_cited_to_the_wrong_chunk_is_flagged():
    from eval.eval import score
    result = {
        "query": "q",
        "evidence": [{"n": 1, "source": "a", "text": "Debt fell to 1,150 crore."},
                     {"n": 2, "source": "b", "text": "Revenue was 4,820 crore."}],
        "memo": "Revenue was 4,820 crore [1]\n\n## Sources\n[1] a",
    }
    s = score(result)
    assert s["unsupported_numbers"] == [] and s["misattributed_numbers"] == ["4820"]


def test_number_cited_to_the_right_chunk_passes():
    from eval.eval import score
    result = {
        "query": "q",
        "evidence": [{"n": 1, "source": "a", "text": "Debt fell to 1,150 crore."},
                     {"n": 2, "source": "b", "text": "Revenue was 4,820 crore."}],
        "memo": "- Debt fell to 1,150 crore [1]\n- Revenue was 4,820 crore [2]\n\n## Sources\n[1] a\n[2] b",
    }
    assert score(result)["misattributed_numbers"] == []
