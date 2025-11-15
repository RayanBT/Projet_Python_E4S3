"""Barre de navigation centrale partagee par toutes les pages."""

from dash import html
from src.components.icons import (
    icon_home,
    icon_chart_bar,
    icon_chart_line,
    icon_info,
    icon_map,
    icon_chart_spider,
    icon_pie_chart
)


def navbar() -> html.Nav:
    """Cree la barre de navigation avec les liens principaux."""
    nav_links = [
        html.A([icon_home(), "Accueil"], href="/", className="nav-link"),
        html.A([icon_map(), "Carte"], href="/carte", className="nav-link"),
        html.A([icon_chart_line(), "Évolution"], href="/evolution", className="nav-link"),
        html.A([icon_chart_bar(), "Histogrammes"], href="/histogramme", className="nav-link"),
        html.A([icon_chart_spider(), "Graphique Radar"], href="/radar", className="nav-link"),
        html.A([icon_pie_chart(), "Diagramme Camembert"], href="/camembert", className="nav-link"),
        html.A([icon_info(), "À propos"], href="/about", className="nav-link"),
    ]

    return html.Nav(
        className="app-nav",
        children=nav_links
    )