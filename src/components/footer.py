"""Pied de page affiche en bas de l'application Dash."""

from datetime import datetime

from dash import html


def footer():
    """Construit le pied de page avec l'annee courante.

    Returns:
        dash.html.Footer: Composant Dash representant le pied de page.
    """
    current_year = datetime.now().year
    return html.Footer(
        children=[
            html.P(
                f"(c) {current_year} - Mon Dashboard | Tous droits reserves",
                style={"textAlign": "center", "color": "#888", "fontSize": "14px"},
            )
        ],
        style={"marginTop": "50px", "padding": "20px", "borderTop": "1px solid #ddd"},
    )
