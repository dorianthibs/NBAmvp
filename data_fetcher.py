"""Récupération des données NBA par saison (1979-80 -> 2025-26) + cache CSV."""
import time
from pathlib import Path
import pandas as pd
from nba_api.stats.endpoints import leagueleaders

FIRST_START_YEAR = 1999   # saison 1979-80 : arrivée de la ligne à 3 points
LAST_START_YEAR = 2025    # saison 2025-26
DATA_DIR = Path("data")


def season_label(start_year: int) -> str:
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def all_seasons() -> list[str]:
    """['2025-26', '2024-25', ..., '1979-80']"""
    return [season_label(y) for y in range(LAST_START_YEAR, FIRST_START_YEAR - 1, -1)]


def _fetch(season: str) -> pd.DataFrame:
    df = leagueleaders.LeagueLeaders(
        league_id="00", per_mode48="PerGame", scope="S", season=season,
        season_type_all_star="Regular Season", stat_category_abbreviation="PTS",
        timeout=60,
    ).get_data_frames()[0]
    df = df.rename(columns={"PLAYER": "PLAYER_NAME", "TEAM": "TEAM_ABBREVIATION"})
    if "TEAM_ABBREVIATION" not in df.columns:
        df["TEAM_ABBREVIATION"] = ""
    # True Shooting % recalculé (disponible pour toutes les saisons)
    denom = 2 * (df["FGA"] + 0.44 * df["FTA"])
    df["TS_PCT"] = df["PTS"] / denom.where(denom > 0)
    return df


def load_data(season: str, force: bool = False) -> pd.DataFrame:
    """Lit le cache CSV de la saison s'il existe, sinon interroge l'API NBA."""
    path = DATA_DIR / f"season_{season}.csv"
    if path.exists() and not force:
        return pd.read_csv(path)
    try:
        df = _fetch(season)
        DATA_DIR.mkdir(exist_ok=True)
        df.to_csv(path, index=False)
        return df
    except Exception:
        if path.exists():
            return pd.read_csv(path)
        raise


if __name__ == "__main__":
    # Télécharge TOUTES les saisons une fois (utile avant de publier en ligne)
    for s in all_seasons():
        if not (DATA_DIR / f"season_{s}.csv").exists():
            print("Téléchargement", s)
            load_data(s)
            time.sleep(1)   # on ménage l'API
    print("Terminé.")
