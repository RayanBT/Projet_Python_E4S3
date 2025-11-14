"""Page À propos - Informations sur le projet et l'équipe."""

from dash import html, dcc


def layout() -> html.Div:
    """Layout de la page à propos."""
    return html.Div(className="page-container centered-container", children=[
        html.Div(className="mb-3 centered-content", children=[
            html.H1("À propos du projet", className="page-title"),
            html.Hr(),
        ]),

        html.Div(className="card-large", children=[
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
                    html.Strong("Histogrammes : "),
                    (
                        "Distribution des cas par âge, prévalence, "
                        "et comparaison entre régions"
                    )
                ]),
                html.Li([
                    html.Strong("Graphique Radar : "),
                    (
                        "Analyse multivariée pour comparer les pathologies "
                        "selon différents critères"
                    )
                ]),
                html.Li([
                    html.Strong("Diagramme Circulaire : "),
                    (
                        "Répartition proportionnelle des pathologies "
                        "selon leur niveau de gravité"
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

        html.Div(className="button-group mt-3", children=[
            dcc.Link(
                html.Button("← Retour à l'accueil", className="btn btn-secondary"),
                href='/',
            ),
        ])
    ])
