
import pandas as pd
from data_fetcher import MVP_CANDIDATES

BASE_MIN = 36

METRICS = {
    "PTS_36": ("Points /36", True),
    "REB_36": ("Rebonds /36", True),
    "AST_36": ("Passes /36", True),
    "STL_36": ("Interceptions /36", True),
    "BLK_36": ("Contres /36", True),
    "TOV_36": ("Balles perdues /36", False),
    "FG_PCT": ("% aux tirs", True),
    "FG3_PCT": ("% à 3 pts", True),
    "FT_PCT": ("% lancers francs", True),
    "TS_PCT": ("True Shooting %", True),
}


def prepare(df: pd.DataFrame, min_gp: int = 20, min_minutes: float = 20.0) -> pd.DataFrame:
    df = df.copy()
    df["coef"] = BASE_MIN / df["MIN"]
    for stat in ["PTS", "REB", "AST", "STL", "BLK", "TOV"]:
        df[f"{stat}_36"] = (df[stat] * df["coef"]).round(1)
    df["is_candidate"] = df["PLAYER_NAME"].isin(MVP_CANDIDATES)
    
    pool = df[(df["GP"] >= min_gp) & (df["MIN"] >= min_minutes)]
    for col, (_, higher) in METRICS.items():
        pct = pool[col].rank(pct=True, ascending=higher) * 100
        df[f"{col}_pct"] = pct.reindex(df.index)
    return df


def strengths_weaknesses(row: pd.Series, n: int = 3):
    pcts = pd.Series({c: row[f"{c}_pct"] for c in METRICS}).dropna().sort_values(ascending=False)
    return list(pcts.index[:n]), list(pcts.index[-n:][::-1])
