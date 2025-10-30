"""Etat partage permettant de suivre l'initialisation des donnees."""

from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock
from typing import Any, Dict, List


@dataclass
class InitializationSnapshot:
    """Photographie immuable de l'etat d'initialisation.

    Attributes:
        messages (List[str]): Ensemble des messages deja emis.
        completed (bool): Indique si l'operation est terminee.
        success (bool): Indique si toutes les etapes ont reussi.
        needs_setup (bool): Precise si la preparation reste necessaire.
        current_step (str | None): Libelle de l'etape en cours.
        finished_at (float | None): Timestamp UNIX de fin, si disponible.
    """

    messages: List[str]
    completed: bool
    success: bool
    needs_setup: bool
    current_step: str | None
    finished_at: float | None


class InitializationState:
    """Conteneur thread-safe pour centraliser la progression."""

    def __init__(self) -> None:
        """Initialise un etat vide et un verrou de synchronisation."""
        self._lock = Lock()
        self._messages: List[str] = []
        self._completed = False
        self._success = False
        self._needs_setup = False
        self._current_step: str | None = None
        self._finished_at: float | None = None

    def reset(self, *, needs_setup: bool) -> None:
        """Reinitialise completement l'etat interne.

        Args:
            needs_setup (bool): True si la phase de setup doit etre lancee.
        """
        with self._lock:
            self._messages.clear()
            self._completed = False
            self._success = False
            self._needs_setup = needs_setup
            self._current_step = "Initialisation en attente" if needs_setup else None
            self._finished_at = None
            if needs_setup:
                self._messages.append("[STEP] Initialisation en attente")

    def log(self, message: str) -> None:
        """Ajoute un message au journal et met a jour l'etape si besoin.

        Args:
            message (str): Texte deja formatte (peut commencer par [STEP]).
        """
        with self._lock:
            if message.startswith("[STEP] "):
                self._current_step = message[7:].strip() or None
            self._messages.append(message)

    def set_step(self, step: str) -> None:
        """Declare une nouvelle etape et enregistre le message correspondant.

        Args:
            step (str): Libelle humain de l'etape courante.
        """
        with self._lock:
            self._current_step = step
            self._messages.append(f"[STEP] {step}")

    def mark_complete(self, *, success: bool) -> None:
        """Marque la fin de l'initialisation et stocke le resultat.

        Args:
            success (bool): True si toutes les etapes ont reussi.
        """
        with self._lock:
            self._completed = True
            self._success = success
            if success:
                self._needs_setup = False
                self._current_step = "Initialisation terminee"
            else:
                self._current_step = "Initialisation echouee"
            self._finished_at = time.time()

    def snapshot(self) -> InitializationSnapshot:
        """Cree une copie immutable de l'etat courant.

        Returns:
            InitializationSnapshot: Copie detachee utilisable sans verrou.
        """
        with self._lock:
            return InitializationSnapshot(
                messages=list(self._messages),
                completed=self._completed,
                success=self._success,
                needs_setup=self._needs_setup,
                current_step=self._current_step,
                finished_at=self._finished_at,
            )

    def to_dict(self) -> Dict[str, Any]:
        """Expose l'etat courant sous forme de dictionnaire serialisable.

        Returns:
            Dict[str, Any]: Etat interne pret a etre stocke dans Dash.
        """
        snap = self.snapshot()
        return {
            "messages": snap.messages,
            "completed": snap.completed,
            "success": snap.success,
            "needs_setup": snap.needs_setup,
            "current_step": snap.current_step,
            "finished_at": snap.finished_at,
        }


init_state = InitializationState()
