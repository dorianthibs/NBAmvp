"""Récupération des stats NBA par saison (1979-80 -> 2025-26) depuis Basketball-Reference.
Chaque saison est sauvegardée dans data/season_XXXX-XX.csv (cache)."""
import time
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

FIRST_START_YEAR = 1999   # première saison affichée : 1999-00
LAST_START_YEAR = 2025    # saison 2025-26
DATA_DIR = Path(__file__).parent / "data"
URL = "https://www.basketball-reference.com/leagues/NBA_{end_year}_per_game.html"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
}


def season_label(start_year: int) -> str:
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def all_seasons() -> list[str]:
    """['2025-26', '2024-25', ..., '1979-80']"""
    return [season_label(y) for y in range(LAST_START_YEAR, FIRST_START_YEAR - 1, -1)]


def _clean(raw: pd.DataFrame) -> pd.DataFrame:
    """Transforme le tableau Basketball-Reference au format utilisé par l'appli."""
    df = raw[raw["Player"] != "Player"].copy()          # lignes d'en-tête répétées
    df = df.drop_duplicates(subset="Player", keep="first")  # 1re ligne = total si transfert
    team_col = "Team" if "Team" in df.columns else "Tm"
    df["Player"] = df["Player"].str.replace("*", "", regex=False).str.strip()

    ren = {"Player": "PLAYER_NAME", team_col: "TEAM_ABBREVIATION", "G": "GP", "MP": "MIN",
           "FG": "FGM", "FT": "FTM", "FG%": "FG_PCT", "3P%": "FG3_PCT", "FT%": "FT_PCT",
           "TRB": "REB", "AST": "AST", "STL": "STL", "BLK": "BLK", "TOV": "TOV",
           "PTS": "PTS", "FGA": "FGA", "FTA": "FTA"}
    df = df.rename(columns=ren)[list(dict.fromkeys(ren.values()))]
    for c in df.columns.drop(["PLAYER_NAME", "TEAM_ABBREVIATION"]):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["GP", "MIN", "PTS"])

    denom = 2 * (df["FGA"] + 0.44 * df["FTA"])
    df["TS_PCT"] = df["PTS"] / denom.where(denom > 0)
    df["EFF"] = (df["PTS"] + df["REB"] + df["AST"] + df["STL"] + df["BLK"]
                 - (df["FGA"] - df["FGM"]) - (df["FTA"] - df["FTM"]) - df["TOV"])
    return df.reset_index(drop=True)


def _fetch(season: str) -> pd.DataFrame:
    end_year = int(season[:4]) + 1
    resp = requests.get(URL.format(end_year=end_year), headers=HEADERS, timeout=60)
    resp.raise_for_status()
    raw = pd.read_html(StringIO(resp.text), match="Player", attrs={"id": "per_game_stats"})[0]
    return _clean(raw)


def load_data(season: str, force: bool = False) -> pd.DataFrame:
    """Lit le cache CSV de la saison s'il existe, sinon télécharge."""
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
    # Télécharge TOUTES les saisons une fois (pause entre chaque pour ne pas être bloqué)
    for s in all_seasons():
        if (DATA_DIR / f"season_{s}.csv").exists():
            continue
        print("Téléchargement", s, flush=True)
        try:
            load_data(s)
        except Exception as e:
            print("   échec :", e)
        time.sleep(5)
    print("Terminé.")
