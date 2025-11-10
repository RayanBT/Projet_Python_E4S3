"""Construction de l'application Dash et gestion du routage."""

from __future__ import annotations

import os
import time

from dash import Dash, Input, Output, dcc, html

from src.components.footer import footer
from src.components.header import header
from src.components.navbar import navbar
from src.pages.setup import render_setup_page
from src.state.init_progress import InitializationState

# Import des modules pour enregistrer les callbacks (sans exécuter les layouts)
import src.pages.accueil as accueil_module
import src.pages.carte as carte_module
import src.pages.evolution as evolution_module
import src.pages.histogramme as histogramme_module
import src.pages.radar as radar_module

COMPLETION_DELAY = 2.0


def _should_show_loader(status: dict[str, bool | float]) -> bool:
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
    # Chemin absolu vers le dossier assets dans src/
    # __file__ est dans src/pages/home.py, donc on remonte de 1 niveau
    src_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_path = os.path.join(src_root, 'assets')

    app = Dash(
        __name__,
        suppress_callback_exceptions=True,
        assets_folder=assets_path,
        assets_url_path='/assets'
    )

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
                interval=2_000,
                n_intervals=0,
                disabled=not initial_status["needs_setup"],
            ),
            html.Div(id="page-content", className="page-content-wrapper"),
            footer(),
        ]
    )

    @app.callback(
        Output("init-status", "data"),
        Output("init-poll", "disabled"),
        Input("init-poll", "n_intervals"),
        prevent_initial_call=False,
    )
    def refresh_init_status(
        _n: int
    ) -> tuple[dict[str, bool | float | str | list[str] | None], bool]:
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
        prevent_initial_call=False,
    )
    def display_page(
        pathname: str,
        init_status: dict[str, bool | float | str | list[str] | None]
    ) -> html.Div | html.H2:
        """Retourne le layout approprie selon le chemin et l'avancement."""
        show_loader = bool(init_status.get("show_loader", False))
        completed = bool(init_status.get("completed", False))
        success = bool(init_status.get("success", False))
        messages_raw = init_status.get("messages", [])
        messages = messages_raw if isinstance(messages_raw, list) else []
        current_step_raw = init_status.get("current_step")
        current_step = (
            str(current_step_raw) if current_step_raw is not None else None
        )

        if show_loader:
            return render_setup_page(
                messages,
                current_step=current_step,
                completed=completed,
                success=success,
            )

        # Routes pour les nouvelles pages
        if pathname == "/carte":
            return carte_module.layout()
        if pathname == "/evolution":
            return evolution_module.layout()
        if pathname == "/histogramme":
            return histogramme_module.layout()
        if pathname == "/radar":
            return radar_module.layout()
        if pathname == "/about":
            return html.H2("Page a propos")

        # Page d'accueil par défaut
        return accueil_module.layout()

    return app
