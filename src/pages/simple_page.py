"""Page simple de demonstration avec un petit graphique."""

from dash import dcc, html


def layout():
    """Construit le layout de la page simple.

    Returns:
        dash.html.Div: Contenu principal de la page.
    """
    return html.Div(
        children=[
            html.H2("Page Simple"),
            html.P("Ceci est une page simple de demonstration."),
            dcc.Graph(
                figure={
                    "data": [
                        {"x": [1, 2, 3, 4], "y": [10, 14, 9, 18], "type": "line", "name": "Exemple"},
                    ],
                    "layout": {"title": "Exemple de graphique"},
                }
            ),
        ],
        style={"padding": "20px"},
    )
