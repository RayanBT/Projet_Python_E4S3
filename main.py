"""Point d'entrée principal de l'application.

Gère le lancement du serveur Dash et l'initialisation des données si nécessaire.
"""

import os

from src.pages.home import create_app
from src.state.init_progress import init_state
from src.utils.prepare_data import (
    needs_initialization,
    needs_label_cleaning,
    start_background_initialization,
    start_background_label_cleaning,
)


if __name__ == "__main__":
    is_reloader = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    needs_setup = needs_initialization()
    needs_cleaning = needs_label_cleaning() if not needs_setup else False
    
    # Déterminer si on a besoin d'une initialisation (CSV/DB ou nettoyage labels)
    needs_any_setup = needs_setup or needs_cleaning
    init_state.reset(needs_setup=needs_any_setup)

    if not needs_any_setup:
        # Aucune initialisation nécessaire
        init_state.log("[OK] Donnees deja presentes et labels deja nettoyes.")
        init_state.mark_complete(success=True)
    elif is_reloader:
        # Lancer l'initialisation appropriée en arrière-plan
        if needs_setup:
            start_background_initialization()
            print("[INFO] Preparation des donnees lancee en arriere-plan.")
        elif needs_cleaning:
            start_background_label_cleaning()
            print("[INFO] Nettoyage des labels lance en arriere-plan.")

    app = create_app(init_state)
    app.run(debug=True)
