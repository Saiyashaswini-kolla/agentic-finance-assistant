import io
from pathlib import Path
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.agents import run_pipeline, retrieval_agent, _ABOUT_DOC
from app.retriever import Retriever

BASE = Path(__file__).resolve().parent.parent
app = FastAPI(title="Agentic Finance Research Assistant")

LARGE_DOC_CHUNKS = 80  # past this many chunks, switch to embedding retrieval if it is installed

demo_retriever = Retriever()  # the 4 sample reports, always available
for f in sorted((BASE / "data" / "sample").glob("*.txt")):
    demo_retriever.add_document(f.name, f.read_text())

uploaded_retriever = Retriever()  # only what THIS session has uploaded; starts empty
_embed_retriever = None  # built lazily from uploaded_retriever, rebuilt on each new upload


def build_embed_retriever(source_retriever):
    """Return an EmbedRetriever holding the same documents as source_retriever,
    or None if sentence-transformers is not installed."""
    try:
        from app.embed_retriever import EmbedRetriever
    except ImportError:
        return None
    er = EmbedRetriever()
    for source in dict.fromkeys(c.source for c in source_retriever.chunks):
        text = " ".join(c.text for c in source_retriever.chunks if c.source == source)
        er.add_document(source, text)
    return er


def active_retriever():
    """Once something real has been uploaded, answer ONLY from uploaded documents -
    the demo reports never compete with a real upload. Before any upload, use the
    demo reports so the app is usable out of the box. Large uploaded collections use
    embedding retrieval when it is available."""
    global _embed_retriever
    if not uploaded_retriever.chunks:
        return demo_retriever
    if len(uploaded_retriever.chunks) <= LARGE_DOC_CHUNKS:
        return uploaded_retriever
    if _embed_retriever is None:
        _embed_retriever = build_embed_retriever(uploaded_retriever) or uploaded_retriever
    return _embed_retriever


def pdf_to_text(data: bytes) -> str:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


class Query(BaseModel):
    question: str


@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/debug")
def debug(q: str = "What is the company name?"):
    """Diagnostic page: what does THIS running server currently have loaded, and
    what evidence would it actually retrieve for the question `q`? Visit as
    /debug or /debug?q=your+question"""
    r = active_retriever()
    ev = retrieval_agent(q, r)
    return {
        "uploaded_chunks": len(uploaded_retriever.chunks),
        "uploaded_sources": sorted({c.source for c in uploaded_retriever.chunks}),
        "demo_chunks": len(demo_retriever.chunks),
        "active_retriever_type": type(r).__name__,
        "active_retriever_chunks": len(r.chunks),
        "has_front_chunks_method": hasattr(r, "front_chunks"),
        "question": q,
        "about_doc_pattern_matched": bool(_ABOUT_DOC.search(q)),
        "evidence_count": len(ev),
        "evidence_preview": [{"n": e["n"], "source": e["source"], "text": e["text"][:80]} for e in ev],
        "evidence_full_text_of_item_1": ev[0]["text"] if ev else None,
        "analysis_findings": (lambda: __import__("app.agents", fromlist=["analysis_agent"])
                              .analysis_agent(q, ev))(),
    }


@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    data = await file.read()
    if file.filename.lower().endswith(".pdf"):
        text = pdf_to_text(data)
    else:
        text = data.decode("utf-8", errors="ignore")
    n = uploaded_retriever.add_document(file.filename, text)
    global _embed_retriever
    _embed_retriever = None  # force a rebuild, since the uploaded set just changed
    return {"source": file.filename, "chunks_added": n,
            "total_uploaded_chunks": len(uploaded_retriever.chunks)}


@app.post("/research")
def research(q: Query):
    return run_pipeline(q.question, active_retriever())