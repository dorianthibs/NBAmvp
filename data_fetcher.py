"""Récupération des données NBA (saison 2025-26) + cache local CSV."""
from pathlib import Path
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats

SEASON = "2025-26"
CACHE = Path("data") / "players_2025_26.csv"

MVP_CANDIDATES = [
    "Nikola Jokić", "Shai Gilgeous-Alexander", "Luka Dončić",
    "Giannis Antetokounmpo", "Jaylen Brown", "Victor Wembanyama",
    "Jalen Johnson", "Kawhi Leonard", "Donovan Mitchell", "Jalen Brunson",
]


def _fetch(measure: str) -> pd.DataFrame:
    # Un seul appel par type de stats pour TOUS les joueurs (pas 10 appels)
    return leaguedashplayerstats.LeagueDashPlayerStats(
        season=SEASON,
        per_mode_detailed="PerGame",
        measure_type_detailed_defense=measure,
        timeout=60,
    ).get_data_frames()[0]


def load_data(force: bool = False) -> pd.DataFrame:
    """Lit le cache CSV s'il existe, sinon interroge l'API NBA."""
    if CACHE.exists() and not force:
        return pd.read_csv(CACHE)
    try:
        base = _fetch("Base")
        adv = _fetch("Advanced")[["PLAYER_ID", "TS_PCT", "USG_PCT", "NET_RATING", "PIE"]]
        df = base.merge(adv, on="PLAYER_ID", how="left")
        CACHE.parent.mkdir(exist_ok=True)
        df.to_csv(CACHE, index=False)
        return df
    except Exception:
        if CACHE.exists():       # API indisponible -> on retombe sur le cache
            return pd.read_csv(CACHE)
        raise
