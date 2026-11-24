import time
import pandas as pd
import requests

HEADERS = {"User-Agent": "YourName your.email@example.com"}

COMPANIES = {
    "AAPL": 320193,
    "MSFT": 789019,
    "WMT":  104169,
    "JPM":  19617,
    "NVDA": 1045810,
}

def get_sec_data(cik):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{str(cik).zfill(10)}.json"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()

all_data = {}
for ticker, cik in COMPANIES.items():
    all_data[ticker] = get_sec_data(cik)
    time.sleep(0.2)            # be polite to the SEC: max 10 requests/second

print(all_data.keys())
# print(all_data.items())


taxonomies = set()
for ticker, data in all_data.items():
    taxonomies.update(data["facts"].keys())     # adds dei, us-gaap, ... without repeats

print(taxonomies)




'''for fact in taxonomies:
    # tax = "us-gaap
    print(f"\n {'#' * 30} {fact} {'#' * 30}")
    tax = fact
    columns = {} 
    # []

    for ticker, data in all_data.items():
        if tax in data["facts"]:
            concepts = sorted(data["facts"][tax].keys())
            columns[ticker] = [tax] + concepts
        else:
            columns[ticker] = [] #[tax] + ["N/A"]
    
    for ticker, cols in columns.items():
        print(f"\n {'*' * 30} {ticker} {'*' * 30}")
        print(f"{ticker}: {len(cols)} columns")
        # print(cols[:5], "...", cols[-5:])

    # print(columns)
    df = pd.DataFrame({t: pd.Series(c, dtype=object) for t, c in columns.items()})
    df.to_csv(f"{tax}_concepts.csv", index=False)
    print(f"saved {tax}_concepts.csv")'''


################## creates a dictionary of concepts for each taxonomy, with the tickers that have that concept
# # concepts = set()
# ticker_concepts = {}

# for fact in taxonomies:

#     f = fact
#     for ticker, data in all_data.items():
#         if f in data["facts"]:
#             # ticker_concepts[fact] = ticker_concepts[fact] + set(sorted(data["facts"][f].keys()))
#             # setdeafult works as : if the key doesnt exist set it to the default value (here an empty set) and then update it with the new values
#             ticker_concepts.setdefault(fact, set()).update(data["facts"][f].keys())

#     # print(f"\n {'#' * 30} {fact} {'#' * 30}")
#     # print(ticker_concepts)

# # print(ticker_concepts)


################### generate a CSV for each taxonomy, with rows = concepts, columns = tickers, and values = 1 if the concept exists for that ticker, else 0
# concepts_ticker_flags = {}
# for fact, concepts in ticker_concepts.items(): # .items()

#     ## my try (have issues)
#     # for t, d in all_data.items():
#     #     if fact in d["facts"]:
#     #         for c in concepts:
#     #             flag = list()
#     #             if c '''not''' in d["facts"][fact]:
#     #                 # print(f"{t} does not have {c} in {fact}")
                    
#     #                 concepts_ticker_flags[c] = flag.append(1)
#     #             else:
#     #                 # print(f"{t} has {c} in {fact}")
#     #                 concepts_ticker_flags[c] = flag.append(0)

#     ## working code
    
#     concepts_ticker_flags[fact] = {}
#     for t,d in all_data.items():
#         ticker_tags = d["facts"].get(fact, {})

#         concepts_ticker_flags[fact][t] = {}

#         for c in concepts:
#             # claude suggested code :
#             # concepts_ticker_flags[fact][t][c] = 1 if c in ticker_tags else 0
#             if c not in ticker_tags:
#                 concepts_ticker_flags[fact][t][c] = 0
#             else:
#                 concepts_ticker_flags[fact][t][c] = 1

# for tax, table in concepts_ticker_flags.items():
#     df = pd.DataFrame(table).sort_index()      # columns = tickers, rows = concepts
#     df.to_csv(f"{tax}_compare.csv", index_label="concept")
#     print(tax, df.shape)

df = pd.read_csv("us-gaap_compare.csv", index_col="concept")

common = df[df.all(axis=1)]       # keep rows where every ticker is 1
print(common.shape)
common.to_csv("us-gaap_common.csv")

common = set(common.index) 
# print(type(common), len(common))
# print(list(common)[:5])


def last_year(data, tax, concept):
    units = data["facts"].get(tax, {}).get(concept, {}).get("units", {})
    ends = [f["end"] for rows in units.values() for f in rows]
    return int(max(ends)[:4]) if ends else None

recent = {
    ticker: {c: last_year(data, "us-gaap", c) for c in common}
    for ticker, data in all_data.items()
}
recent_df = pd.DataFrame(recent).sort_index()
print(recent_df[recent_df.min(axis=1) >= 2024])   # every company used it in 2024 or later


passed = recent_df[recent_df.min(axis=1) >= 2024]
print([c for c in passed.index if "Revenue" in c])
print([c for c in passed.index if "NetIncome" in c or "OperatingActivities" in c])