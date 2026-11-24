# Progress so far: SEC EDGAR XBRL exploration

## Goal

Work out what the SEC EDGAR `companyfacts` JSON looks like, and find which XBRL concepts (tags) can be used to compare companies against each other. This feeds a later `concept_map` and the silver layer of the pipeline.

## Data source

- Endpoint: `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json` (the CIK is zero-padded to 10 digits).
- The SEC requires a `User-Agent` header with a name and email. Without one it returns **403**. The scripts still use the placeholder `"YourName your.email@example.com"`.
- Rate limit is 10 requests/second. `get_csv.py` waits 0.2 s between requests.

Companies used. Each was picked because it has a different quirk:

| Ticker | CIK | Why it's useful |
|---|---|---|
| AAPL | 320193 | Fiscal year ends in September |
| MSFT | 789019 | Fiscal year ends in June |
| WMT | 104169 | Fiscal year ends in January; 3:1 stock split in 2024 |
| JPM | 19617 | A bank, so it uses different tags |
| NVDA | 1045810 | Stock splits in 2021 and 2024 |

## Scripts, in the order they were written

### 1. `sec_edgar.py`: explore one company (JPMorgan)
Pulls one company's JSON and inspects its structure step by step:
- Top-level keys, the taxonomies used (`us-gaap`, `dei`, ...) and how many concepts each has.
- Concepts with "Revenue" in the name.
- Flattens a single concept (`NetIncomeLoss`) into a DataFrame with the columns `start, end, val, form, fy, fp, filed, frame`. This flattened table is what a "silver" row looks like.
- **Duplicates:** the same `start`/`end` period is reported in many filings.
- **Instant vs duration:** balance-sheet items like `Assets` have no `start` column.
- Total number of facts across all concepts.

### 2. `edgar_testing.py`: loop over all 5 companies
- Moves the fetch into `get_sec_data(cik)`.
- For each company, prints its taxonomies with concept counts, then the "Revenue" concepts in each taxonomy.
- A commented-out block filters Apple's revenue facts to periods ending in 2023.

### 3. `get_csv.py`: compare companies and write CSVs
- Fetches all 5 companies once into `all_data` (a dict keyed by ticker) and collects the set of all taxonomies.
- **Commented out, already run:** the two steps that wrote the `*_concepts.csv` and `*_compare.csv` files (see below).
- **Currently active:**
  1. Reads `us-gaap_compare.csv` and keeps the concepts that all 5 companies use, then writes them to `us-gaap_common.csv`.
  2. `last_year(data, tax, concept)` returns the latest year in which a company reported a concept.
  3. Keeps only the common concepts that **every** company still reported in 2024 or later.
  4. Prints the candidates among those for revenue, net income and operating cash flow.

## Output CSVs

There are two layouts, one file per taxonomy:

- **`<tax>_concepts.csv`**: one column per ticker. Row 1 holds the taxonomy name, followed by that company's concepts in alphabetical order. Rows don't line up across companies. Use it to scan one company's tags.
- **`<tax>_compare.csv`**: one row per concept and one column per ticker. A cell is `1` if the company uses the concept and `0` if it doesn't. Use it to compare companies.
- **`us-gaap_common.csv`**: the us-gaap concepts used by all 5 companies.

Results from the compare files:

| Taxonomy | Concepts (all companies) | Used by all 5 | Notes |
|---|---|---|---|
| us-gaap | 1,740 | 97 | AAPL 512, MSFT 562, WMT 478, JPM 918, NVDA 627. 1,068 concepts are used by only one company; 571 of those are JPM's alone. |
| dei | 3 | 2 | `EntityListingParValuePerShare` is MSFT only |
| ecd | 7 | 0 | Every company uses these except AAPL (executive compensation disclosures) |
| ffd | 6 | 6 | Filing-fee tags, shared by everyone |
| invest | 1 | 0 | `DerivativeNotionalAmount`: WMT, JPM, NVDA |
| srt | 2 | 0 | JPM uses both; NVDA uses `StockRepurchaseProgramAuthorizedAmount1` |

## Notes and learning docs

- **`how to compate companies.md`**: Claude's step-by-step guide for building the per-taxonomy CSVs. It also reviews the compare code: use a nested dict `flags[taxonomy][ticker][concept]`, `.append()` returns `None`, the 1/0 values were swapped, use `.get(tax, {})` for companies that lack a taxonomy, and call `tax` a taxonomy rather than a "fact".
- **`sql_to_pandas.md`**: a cheat sheet that maps SQL `WHERE` filtering to pandas (`df[cond]`, `&`/`|`/`~`, `.isin`, `.str.contains`, `.loc`, `.query`), with examples on the compare CSV.

## Key findings

1. **Companies use different tags for the same thing**, revenue in particular. A single tag won't cover all companies, so each metric needs a priority list of tags.
2. **Only 97 us-gaap concepts are shared by all 5 companies.** Fewer still were reported recently (2024+) by all of them.
3. **JPM is the outlier.** As a bank it uses far more tags, and many of them are bank-specific.
4. **The same period is reported many times**, because later filings (10-K, 10-Q) repeat earlier numbers. The data needs deduplication.
5. **Facts come in two kinds.** Instant facts (balance sheet) have only `end`. Duration facts (income and cash-flow statements) have both `start` and `end`.

## Next steps

- [ ] Turn the 2024+ common-concept results into a `concept_map`: a priority-1 tag per metric, with fallbacks such as JPM-specific tags.
- [ ] Decide on deduplication, for example keeping the latest `filed` value per concept and period.
- [ ] Handle fiscal years that end in different months (use `start`/`end`, not just `fy`) and stock splits for per-share and share-count values.
- [ ] Replace the placeholder `User-Agent` with a real one.
- [ ] Clean up the commented-out code in `get_csv.py`, or split it into separate scripts.
