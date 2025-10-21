# filename = 'dash-01.py'

#
# Imports
#

import plotly_express as px

import dash
from dash import dcc, html

# Use the project's DB helpers to read `data/effectifs.sqlite3`
from pathlib import Path
from typing import Dict, Any

from main import DB_PATH, TABLE_NAME
from db.models import get_engine, get_session, reflect_effectifs

# Default year to display (will be adjusted to data present in DB)
year = None


def load_aggregated_by_region(selected_year: int):
    """Load and aggregate effectifs by region for a given year.

    Returns a list of dict rows with keys: region, Npop, Ntop, count
    """
    engine = get_engine(DB_PATH)
    Effectif = reflect_effectifs(engine, TABLE_NAME)

    with get_session(engine) as session:
        # Query all rows matching the year
        rows = (
            session.query(Effectif)
            .filter(getattr(Effectif, "annee") == selected_year)
            .all()
        )

    # Convert and aggregate without relying on pandas (optional)
    agg: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        region = getattr(r, "region", "<unknown>") or "<unknown>"
        try:
            npop = int(getattr(r, "Npop") or 0)
        except Exception:
            try:
                npop = int(float(getattr(r, "Npop")))
            except Exception:
                npop = 0
        try:
            ntop = int(getattr(r, "Ntop") or 0)
        except Exception:
            try:
                ntop = int(float(getattr(r, "Ntop")))
            except Exception:
                ntop = 0

        if region not in agg:
            agg[region] = {"region": region, "Npop": 0, "Ntop": 0, "count": 0}
        agg[region]["Npop"] += npop
        agg[region]["Ntop"] += ntop
        agg[region]["count"] += 1

    return list(agg.values())

#
# Main
#

if __name__ == "__main__":
    # Determine a sensible default year from the DB (latest available)
    engine = get_engine(DB_PATH)
    Effectif = reflect_effectifs(engine, TABLE_NAME)
    with get_session(engine) as session:
        try:
            years_available = [int(r[0]) for r in session.execute(
                f'SELECT DISTINCT annee FROM "{TABLE_NAME}" ORDER BY annee'
            ).fetchall()]
        except Exception:
            years_available = []

    if years_available:
        year = years_available[-1]
    else:
        # Fallback to a sensible default if table empty
        year = 2022

    rows = load_aggregated_by_region(year)

    # Try to use pandas for nicer DataFrame support if available
    try:
        import pandas as pd

        df = pd.DataFrame(rows)
        if df.empty:
            print(f"Aucune donnée pour l'année {year}")
    except Exception:
        df = None

    # Build a scatter: x=Npop, y=Ntop, color=region, size=count
    if df is not None:
        fig = px.scatter(df, x="Npop", y="Ntop", color="region", size="count", hover_name="region")
    else:
        # Fallback: build from list of dicts
        fig = px.scatter(rows, x="Npop", y="Ntop", color="region", size="count", hover_name="region")

    app = dash.Dash(__name__)

    app.layout = html.Div(
        children=[
            html.H1(children=f"Effectifs : Npop vs Ntop par région ({year})", style={"textAlign": "center", "color": "#7FDBFF"}),
            dcc.Graph(id="graph1", figure=fig),
            html.Div(children=f"Affiche les totaux par région pour l'année {year}. Colonnes utilisées: Npop (x), Ntop (y), count (taille)."),
        ]
    )

    app.run_server(debug=True)