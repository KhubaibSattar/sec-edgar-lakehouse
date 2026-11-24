You did spot it: you noticed the all-0 rows were impossible. Finding the line that causes a symptom gets easier with practice. Noticing the symptom is the harder skill.

## The WHERE template

```python
df[ condition ]
```

The condition is a column of True/False values, one per row. pandas keeps the rows where it's True.

```sql
SELECT * FROM df WHERE AAPL = 1
```
```python
df[df["AAPL"] == 1]
```

## The main pieces, from SQL to pandas

| SQL | pandas |
|---|---|
| `WHERE AAPL = 1` | `df[df["AAPL"] == 1]` |
| `WHERE AAPL <> 1` | `df[df["AAPL"] != 1]` |
| `WHERE a = 1 AND b = 0` | `df[(df["a"] == 1) & (df["b"] == 0)]` |
| `WHERE a = 1 OR b = 1` | `df[(df["a"] == 1) \| (df["b"] == 1)]` |
| `WHERE NOT (a = 1)` | `df[~(df["a"] == 1)]` |
| `WHERE concept IN ('Assets', 'Revenues')` | `df[df["concept"].isin(["Assets", "Revenues"])]` |
| `WHERE concept LIKE '%Revenue%'` | `df[df["concept"].str.contains("Revenue")]` |
| `WHERE concept LIKE 'Revenue%'` | `df[df["concept"].str.startswith("Revenue")]` |
| `WHERE val BETWEEN 10 AND 20` | `df[df["val"].between(10, 20)]` |
| `WHERE start IS NULL` | `df[df["start"].isna()]` |
| `WHERE start IS NOT NULL` | `df[df["start"].notna()]` |

**The three rules that trip up SQL people:**
1. Use `&`, `|` and `~`, **not** `and`, `or` and `not`. Python's words don't work on whole columns.
2. **Wrap each condition in brackets** when you combine them: `(a) & (b)`. Without the brackets you get a confusing error.
3. Use `==` to compare. A single `=` is assignment.

## SELECT columns + WHERE together: `.loc`

```sql
SELECT AAPL, JPM FROM df WHERE JPM = 1
```
```python
df.loc[df["JPM"] == 1, ["AAPL", "JPM"]]
#      ^ rows (WHERE)   ^ columns (SELECT)
```

## The SQL-looking option: `.query()`

If you prefer something that reads like SQL, use `.query()`:

```python
df.query("AAPL == 1 and JPM == 0")
df.query("concept in ['Assets', 'Revenues']")
```

Inside `.query()`, the words `and`, `or` and `not` *do* work. It's nice for quick exploration, but learn the bracket style too, because that's what most code you'll read uses.

## Try it on your compare CSV

```python
df = pd.read_csv("us-gaap_compare.csv")

# concepts every company uses (good priority-1 candidates)
df[(df["AAPL"] == 1) & (df["MSFT"] == 1) & (df["WMT"] == 1) & (df["JPM"] == 1) & (df["NVDA"] == 1)]

# concepts only JPM uses (bank-specific tags)
df[(df["JPM"] == 1) & (df[["AAPL", "MSFT", "WMT", "NVDA"]].sum(axis=1) == 0)]

# revenue-related tags and who uses them
df[df["concept"].str.contains("Revenue")]
```

When you want the next step, ask me for GROUP BY, JOIN and ORDER BY in the same format.