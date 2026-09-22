"""Test questions.
kind: "same" = worded like the document, "para" = synonyms/plurals/paraphrase,
      "none" = unanswerable (the model must not invent an answer).
expect = a fact that must appear in the retrieved text (None for unanswerable).
"""


def S(q, expect):
    return {"q": q, "expect": expect, "kind": "same"}


def P(q, expect):
    return {"q": q, "expect": expect, "kind": "para"}


def U(q):
    return {"q": q, "expect": None, "kind": "none"}


CASES = [
    # ---- Acme Retail
    S("What was Acme's revenue in fiscal 2025?", "4,820"),
    S("What share of Acme's inventory comes from a few suppliers?", "45 percent"),
    S("What was Acme's operating margin in fiscal 2025?", "11.4 percent"),
    S("What was Acme's dividend per share?", "6 rupees"),
    S("How much capital expenditure does Acme plan for fiscal 2026?", "600 crore"),
    P("How did Acme's earnings change year over year?", "412"),
    P("Is Acme reducing its borrowings?", "1,150"),
    P("What could hurt Acme's future sales?", "quick commerce"),
    P("What are Acme's main risks?", "quick commerce"),
    P("How important are physical stores to Acme's sales?", "62 percent"),
    P("Why did Acme's margins get better?", "logistics costs"),
    # ---- Borealis Bank
    S("How much did Borealis Bank's deposits grow?", "14 percent"),
    S("What was Borealis Bank's net interest income in fiscal 2025?", "9,200"),
    S("What is Borealis Bank's capital adequacy ratio?", "16.5 percent"),
    S("How many new branches does Borealis Bank plan?", "250 new branches"),
    P("What happened to Borealis Bank's bad loans?", "2.1 percent"),
    P("How much did Borealis Bank make in earnings last year?", "2,340"),
    P("What dangers does Borealis Bank face from customers not repaying?", "unsecured personal loans"),
    P("Could online security breaches hurt Borealis Bank?", "cyber attacks"),
    # ---- Cygnus Pharma
    S("How much does Cygnus Pharma spend on research?", "480"),
    S("What are Cygnus Pharma's export sales as a share of revenue?", "58 percent"),
    S("What was Cygnus Pharma's net profit in fiscal 2025?", "520 crore"),
    S("How much cash does Cygnus Pharma hold?", "900 crore"),
    P("Does Cygnus Pharma owe money to lenders?", "no long term borrowings"),
    P("What could go wrong with Cygnus Pharma's manufacturing?", "single plant"),
    P("What are Cygnus Pharma's risks?", "single plant"),
    P("How many new medicines did Cygnus Pharma get cleared?", "two new drug approvals"),
    # ---- Meridian Airways
    S("How many passengers did Meridian Airways carry?", "21 million"),
    S("How many aircraft are in Meridian Airways' fleet?", "74 aircraft"),
    S("What share of Meridian Airways' expenses is fuel?", "38 percent"),
    S("What was Meridian Airways' revenue in fiscal 2025?", "7,400"),
    P("Did Meridian Airways make a loss?", "260 crore"),
    P("What are Meridian Airways' risks?", "volatile fuel prices"),
    P("Is Meridian Airways paying down its borrowings?", "5,400"),
    P("When will Meridian Airways stop losing money?", "break even"),
    # ---- unanswerable
    U("What was the CEO's salary?"),
    U("What is Acme's projected revenue for fiscal 2027?"),
    U("How many employees does Cygnus Pharma have?"),
    U("What is Borealis Bank's share price?"),
    U("Who audits Meridian Airways' accounts?"),
    U("What was Acme's revenue in fiscal 2019?"),
]
