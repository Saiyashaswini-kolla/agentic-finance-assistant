"""Questions about the IMF Quarterly Report on IMF Finances (quarter ended January 2026).
Written from the PDF text alone, before running the app on it.
expect = a short exact snippet from the report text; None = the report does not answer it.
answer = words/numbers a correct memo must contain (any one of them).
"""
REAL_CASES = [
    # ---- worded like the report
    {"q": "What was the SDR interest rate for the nine months ended January 31, 2026?",
     "expect": "2.842 percent", "answer": ["2.842"], "kind": "same"},
    {"q": "What was the rate of charge for the nine months ended January 31, 2026?",
     "expect": "3.442 percent", "answer": ["3.442"], "kind": "same"},
    {"q": "What was the exchange rate of the SDR to the US dollar at January 31, 2026?",
     "expect": "SDR 1 = US$1.38187", "answer": ["1.38187"], "kind": "same"},
    {"q": "How many active arrangements did the General Resources Account have at January 31, 2026?",
     "expect": "Number of active arrangements 1/ 21 26", "answer": ["21"], "kind": "same"},
    {"q": "What were total assets of the General Department at January 31, 2026, in millions of SDRs?",
     "expect": "Total assets 517,381 516,887", "answer": ["517,381"], "kind": "same"},
    {"q": "What were quota subscriptions at January 31, 2026?",
     "expect": "Quota subscriptions 476,372 476,372", "answer": ["476,372"], "kind": "same"},
    {"q": "What were the commitments under the Extended Fund Facility at January 31, 2026?",
     "expect": "Extended Fund Facility (EFF) 52,097 51,846", "answer": ["52,097"], "kind": "same"},
    {"q": "Which accounting standards is the report prepared under?",
     "expect": "International Financial Reporting Standards", "answer": ["international financial reporting standards", "ifrs"], "kind": "same"},
    # ---- reworded (paraphrase, synonyms)
    {"q": "Where do the proceeds from the IMF's gold sales go?",
     "expect": "profits from the sale of gold held by the IMF", "answer": ["special disbursement account", "sda"], "kind": "para"},
    {"q": "Why does the IMF move money from the Investment Account to the GRA each year?",
     "expect": "cover administrative expenses", "answer": ["administrative expenses"], "kind": "para"},
    {"q": "In what ways can the IMF make its resources available to a country in balance of payments trouble?",
     "expect": "financing arrangement or in the form of outright purchases", "answer": ["outright purchases", "financing arrangement"], "kind": "para"},
    {"q": "What is the name of the endowment part of the Investment Account?",
     "expect": "Endowment Subaccount (EA)", "answer": ["endowment subaccount"], "kind": "para"},
    {"q": "Which country had the largest commitments under GRA arrangements?",
     "expect": "Mexico, 17,825, 21%", "answer": ["mexico"], "kind": "para"},
    {"q": "Are expected credit loss assessments done in the quarterly reports?",
     "expect": "are not included in the quarterly financial reports", "answer": ["not included"], "kind": "para"},
    # ---- not in the report
    {"q": "Who is the Managing Director of the IMF?", "expect": None, "kind": "none"},
    {"q": "How many employees does the IMF have?", "expect": None, "kind": "none"},
    {"q": "What was the price of gold per ounce at January 31, 2026?", "expect": None, "kind": "none"},
    {"q": "What is the forecast for global GDP growth?", "expect": None, "kind": "none"},
    {"q": "Where is the IMF headquartered?", "expect": None, "kind": "none"},
]
