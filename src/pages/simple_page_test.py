# src/pages/graph_ntop_prev.py

from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
from sqlalchemy import select
from db.models import get_engine, get_session, reflect_effectifs
from typing import Final
from pathlib import Path

ROOT: Final[Path] = Path(__file__).resolve().parent
DATA_DIR: Final[Path] = ROOT / "data"
DB_PATH: Final[str] = str(DATA_DIR / "effectifs.sqlite3")
TABLE_NAME = "effectifs"


def layout_graph_ntop_prev():
    return html.Div(
        children=[
            html.H2("Graphique : Ntop vs Prev"),
            html.P("Visualisation de la relation entre Ntop et prev."),
            dcc.Graph(id="graph-ntop-prev"),
        ],
        style={"padding": "20px"},
    )









import logging
logger = logging.getLogger(__name__)



















def register_callbacks(app, db_path: str):
    @app.callback(
        Output("graph-ntop-prev", "figure"),
        Input("url", "pathname"),
    )
    def update_graph(pathname: str):
        if pathname != "/simple":
            # Retourner un graphique vide si la page n'est pas active
            return px.scatter(
                pd.DataFrame({"Ntop": [], "prev": []}),
                x="prev",
                y="Ntop",
                title="Page non active",
            )

        # Connexion à la base
        engine = get_engine(db_path)
        Effectif = reflect_effectifs(engine, TABLE_NAME)

        # Lecture des données Ntop et prev
        with get_session(engine) as session:
            stmt = select(Effectif).with_only_columns([Effectif.Ntop, Effectif.prev])
            result = session.execute(stmt).all()
            df = pd.DataFrame(result, columns=["Ntop", "prev"])
        










        logger.info("Aperçu du DataFrame :\n%s", df.head())













        # Création du scatter plot
        fig = px.scatter(
            df,
            x="prev",
            y="Ntop",
            title="Relation Ntop vs Prev",
            labels={"prev": "Prev", "Ntop": "Ntop"},
            hover_data={"Ntop": True, "prev": True},
        )

        # Paramètres visuels
        fig.update_traces(
            marker=dict(size=8, opacity=0.7),
            selector=dict(mode="markers")
        )

        fig.update_layout(
            transition_duration=500,
            xaxis_title="Prev",
            yaxis_title="Ntop",
            template="plotly_white"
        )

        return fig
