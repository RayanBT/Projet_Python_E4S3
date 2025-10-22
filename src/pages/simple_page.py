# src/pages/simple_page.py
from dash import html, dcc

def layout():
    """Layout de la page simple."""
    return html.Div(
        children=[
            html.H2("Page Simple"),
            html.P("Ceci est une page simple de démonstration."),
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
