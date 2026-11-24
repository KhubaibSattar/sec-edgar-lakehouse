import pandas as pd
import requests


HEADERS = {"User-Agent": "YourName your.email@example.com"}   # <-- change this

# 0.6

def get_sec_data(cik):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik.zfill(10)}.json"
    
    #################################### REMOVING HEADER ####################################
    resp = requests.get(url, headers=HEADERS, timeout=30)
    # resp = requests.get(url, timeout=30)
    
    resp.raise_for_status()   # a 403 here usually means the User-Agent is missing/bad
    data = resp.json()
    return data

# CIK = "320193"  # Apple. Try 789019 (Microsoft) or 19617 (JPMorgan) next.
COMPANIES = {
    "AAPL": 320193,    # FY ends Sept
    "MSFT": 789019,    # FY ends June
    "WMT":  104169,    # FY ends Jan, split 3:1 in 2024
    "JPM":  19617,     # a bank
    "NVDA": 1045810,   # splits in 2021 and 2024
}

for comp in COMPANIES:
    print( "\n" + "*" * 30 , comp , "*" * 30 )
    # comp = "AAPL"

    # print(COMPANIES[comp])
    # print(str(COMPANIES[comp]).zfill(10))
    cik = str(COMPANIES[comp]).zfill(10)

    print (f"CIK: {cik} | Company: {comp}")

    # url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    # resp = requests.get(url, headers=HEADERS, timeout=30)
    # resp.raise_for_status()   # a 403 here usually means the User-Agent is missing/bad
    # data = resp.json()

    data = get_sec_data(cik)

    # ---------------------------------------------------------------
    # 1. Top level: who is this, and which taxonomies do they use?
    # ---------------------------------------------------------------
    print("=" * 60)
    print("Company:", data["entityName"], "| CIK:", data["cik"])
    print("Top-level keys:", list(data.keys()))
    print("facts :", list(data["facts"].keys()))
    # print("facts items :", data["facts"].items())

    facts = list(data["facts"].keys())

    for taxonomy, concepts in data["facts"].items():
        print(f"  taxonomy '{taxonomy}': {len(concepts)} concepts")

    # ---------------------------------------------------------------
    # 2. Which revenue tag does this company use?
    # ---------------------------------------------------------------

    gaap = data["facts"]["us-gaap"]

    for fact in facts:
        
        print("\n" + "=" * 30 , fact , "=" * 30 )
        
        f = data["facts"][fact]
        # revenue_tags = [c for c in gaap if "Revenue" in c]
        revenue_tags = [c for c in f if "Revenue" in c]
        # print(revenue_tags)
        if len(revenue_tags) > 0 :
            print("\nConcepts with 'Revenue' in the name:")
            for c in revenue_tags:
            # [:10]:
                print("  ", c)
        else:
            print("\nNo Concepts with 'Revenue' in the name.")


# 0.3

# appl_data = get_sec_data(str(COMPANIES["AAPL"]))

# revenue_tags = [c for c in appl_data["facts"]["us-gaap"] if "Revenue" in c]

# for revenue_tag in revenue_tags:
#     print("\n" + "*"*30, revenue_tag , "*"*30 )
    
#     df = pd.DataFrame(appl_data["facts"]["us-gaap"][revenue_tag]["units"]["USD"])
    
#     # print(30*"*")
#     # print(df)
#     # print(30*"+")
#     # print(df.columns.tolist())

#     # df["start"] = pd.to_datetime(df["start"])
#     df["end"] = pd.to_datetime(df["end"])

#     # print(df)
    
#     # df_2023 = df[(df["end"].dt.year == 2023) & (df["start"].dt.year == 2023) ]
#     df_2023 = df[df["end"].dt.year == 2023]
#     # df_2023 = df[df["fy"] == 2023]

#     print(df_2023)
    
#     # df_2023shape = df_2023.shape[0]
#     # print(df_2023shape)