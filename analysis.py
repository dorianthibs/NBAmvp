"""Normalisation à 36 minutes, percentiles, forces / faiblesses."""
import pandas as pd

BASE_MIN = 36

# Liste manuelle pour la saison en cours ; les autres saisons -> top 10 auto (EFF)
MVP_CANDIDATES = {
    "2025-26": [
        "Nikola Jokić", "Shai Gilgeous-Alexander", "Luka Dončić",
        "Giannis Antetokounmpo", "Jaylen Brown", "Victor Wembanyama",
        "Jalen Johnson", "Kawhi Leonard", "Donovan Mitchell", "Jalen Brunson",
    ],
}

# colonne : (libellé, plus_haut_est_meilleur)
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


def prepare(df: pd.DataFrame, season: str, min_minutes: float = 20.0) -> pd.DataFrame:
    df = df[df["MIN"] > 0].copy()
    df["coef"] = BASE_MIN / df["MIN"]
    for stat in ["PTS", "REB", "AST", "STL", "BLK", "TOV"]:
        df[f"{stat}_36"] = (df[stat].fillna(0) * df["coef"]).round(1)

    # Seuil de matchs relatif à la longueur de la saison (saisons raccourcies)
    min_gp = max(10, int(0.4 * df["GP"].max()))
    qualified = (df["GP"] >= min_gp) & (df["MIN"] >= min_minutes)
    pool = df[qualified]

    # Candidats MVP : liste manuelle sinon top 10 par efficacité
    cands = MVP_CANDIDATES.get(season)
    if cands is None:
        score = pool["EFF"] if "EFF" in pool else pool["PTS"] + pool["REB"] + pool["AST"]
        cands = pool.loc[score.nlargest(10).index, "PLAYER_NAME"].tolist()
    df["is_candidate"] = df["PLAYER_NAME"].isin(cands)

    for col, (_, higher) in METRICS.items():
        pct = pool[col].rank(pct=True, ascending=higher) * 100
        df[f"{col}_pct"] = pct.reindex(df.index)
    df.attrs["min_gp"] = min_gp
    return df


def strengths_weaknesses(row: pd.Series, n: int = 3):
    """Retourne (3 meilleures colonnes, 3 pires colonnes) selon le percentile."""
    pcts = pd.Series({c: row[f"{c}_pct"] for c in METRICS}).dropna().sort_values(ascending=False)
    return list(pcts.index[:n]), list(pcts.index[-n:][::-1])
