"""Gestion de l'initialisation des donnees et lancement de l'application Dash."""

from __future__ import annotations

import os
from pathlib import Path
from threading import Thread
from typing import Callable, Final

import requests

from db.models import count_rows_orm, get_engine, get_session, reflect_effectifs  # type: ignore
from db.schema import as_pydantic_models  # type: ignore
from db.utils import bootstrap_db_from_csv, count_rows_raw  # type: ignore
from src.pages.home import create_app
from src.state.init_progress import init_state

ROOT: Final[Path] = Path(__file__).resolve().parent
DATA_DIR: Final[Path] = ROOT / "data"
CSV_URL: Final[str] = (
    "https://data.ameli.fr/api/explore/v2.1/catalog/datasets/effectifs/"
    "exports/csv?use_labels=true"
)
CSV_DEST: Final[Path] = DATA_DIR / "raw/effectifs.csv"
DB_PATH: Final[Path] = DATA_DIR / "effectifs.sqlite3"
TABLE_NAME: Final[str] = "effectifs"

Reporter = Callable[[str], None]


def ensure_effectifs_csv(report: Reporter | None = None) -> Path:
    """Telecharge le CSV distant si necessaire.

    Args:
        report (Reporter | None): Fonction de log recevant les messages d'avancement.

    Returns:
        Path: Chemin du fichier CSV garanti sur le disque.
    """
    reporter = report or print
    CSV_DEST.parent.mkdir(parents=True, exist_ok=True)

    if CSV_DEST.exists() and CSV_DEST.stat().st_size > 0:
        reporter(f"[OK] CSV deja present : {CSV_DEST}")
        return CSV_DEST

    reporter("[INFO] Telechargement du CSV en cours...")
    tmp = CSV_DEST.with_suffix(".part")

    try:
        with requests.get(CSV_URL, stream=True, timeout=60) as response:
            response.raise_for_status()
            with tmp.open("wb") as fh:
                for chunk in response.iter_content(chunk_size=1_048_576):
                    if chunk:
                        fh.write(chunk)
        tmp.replace(CSV_DEST)
        reporter(f"[OK] CSV telecharge : {CSV_DEST}")
        return CSV_DEST
    except Exception as exc:  # pragma: no cover - defensive cleanup
        tmp.unlink(missing_ok=True)
        if CSV_DEST.exists() and CSV_DEST.stat().st_size == 0:
            CSV_DEST.unlink(missing_ok=True)
        reporter(f"[ERREUR] Telechargement echoue : {exc}")
        raise


def summarise_database(report: Reporter) -> None:
    """Affiche quelques statistiques sur la base chargee.

    Args:
        report (Reporter): Fonction de log recevant les messages d'avancement.

    Returns:
        None
    """
    total_raw = count_rows_raw(DB_PATH, TABLE_NAME)
    report(f"[RAW SQL] {TABLE_NAME} -> {total_raw} lignes")

    engine = get_engine(DB_PATH)
    Effectif = reflect_effectifs(engine, TABLE_NAME)
    with get_session(engine) as session:
        total_orm = count_rows_orm(session, Effectif)
        report(f"[ORM] {TABLE_NAME} -> {total_orm} lignes")

        try:
            _, EffectifOut = as_pydantic_models()
            rows = session.query(Effectif).limit(3).all()
            for idx, row in enumerate(rows, start=1):
                model = EffectifOut.model_validate(row)
                report(f"[ORM/Pydantic] exemple {idx}: {model.model_dump()}")
        except Exception as exc:  # pragma: no cover - optional validation
            report(f"[INFO] Pydantic ignore ({exc.__class__.__name__}: {exc})")


def perform_initialization(report: Reporter) -> bool:
    """Effectue toutes les etapes d'initialisation des donnees.

    Args:
        report (Reporter): Fonction de log recevant les messages d'avancement.

    Returns:
        bool: True si toutes les etapes se sont bien deroulees, False sinon.
    """
    try:
        report("[STEP] Initialisation des donnees")
        report("[STEP] Telechargement du CSV")
        csv_path = ensure_effectifs_csv(report=report)
        report("[STEP] Initialisation de la base SQLite")
        bootstrap_db_from_csv(
            DB_PATH,
            csv_path,
            TABLE_NAME,
            force_reimport=False,
            report=report,
        )
        report("[STEP] Verification des donnees")
        summarise_database(report)
        report("[STEP] Initialisation terminee")
        report("[OK] Initialisation terminee.")
        return True
    except Exception as exc:
        report(f"[ERREUR] Initialisation interrompue : {exc}")
        return False


def needs_initialization() -> bool:
    """Determine si les donnees doivent etre preparees.

    Returns:
        bool: True si au moins une ressource (CSV ou base) doit etre reimportee.
    """
    csv_ready = CSV_DEST.exists() and CSV_DEST.stat().st_size > 0
    if not csv_ready:
        return True

    if not DB_PATH.exists():
        return True

    try:
        return count_rows_raw(DB_PATH, TABLE_NAME) == 0
    except Exception:
        return True


def start_background_initialization() -> None:
    """Lance la preparation des donnees dans un thread de fond.

    Returns:
        None
    """
    init_state.set_step("Initialisation en cours...")

    def worker() -> None:
        success = perform_initialization(init_state.log)
        init_state.mark_complete(success=success)

    Thread(target=worker, daemon=True).start()


def prepare_database(report: Reporter | None = None) -> None:
    """Prepare la base synchronement pour les scripts ou tests.

    Args:
        report (Reporter | None): Fonction de log personnalisee ou None pour print.

    Raises:
        RuntimeError: Si l'initialisation echoue.
    """
    reporter = report or print
    success = perform_initialization(reporter)
    if not success:
        raise RuntimeError("Initialisation des donnees echouee")


if __name__ == "__main__":
    is_reloader = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    needs_setup = needs_initialization()
    init_state.reset(needs_setup=needs_setup)

    if not needs_setup:
        init_state.log("[OK] Donnees deja presentes. Redirection vers l'accueil.")
        init_state.mark_complete(success=True)
    elif is_reloader:
        start_background_initialization()
        print("[INFO] Preparation des donnees lancee en arriere-plan.")

    app = create_app(init_state)
    app.run(debug=True)
