"""Point d'entree principal de l'application.

Gere le lancement du serveur Dash et l'initialisation des donnees si necessaire.
"""

import os
import threading
import time
import webbrowser

import config
from src.pages.home import create_app
from src.state.init_progress import init_state
from src.utils.prepare_data import (
    needs_initialization,
    needs_label_cleaning,
    start_background_initialization,
    start_background_label_cleaning,
)

# Constantes
WERKZEUG_RELOADER_VAR = "WERKZEUG_RUN_MAIN"
AUTO_BROWSER_DELAY_SECONDS = 1.0


def _auto_open_browser(host: str, port: int) -> None:
    """Ouvre le navigateur sur l'URL locale apres un court delai."""

    def _open() -> None:
        time.sleep(AUTO_BROWSER_DELAY_SECONDS)
        display_host = "127.0.0.1" if host in ("0.0.0.0", "127.0.0.1") else host
        url = f"http://{display_host}:{port}"
        try:
            webbrowser.open_new(url)
            print(f"[INFO] Ouverture automatique du navigateur sur {url}")
        except Exception as error:
            print(f"[AVERTISSEMENT] Impossible d'ouvrir automatiquement le navigateur: {error}")

    threading.Thread(target=_open, daemon=True).start()


def main() -> None:
    """Lance l'application Dash avec initialisation des donnees si necessaire."""
    is_reloader = os.environ.get(WERKZEUG_RELOADER_VAR) == "true"
    needs_setup = needs_initialization()
    needs_cleaning = needs_label_cleaning() if not needs_setup else False

    # Determiner si on a besoin d'une initialisation (CSV/DB ou nettoyage labels)
    needs_any_setup = needs_setup or needs_cleaning
    init_state.reset(needs_setup=needs_any_setup)

    if not needs_any_setup:
        # Aucune initialisation necessaire
        init_state.log("[OK] Donnees deja presentes et labels deja nettoyes.")
        init_state.mark_complete(success=True)
    elif is_reloader:
        # Lancer l'initialisation appropriee en arriere-plan
        if needs_setup:
            start_background_initialization()
            print("[INFO] Preparation des donnees lancee en arriere-plan.")
        elif needs_cleaning:
            start_background_label_cleaning()
            print("[INFO] Nettoyage des labels lance en arriere-plan.")

    app = create_app(init_state)

    should_auto_open = config.APP_AUTO_OPEN_BROWSER and (is_reloader or not config.APP_DEBUG)
    if should_auto_open:
        _auto_open_browser(config.APP_HOST, config.APP_PORT)

    app.run(debug=config.APP_DEBUG, host=config.APP_HOST, port=config.APP_PORT)


if __name__ == "__main__":
    main()
