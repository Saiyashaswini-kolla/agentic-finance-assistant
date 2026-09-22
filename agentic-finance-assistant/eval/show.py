"""Show one question's evidence, check result and memo.  Usage: python -m eval.show 27"""
import sys
from app.retriever import Retriever
from app.agents import run_pipeline
from eval.eval import QUESTIONS, load_corpus, score

i = int(sys.argv[1])
r = Retriever()
load_corpus(r)
d = run_pipeline(QUESTIONS[i], r)
print("QUESTION:", d["query"])
print("EVIDENCE:", [(e["n"], e["source"]) for e in d["evidence"]])
print("CHECK:", score(d))
print("\nMEMO:\n" + d["memo"])
