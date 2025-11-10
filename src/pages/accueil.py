"""Page d'accueil du dashboard avec présentation du projet."""

from dash import dcc, html

from src.components.icons import icon_chart_bar, icon_chart_line, icon_video


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
            html.H2("À propos du projet", className="section-title"),
            html.P([
                (
                    "Ce dashboard interactif permet d'explorer et d'analyser les données "
                    "de santé publique en France. "
                ),
                (
                    "Il offre une visualisation complète des pathologies déclarées "
                    "sur le territoire français, "
                ),
                "avec des analyses géographiques et temporelles détaillées."
            ], className="text-muted mb-2", style={'fontSize': '1.1rem', 'lineHeight': '1.8'}),

            html.H3("Fonctionnalités principales", className="subsection-title mt-3 mb-2"),
            html.Ul(className="info-list", children=[
                html.Li([
                    html.Strong("Carte Choroplèthe : "),
                    (
                        "Visualisation géographique de la prévalence "
                        "des pathologies par région"
                    )
                ]),
                html.Li([
                    html.Strong("Analyse Temporelle : "),
                    (
                        "Évolution des pathologies au fil des années "
                        "avec graphiques interactifs"
                    )
                ]),
                html.Li([
                    html.Strong("Filtres Dynamiques : "),
                    (
                        "Sélection par année, pathologie et région "
                        "pour des analyses personnalisées"
                    )
                ]),
                html.Li([
                    html.Strong("Base de données SQLite : "),
                    "Stockage et requêtes optimisées pour des performances rapides"
                ]),
            ]),

            html.H3("Technologies utilisées", className="subsection-title mt-3 mb-2"),
            html.Div(className="d-flex flex-wrap justify-center gap-2 mt-2", children=[
                html.Span("Python", className="tech-badge", style={'backgroundColor': '#3776ab'}),
                html.Span("Dash", className="tech-badge", style={'backgroundColor': '#119dff'}),
                html.Span("Plotly", className="tech-badge", style={'backgroundColor': '#3f4f75'}),
                html.Span("SQLite", className="tech-badge", style={'backgroundColor': '#044a64'}),
                html.Span("Pandas", className="tech-badge", style={'backgroundColor': '#150458'}),
                html.Span("Folium", className="tech-badge", style={'backgroundColor': '#77b829'}),
            ]),
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
                    [icon_chart_bar("icon-inline"), 'Voir la Carte Choroplèthe'],
                    className="btn btn-primary"
                ),
                href='/carte',
            ),
            dcc.Link(
                html.Button(
                    [icon_chart_line("icon-inline"), "Voir l'Évolution Temporelle"],
                    className="btn btn-success"
                ),
                href='/evolution',
            ),
        ])
    ])
