"""Page d'accueil du dashboard avec présentation du projet."""

from dash import dcc, html

from src.components.icons import icon_chart_bar, icon_chart_line, icon_video, icon_chart_spider, icon_map, icon_pie_chart


def layout() -> html.Div:
    """Construit le layout de la page d'accueil."""
    return html.Div(className="page-container centered-container", children=[
        html.Div(className="mb-3 centered-content", children=[
            html.H1(
                "Dashboard d'Analyse des Pathologies en France",
                className="page-title"
            ),
            html.Hr(),
        ]),

        html.Div(className="card-large", children=[
            html.H2("Bienvenue", className="section-title"),
            html.P([
                (
                    "Explorez les données de santé publique françaises à travers des visualisations "
                    "interactives et intuitives. Notre dashboard vous permet d'analyser l'évolution "
                    "des pathologies à travers le temps et l'espace, avec des outils puissants pour "
                    "comprendre les tendances et les répartitions géographiques."
                )
            ], className="text-muted", style={'fontSize': '1.15rem', 'lineHeight': '1.9', 'marginBottom': '20px'}),
            html.P([
                (
                    "Naviguez entre les différentes visualisations pour découvrir les statistiques "
                    "par région, année, âge et sexe. Chaque page offre des filtres dynamiques pour "
                    "personnaliser votre analyse."
                )
            ], className="text-muted", style={'fontSize': '1.05rem', 'lineHeight': '1.8'}),
        ]),

        html.Div(className="card-large", children=[
            html.H2("Vidéo de Présentation", className="section-title text-center"),
            html.Div(className="alert alert-info", children=[
                html.Div(className="centered-content", style={'padding': '60px 20px'}, children=[
                    icon_video("icon-large"),
                    html.P(
                        "Vidéo de présentation du projet",
                        className="mt-2 text-muted",
                        style={'fontSize': '1.2rem'}
                    ),
                    html.P(
                        "(À intégrer : lien YouTube, fichier vidéo, ou enregistrement)",
                        className="text-small text-light",
                        style={'fontStyle': 'italic'}
                    ),
                ]),
            ]),
        ]),

        html.Div(className="button-group mt-3", children=[
            dcc.Link(
                html.Button(
                    [icon_map("icon-inline"), "Voir la Carte - Prévalence"],
                    className="btn btn-carte"
                ),
                href='/carte',
            ),
            dcc.Link(
                html.Button(
                    [icon_chart_line("icon-inline"), "Voir l'Évolution Temporelle"],
                    className="btn btn-evolution"
                ),
                href='/evolution',
            ),
            dcc.Link(
                html.Button(
                    [icon_chart_bar("icon-inline"), "Voir les Histogrammes"],
                    className="btn btn-histogramme"
                ),
                href='/histogramme',
            ),
            dcc.Link(
                html.Button(
                    [icon_chart_spider("icon-inline"), "Voir le Graphique Radar"],
                    className="btn btn-radar"
                ),
                href='/radar',
            ),
            dcc.Link(
                html.Button(
                    [icon_pie_chart("icon-inline"), "Voir le Diagramme Circulaire"],
                    className="btn btn-camembert"
                ),
                href='/camembert',
            ),
        ])
    ])
