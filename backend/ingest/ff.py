from __future__ import annotations

import logging

import pandas as pd
from pandas_datareader import data as pdr

log = logging.getLogger(__name__)

FIVE_F_DATASET = "F-F_Research_Data_5_Factors_2x3_daily"
MOM_DATASET = "F-F_Momentum_Factor_daily"


def fetch_factors(start: str, end: str) -> pd.DataFrame:
    """Fetch Ken French 5-factor + momentum daily series via pandas-datareader.

    Returns a long DataFrame with columns
    [date, mkt_rf, smb, hml, rmw, cma, mom, rf] — values are decimal returns
    (source is in percent, we divide by 100).
    """
    five = pdr.DataReader(FIVE_F_DATASET, "famafrench", start, end)[0]
    mom = pdr.DataReader(MOM_DATASET, "famafrench", start, end)[0]

    five = five.rename(
        columns={
            "Mkt-RF": "mkt_rf",
            "SMB": "smb",
            "HML": "hml",
            "RMW": "rmw",
            "CMA": "cma",
            "RF": "rf",
        }
    )
    mom = mom.rename(columns={mom.columns[0]: "mom"})  # column name has stray whitespace

    df = five.join(mom, how="outer")
    df = df.reset_index().rename(columns={df.index.name or "Date": "date"})
    if "Date" in df.columns:
        df = df.rename(columns={"Date": "date"})

    # Ken French returns percentages; convert to decimal.
    for col in ("mkt_rf", "smb", "hml", "rmw", "cma", "mom", "rf"):
        if col in df.columns:
            df[col] = df[col] / 100.0

    df["date"] = pd.to_datetime(df["date"]).dt.date
    cols = ["date", "mkt_rf", "smb", "hml", "rmw", "cma", "mom", "rf"]
    for c in cols:
        if c not in df.columns:
            df[c] = None
    return df[cols].sort_values("date").reset_index(drop=True)
