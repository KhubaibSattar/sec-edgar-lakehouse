# CLaude's Response:

Your layout works: one file per taxonomy, one column per ticker, the taxonomy name on the first row under the tickers, and then that ticker's concepts. I tested the logic below on sample files shaped like the real data, and it produces exactly that layout.

Build it one step at a time, and run each step before moving to the next.

## Step 1: Fetch each company once and keep the data

You'll need each company's JSON several times, so download it once and store it in a dictionary keyed by ticker.

```python
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
```

**Check:** it should print the 5 tickers. (A small fix to your example: Apple's ticker is `AAPL`, not `APPL`.)

## Step 2: Find every taxonomy across all 5 companies

You want one file per taxonomy, including a taxonomy that only one company uses. So collect them all into a **set**, which keeps each name only once.

```python
taxonomies = set()
for ticker, data in all_data.items():
    taxonomies.update(data["facts"].keys())     # adds dei, us-gaap, ... without repeats

print(taxonomies)
```

**Check:** you'll probably see `{'dei', 'us-gaap'}`. If one company also has something like `srt` or `ifrs-full`, it shows up here, and it will get its own file.

## Step 3: Build one taxonomy's columns

Start with just `us-gaap` so you can see what's happening. Each ticker's column is a list: the taxonomy name first, then its concept names in alphabetical order.

```python
tax = "us-gaap"
columns = {}

for ticker, data in all_data.items():
    if tax in data["facts"]:
        concepts = sorted(data["facts"][tax].keys())    # only the names, nothing below them
        columns[ticker] = [tax] + concepts
    else:
        columns[ticker] = []                            # company doesn't use this taxonomy

for ticker, col in columns.items():
    print(ticker, len(col))
```

`.keys()` gives only the concept names, so units and facts are left out automatically, as you wanted.

**Check:** each ticker shows a different count. The lists have **different lengths**, which matters in the next step.

## Step 4: Turn it into a table and save it

`pd.DataFrame` refuses lists of different lengths. Wrapping each list in `pd.Series` fixes that: shorter columns get filled with blanks at the bottom.

```python
df = pd.DataFrame({ticker: pd.Series(col, dtype=object) for ticker, col in columns.items()})
print(df.head())

df.to_csv(f"{tax}_concepts.csv", index=False)
```

`index=False` stops pandas from adding a 0, 1, 2… column at the front.

**Check:** open the CSV. Row 1 has the tickers, row 2 has `us-gaap` in every column, and the concepts follow.

## Step 5: Loop over every taxonomy

Once Step 4 works for `us-gaap`, wrap Steps 3–4 in a loop:

```python
for tax in sorted(taxonomies):
    columns = {}
    for ticker, data in all_data.items():
        if tax in data["facts"]:
            columns[ticker] = [tax] + sorted(data["facts"][tax].keys())
        else:
            columns[ticker] = []

    df = pd.DataFrame({t: pd.Series(c, dtype=object) for t, c in columns.items()})
    df.to_csv(f"{tax}_concepts.csv", index=False)
    print(f"saved {tax}_concepts.csv")
```

If 4 companies have 4 taxonomies and one company has 5, you get 5 files. In the extra file, the 4 companies without it have empty columns, so you can see at a glance who's missing it.

## One thing to expect

In this layout, **rows don't line up across companies**. Row 50 might be `Assets` for Apple but `AccruedLiabilities` for JPMorgan, because each column has its own list. That's fine for scanning each company's tags.

To *compare* companies, a second layout often works better: one row per concept, and a ✓ under each company that uses it. Once you've built this version, try building that one yourself. Hint: start from a `set` of all concepts in the taxonomy, then check `concept in data["facts"][tax]` for each ticker.


# Code modification and Claudes suggestions

Your first loop is right: it builds the full set of concepts for each taxonomy. The second loop is where it goes wrong, for one main reason.

## Why you're stuck

To answer "does this ticker have this concept in this taxonomy?", you have **three things to keep track of**: the taxonomy, the ticker and the concept. Your dictionary only stores one of them:

```python
concepts_ticker_flags[c] = ...     # key is only the concept
```

So the taxonomy and the ticker get lost, and each ticker overwrites the one before it.

**The fix is to nest dictionaries, one level for each thing you need to track:**

```python
flags[taxonomy][ticker][concept] = 1 or 0
```

For example:

```python
flags = {
    "us-gaap": {
        "AAPL": {"Assets": 1, "DeferredRevenue": 1, ...},
        "JPM":  {"Assets": 1, "DeferredRevenue": 0, ...},
    },
    "dei": { ... },
}
```

## The other bugs in your second loop

1. **`flag.append(1)` returns `None`.** `.append()` changes the list but returns nothing, so you were storing `None`. You don't need a list at all; just store `1` or `0`.
2. **`flag = list()` is inside the loop**, so it's reset to empty for every concept.
3. **The 1 and 0 are swapped.** `not in` gave 1, but you want 1 to mean "has it".
4. **`if fact in d["facts"]` skips companies that don't have the taxonomy**, so they'd get no row instead of 0s.
5. A naming tip: what you call `fact` is really a **taxonomy** (us-gaap, dei). In EDGAR, a "fact" is one reported value. Calling it `tax` will make your code easier to follow.

## The fixed second part

Keep your first loop as it is. Replace the second one with this:

```python
flags = {}

for tax, concepts in ticker_concepts.items():
    flags[tax] = {}

    for ticker, data in all_data.items():
        ticker_tags = data["facts"].get(tax, {})    # this ticker's concepts, or {} if it lacks the taxonomy
        flags[tax][ticker] = {}

        for c in concepts:
            flags[tax][ticker][c] = 1 if c in ticker_tags else 0
```

Two new pieces:
- **`.get(tax, {})`** means "give me `data["facts"][tax]`, or an empty dict if it doesn't exist". A company without the taxonomy then gets 0 for every concept, without needing an `if`.
- **`1 if c in ticker_tags else 0`** is a one-line if/else.

## Turning it into your table

This part is simple, because pandas understands nested dicts directly. **Outer keys become columns and inner keys become rows**, and pandas lines up the rows by concept name for you:

```python
for tax, table in flags.items():
    df = pd.DataFrame(table).sort_index()      # columns = tickers, rows = concepts
    df.to_csv(f"{tax}_compare.csv", index_label="concept")
    print(tax, df.shape)
```

Result:

```
concept             AAPL  MSFT  WMT  JPM  NVDA
Assets                 1     1    1    1     1
DeferredRevenue...     1     1    0    0     1
```

`index_label="concept"` gives the first column a header in the CSV.

## One extra line that helps with concept_map

Add a count of how many companies use each concept:

```python
df["companies"] = df.sum(axis=1)       # axis=1 = add across the row
df = df.sort_values("companies", ascending=False)
```

The tags at the top, used by all 5, are your safe priority-1 picks. The tags only 1–2 companies use, like JPMorgan's bank-specific ones, are your fallbacks.