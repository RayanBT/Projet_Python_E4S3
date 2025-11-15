"""Composant d'entete utilise sur l'ensemble des pages Dash."""

from dash import html


def header(title: str = "Dashboard d'Analyse des Pathologies en France", subtitle: str = "Visualisation interactive des données de santé publique (2015-2023)") -> html.Header:
    """Construit le bandeau d'entete principal.

    Args:
        title: Texte a afficher dans la balise titre.
        subtitle: Sous-titre explicatif.

    Returns:
        Composant Dash representant l'entete.
    """
    return html.Header(
        className="app-header",
        children=[
            html.Div(className="header-content", children=[
                html.H1(title, className="header-title"),
                html.P(subtitle, className="header-subtitle")
            ])
        ]
    )
