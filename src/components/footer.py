"""Pied de page affiche en bas de l'application Dash."""

from datetime import datetime

from dash import html


def footer() -> html.Footer:
    """Construit le pied de page avec l'annee courante."""
    current_year = datetime.now().year
    return html.Footer(
        className="app-footer",
        children=[
            html.Div(className="footer-content", children=[
                html.Div(className="footer-info", children=[
                    html.P([
                        html.Span("© ", className="footer-copyright"),
                        html.Span(f"{current_year} ", className="footer-year"),
                        html.Span("Dashboard Santé France", className="footer-brand")
                    ]),
                    html.P("Analyse des pathologies et données de santé publique",
                          className="footer-description")
                ]),
                html.Div(className="footer-links", children=[
                    html.A("À propos", href="/", className="footer-link"),
                    html.Span("•", className="footer-separator"),
                    html.A("Carte", href="/carte", className="footer-link"),
                    html.Span("•", className="footer-separator"),
                    html.A("Évolution", href="/evolution", className="footer-link"),
                    html.Span("•", className="footer-separator"),
                    html.A("Histogrammes", href="/histogramme", className="footer-link"),
                    html.Span("•", className="footer-separator"),
                    html.A("Radar", href="/radar", className="footer-link"),
                    html.Span("•", className="footer-separator"),
                    html.A("Diagramme Circulaire", href="/camembert", className="footer-link"),
                ])
            ])
        ]
    )
