# Agentic Finance Research Assistant

A retrieval-augmented question-answering web app. Ask a question about company reports
(`.txt` or `.pdf`) and get a short investment memo with citations.

**How it works**

1. **Retrieval agent** cuts the reports into sentence-aware chunks and finds the best ones (TF-IDF).
2. **Analysis agent** asks an LLM (Gemini) to write findings using only that evidence.
3. **Report agent** writes the memo. **Code, not the LLM, writes the Sources list**, and any citation that
   does not point at real evidence is removed.
4. A separate **groundedness check** flags any number, number word or citation in a memo
   that is missing from the retrieved evidence.

Without an API key the app still runs in an offline mode (it copies the first sentence of each retrieved chunk).

![Example answer](demo1.png)
![Unanswerable question](demo2.png)

## Run locally

    python -m venv .venv
    .venv\Scripts\activate           # Mac/Linux: source .venv/bin/activate
    pip install -r requirements.txt
    pytest -q                        # 14 passed
    uvicorn app.main:app --reload    # open http://localhost:8000

Optional AI mode: set `GEMINI_API_KEY` (and `MODEL`, for example `gemini-3.5-flash-lite`) in the terminal
before starting the server. Never put a key in a file.

Try asking: "What is the debt situation?" or "What was the CEO's salary?" (the report does not say).

## Run with Docker

    docker build -t finance-agent .
    docker run -p 7860:7860 -e GEMINI_API_KEY="your-key" -e MODEL="gemini-3.5-flash-lite" finance-agent

Then open http://localhost:7860.

## Evaluation

Data: 4 fictional reports (`data/sample`, `data/eval`). 41 questions in `eval/cases.py`
(35 answerable, 6 unanswerable). The questions were written by the author, so results are
optimistic compared with real reports.

    python -m eval.eval 0 14        # groundedness on questions 1-14 (needs GEMINI_API_KEY)
    python -m eval.compare          # TF-IDF vs embeddings (pip install sentence-transformers)

**Groundedness with Gemini (41 questions):** 37/41 before prompt and chunking fixes, 40/41 after.
Gemini's wording varies between runs, so a difference of about 2 questions is noise. The remaining
failure was a summary that wrote "over half" for 58 percent: true, but not in the evidence.

**Retrieval (35 answerable questions, top-1 hit):** TF-IDF 24/35 vs MiniLM embeddings 31/35.
Embeddings were ahead on paraphrased wording (16/18 vs 10/18); TF-IDF was ahead on exact-term
questions. Both had the needed fact in the top 4 chunks on all 35.

## Known limits

- The check covers numbers, number words and citations only. It cannot catch a real figure attached
  to the wrong fact, or a misleading claim that contains no figures.
- Small synthetic corpus; settings were tuned on the same questions used for the results.
- Uploaded reports live in memory and disappear when the server restarts. Scanned PDFs are not supported.
