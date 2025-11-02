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
        className="app-header",
        children=[
            html.Div(className="header-content", children=[
                html.H1(title, className="header-title"),
                html.P("Analyse des pathologies en France", className="header-subtitle")
            ])
        ]
    )
