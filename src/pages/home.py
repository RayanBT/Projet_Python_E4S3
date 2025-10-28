# src/pages/home.py
from dash import Dash, html, dcc, Input, Output
from src.components.header import header
from src.components.navbar import navbar
from src.components.footer import footer
from src.pages.simple_page import layout as simple_page_layout


def create_app() -> Dash:
    """Crée et configure l'application Dash."""
    app = Dash(__name__, suppress_callback_exceptions=True)
    server = app.server

    app.layout = html.Div([
        header("Mon Dashboard"),
        navbar(),
        dcc.Location(id="url", refresh=False),
        html.Div(id="page-content"),
        footer()
    ])

    @app.callback(
        Output("page-content", "children"),
        Input("url", "pathname")
    )
    def display_page(pathname):
        if pathname == "/simple":
            return simple_page_layout()
        elif pathname == "/about":
            return html.H2("Page À propos")
        else:
            return html.H2("Bienvenue sur la page d'accueil !")

    return app
