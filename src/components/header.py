"""Composant d'entete utilise sur l'ensemble des pages Dash."""

from dash import html


def header(title: str = "Mon Dashboard"):
    """Construit le bandeau d'entete principal.

    Args:
        title (str): Texte a afficher dans la balise titre.

    Returns:
        dash.html.Header: Composant Dash representant l'entete.
    """
    return html.Header(
        children=[html.H1(title, style={"textAlign": "center", "margin": "20px 0"})],
        style={"backgroundColor": "#1E90FF", "color": "white", "padding": "10px"},
    )
