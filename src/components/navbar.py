"""Barre de navigation centrale partagee par toutes les pages."""

from dash import html


def navbar():
    """Cree la barre de navigation avec les liens principaux.

    Returns:
        dash.html.Nav: Composant Dash representant la navigation.
    """
    nav_links = [
        html.A("Accueil", href="/", style={"marginRight": "20px"}),
        html.A("Page simple", href="/simple", style={"marginRight": "20px"}),
        html.A("A propos", href="/about"),
    ]

    return html.Nav(
        children=nav_links,
        style={
            "display": "flex",
            "justifyContent": "center",
            "alignItems": "center",
            "backgroundColor": "#f8f9fa",
            "padding": "10px",
            "borderBottom": "1px solid #ddd",
        },
    )
