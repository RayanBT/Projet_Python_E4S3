"""Construction de l'application Dash et gestion du routage."""

from __future__ import annotations

import time

from dash import Dash, Input, Output, dcc, html

from src.components.footer import footer
from src.components.header import header
from src.components.navbar import navbar
from src.pages.setup import render_setup_page
from src.pages.simple_page import layout as simple_page_layout
from src.state.init_progress import InitializationState

COMPLETION_DELAY = 2.0


def _should_show_loader(status: dict) -> bool:
    """Determine si l'ecran de chargement doit rester visible.

    Args:
        status (dict): Etat courant de l'initialisation.

    Returns:
        bool: True si le loader doit apparaitre, False sinon.
    """
    if status.get("needs_setup", False):
        return True
    finished_at = status.get("finished_at")
    if status.get("success") and finished_at:
        return (time.time() - float(finished_at)) < COMPLETION_DELAY
    return False


def create_app(init_state: InitializationState) -> Dash:
    """Assemble l'application Dash et ses callbacks principaux.

    Args:
        init_state (InitializationState): Etat partage contenant la progression.

    Returns:
        Dash: Instance configuree de l'application Dash.
    """
    app = Dash(__name__, suppress_callback_exceptions=True)

    initial_status = init_state.to_dict()
    initial_status["show_loader"] = _should_show_loader(initial_status)
    app.layout = html.Div(
        [
            header("Mon Dashboard"),
            navbar(),
            dcc.Location(id="url", refresh=False),
            dcc.Store(id="init-status", data=initial_status),
            dcc.Interval(
                id="init-poll",
                interval=1_000,
                n_intervals=0,
                disabled=not initial_status["needs_setup"],
            ),
            html.Div(id="page-content"),
            footer(),
        ]
    )

    @app.callback(
        Output("init-status", "data"),
        Output("init-poll", "disabled"),
        Input("init-poll", "n_intervals"),
        prevent_initial_call=False,
    )
    def refresh_init_status(_n: int) -> tuple[dict, bool]:
        """Rafraichit periodiquement l'etat d'initialisation presente dans le store."""
        status = init_state.to_dict()
        show_loader = _should_show_loader(status)
        status["show_loader"] = show_loader
        disable_interval = status.get("completed", False) and not show_loader
        return status, disable_interval

    @app.callback(
        Output("page-content", "children"),
        Input("url", "pathname"),
        Input("init-status", "data"),
    )
    def display_page(pathname: str, init_status: dict) -> html.Div:
        """Retourne le layout approprie selon le chemin et l'avancement."""
        show_loader = init_status.get("show_loader", False)
        needs_setup = init_status.get("needs_setup", False)
        completed = init_status.get("completed", False)
        success = init_status.get("success", False)
        messages = init_status.get("messages", [])
        current_step = init_status.get("current_step")
        finished_at = init_status.get("finished_at")

        if show_loader:
            return render_setup_page(
                messages,
                current_step=current_step,
                completed=completed,
                success=success,
                finished_at=finished_at,
            )

        if pathname == "/simple":
            return simple_page_layout()
        if pathname == "/about":
            return html.H2("Page a propos")
        return html.H2("Bienvenue sur la page d'accueil !")

    return app
