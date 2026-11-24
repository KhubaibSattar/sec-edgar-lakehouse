"""
EDGAR XBRL explorer: pull one company's facts and look at the shape of the data.

Run:  pip install requests pandas
      python edgar_explore.py
(Also works pasted into a Databricks notebook cell.)
"""
import requests
import pandas as pd

# SEC requires a User-Agent with your name + email, or it returns 403.
HEADERS = {"User-Agent": "YourName your.email@example.com"}   # <-- change this

# "320193"  # Apple. Try 789019 (Microsoft) or 19617 (JPMorgan) next.
CIK = "19617"  # JPMorgan Chase

url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK.zfill(10)}.json"
resp = requests.get(url, headers=HEADERS, timeout=30)
resp.raise_for_status()   # a 403 here usually means the User-Agent is missing/bad
data = resp.json()

# ---------------------------------------------------------------
# 0. Raw JSON: what does the SEC return?
# ---------------------------------------------------------------

print(f"URL: {url}  | Status: {resp.status_code} | Size: {len(resp.content):,} bytes")
# print("=" * 60)
# print(data)


# ---------------------------------------------------------------
# 1. Top level: who is this, and which taxonomies do they use?
# ---------------------------------------------------------------
print("=" * 60)
print("Company:", data["entityName"], "| CIK:", data["cik"])
print("Top-level keys:", list(data.keys()))
for taxonomy, concepts in data["facts"].items():
    print(f"  taxonomy '{taxonomy}': {len(concepts)} concepts")

# ---------------------------------------------------------------
# 2. Which revenue tag does this company use?
# ---------------------------------------------------------------
gaap = data["facts"]["us-gaap"]
revenue_tags = [c for c in gaap if "Revenue" in c]
print("\nConcepts with 'Revenue' in the name:")
for c in revenue_tags[:10]:
    print("  ", c)

# ---------------------------------------------------------------
# 3. Flatten ONE concept into a table: this is what "silver" looks like
# ---------------------------------------------------------------
concept = "NetIncomeLoss"
info = gaap[concept]
print(f"\n{concept}: {info['label']}")
print("Units available:", list(info["units"].keys()))

df = pd.DataFrame(info["units"]["USD"])
print(f"Rows: {len(df)}")
print("Columns:", list(df.columns))
print(df[["start", "end", "val", "form", "fy", "fp", "filed", "frame"]].tail(10).to_string())

# ---------------------------------------------------------------
# 4. Duplicates: same period reported in many filings
# ---------------------------------------------------------------
dupes = df.groupby(["start", "end"]).size().sort_values(ascending=False)
print("\nHow many filings report the same period (top 5):")
print(dupes.head().to_string())

# ---------------------------------------------------------------
# 5. Instant vs duration: balance sheet items have no 'start'
# ---------------------------------------------------------------
assets = pd.DataFrame(gaap["Assets"]["units"]["USD"])
print("\nAssets (instant) columns:", list(assets.columns), " <- no 'start'")
print(assets[["end", "val", "form", "filed"]].tail(3).to_string())

# ---------------------------------------------------------------
# 6. Total size: count every fact across all concepts
# ---------------------------------------------------------------
total = sum(
    len(rows)
    for tax in data["facts"].values()
    for c in tax.values()
    for rows in c["units"].values()
)
print(f"\nTotal facts for {data['entityName']}: {total:,}")