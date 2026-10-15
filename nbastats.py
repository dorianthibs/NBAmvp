"""Lancer avec :  streamlit run app.py"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_fetcher import all_seasons, load_data
from analysis import BASE_MIN, METRICS, prepare, strengths_weaknesses

st.set_page_config(page_title="NBA MVP Race 2026", layout="wide")

GREEN, RED, GREY, ORANGE = "#2e9e5b", "#d64545", "#9aa3ad", "#f58426"

@st.cache_data(ttl=3600, show_spinner="Chargement des données NBA…")
def get_data(season: str) -> pd.DataFrame:
    return prepare(load_data(season), season)


st.sidebar.title("NBA MVP Race")
st.sidebar.caption(f"Saison {SEASON} · stats ramenées à {BASE_MIN} min")
SEASON = st.sidebar.selectbox("📅 Saison", all_seasons(), index=0)
st.sidebar.caption(f"Stats ramenées à {BASE_MIN} min")
df = get_data(SEASON)
names = sorted(df["PLAYER_NAME"].unique())
top = df[df["is_candidate"]].sort_values("PTS", ascending=False)["PLAYER_NAME"].tolist()
default = names.index(top[0]) if top else 0
player = st.sidebar.selectbox("Rechercher un joueur )", names,
                              index=default, key=f"player_{SEASON}")
if st.sidebar.button("Rafraîchir les données"):
    load_data(SEASON, force=True)
    st.cache_data.clear()
    st.rerun()

row = df[df["PLAYER_NAME"] == player].iloc[0]


def metric_bar(col: str, color: str):
    """Barres : le joueur choisi face aux candidats MVP sur une stat."""
    label, higher = METRICS[col]
    pool = df[df["is_candidate"] | (df["PLAYER_NAME"] == player)]
    pool = pool.sort_values(col, ascending=higher)  # meilleur en haut
    colors = [color if n == player else GREY for n in pool["PLAYER_NAME"]]
    fig = go.Figure(go.Bar(x=pool[col], y=pool["PLAYER_NAME"], orientation="h",
                           marker_color=colors, text=pool[col], textposition="outside"))
    fig.update_layout(title=f"{label} — top {row[f'{col}_pct']:.0f}e percentile",
                      height=380, margin=dict(l=0, r=20, t=50, b=0), showlegend=False)
    return fig


def radar(players: list[str]):
    cols = list(METRICS)
    labels = [METRICS[c][0] for c in cols]
    fig = go.Figure()
    for p in players:
        r = df[df["PLAYER_NAME"] == p].iloc[0]
        vals = [r[f"{c}_pct"] for c in cols]
        fig.add_trace(go.Scatterpolar(r=vals + vals[:1], theta=labels + labels[:1],
                                      name=p, fill="toself" if len(players) == 1 else None))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])), height=520,
                      margin=dict(t=30, b=30))
    return fig


tab1, tab2 = st.tabs([" Profil joueur", " Comparateur MVP"])

# ---------- Onglet 1 : profil ----------
with tab1:
    st.header(player)
    st.caption(f"{row['TEAM_ABBREVIATION']} · {int(row['GP'])} matchs · {row['MIN']:.1f} min/match")
    c = st.columns(4)
    c[0].metric("Points /36", row["PTS_36"], f"{row['PTS']:.1f} /match", delta_color="off")
    c[1].metric("Rebonds /36", row["REB_36"], f"{row['REB']:.1f} /match", delta_color="off")
    c[2].metric("Passes /36", row["AST_36"], f"{row['AST']:.1f} /match", delta_color="off")
    c[3].metric("True Shooting", f"{row['TS_PCT'] * 100:.1f}%" if pd.notna(row["TS_PCT"]) else "n/a")

    if pd.isna(row["PTS_36_pct"]):
        st.warning("Échantillon trop faible (peu de matchs/minutes) : percentiles non calculés.")
    else:
        st.plotly_chart(radar([player]), use_container_width=True)
        best, worst = strengths_weaknesses(row)

        st.subheader("3 domaines où il excelle")
        for col_ui, m in zip(st.columns(3), best):
            col_ui.plotly_chart(metric_bar(m, GREEN), use_container_width=True)

        st.subheader(" 3 domaines où il est moins bon")
        for col_ui, m in zip(st.columns(3), worst):
            col_ui.plotly_chart(metric_bar(m, RED), use_container_width=True)
        st.caption("Percentiles calculés sur les joueurs ayant ≥ 20 matchs et ≥ 20 min/match. "
                   "Pour les balles perdues, moins = mieux.")

# ---------- Onglet 2 : comparateur ----------
with tab2:
    st.header("Course au MVP — à volume égal (36 min)")
    available = df[df["is_candidate"]].sort_values("PTS", ascending=False)["PLAYER_NAME"].tolist()
    chosen = st.multiselect("Candidats", available, default=available, key=f"cands_{SEASON}")
    if chosen:
        sub = df[df["PLAYER_NAME"].isin(chosen)]
        table_cols = ["PLAYER_NAME", "GP", "MIN"] + list(METRICS)
        table = sub[table_cols].rename(columns={c: METRICS[c][0] for c in METRICS})
        st.header(f"{player} — {SEASON}")
        st.header(f"Course au MVP {SEASON} — à volume égal (36 min)")
        st.dataframe(table.sort_values("Points /36", ascending=False),
                     use_container_width=True, hide_index=True)

        left, right = st.columns([3, 2])
        with left:
            st.plotly_chart(radar(chosen), use_container_width=True)
        with right:
            stat = st.selectbox("Classement sur une stat", list(METRICS),
                                format_func=lambda k: METRICS[k][0])
            lab, higher = METRICS[stat]
            s = sub.sort_values(stat, ascending=higher)
            fig = go.Figure(go.Bar(x=s[stat], y=s["PLAYER_NAME"], orientation="h",
                                   marker_color=ORANGE, text=s[stat], textposition="outside"))
            fig.update_layout(title=lab, height=520, margin=dict(l=0, r=20, t=50, b=0))
            st.plotly_chart(fig, use_container_width=True)
