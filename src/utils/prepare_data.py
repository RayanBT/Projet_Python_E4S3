"""Utilitaires de gestion des données (CSV, DB, vérifications).

Ce module contient les fonctions pour :
- Télécharger et nettoyer le CSV des effectifs
- Télécharger le JSON des départements/régions
- Initialiser et vérifier la base SQLite
- Nettoyer les labels de pathologies

Typiquement utilisé par main.py mais peut être importé ailleurs.
"""

from __future__ import annotations

from pathlib import Path
from threading import Thread
from typing import Callable, Final

import requests

from db.models import count_rows_orm, get_engine, get_session, reflect_effectifs
from db.schema import as_pydantic_models
from db.utils import bootstrap_db_from_csv, count_rows_raw
from src.state.init_progress import init_state
from src.utils.clean_data import (
    clean_csv_data,
    verify_pathologie_labels,
    clean_pathologie_labels
)

# Import de la configuration centralisée
import config

# Type pour les fonctions de rapport/log
Reporter = Callable[[str], None]

# Utilisation des chemins depuis config.py
DATA_DIR: Final[Path] = config.DATA_DIR
CSV_URL: Final[str] = config.CSV_URL
DEPT_REGION_URL: Final[str] = config.DEPT_REGION_URL
CSV_DEST: Final[Path] = config.CSV_RAW_PATH
DEPT_REGION_DEST: Final[Path] = config.DEPT_REGION_JSON_PATH
DB_PATH: Final[Path] = config.DB_PATH
TABLE_NAME: Final[str] = config.DB_TABLE_NAME


def ensure_departements_regions_json(report: Reporter | None = None) -> Path:
    """Telecharge le JSON des departements et regions si necessaire.

    Args:
        report (Reporter | None): Fonction de log recevant les messages d'avancement.

    Returns:
        Path: Chemin du fichier JSON des departements-regions.
    """
    reporter = report or print
    DEPT_REGION_DEST.parent.mkdir(parents=True, exist_ok=True)

    if DEPT_REGION_DEST.exists() and DEPT_REGION_DEST.stat().st_size > 0:
        reporter(f"[OK] JSON departements-regions deja present : {DEPT_REGION_DEST}")
    else:
        reporter("[INFO] Telechargement du JSON departements-regions en cours...")
        tmp = DEPT_REGION_DEST.with_suffix(".part")
        try:
            with requests.get(DEPT_REGION_URL, timeout=30) as response:
                response.raise_for_status()
                with tmp.open("wb") as fh:
                    fh.write(response.content)
            tmp.replace(DEPT_REGION_DEST)
            reporter(f"[OK] JSON departements-regions telecharge : {DEPT_REGION_DEST}")
        except Exception as exc:
            tmp.unlink(missing_ok=True)
            if DEPT_REGION_DEST.exists() and DEPT_REGION_DEST.stat().st_size == 0:
                DEPT_REGION_DEST.unlink(missing_ok=True)
            reporter(f"[ERREUR] Telechargement du JSON echoue : {exc}")
            raise

    return DEPT_REGION_DEST


def ensure_effectifs_csv(report: Reporter | None = None) -> tuple[Path, Path]:
    """Telecharge le CSV distant si necessaire et le nettoie.

    Args:
        report (Reporter | None): Fonction de log recevant les messages d'avancement.

    Returns:
        tuple[Path, Path]: Chemins des fichiers CSV brut et nettoyé.
    """
    reporter = report or print
    CSV_DEST.parent.mkdir(parents=True, exist_ok=True)

    if CSV_DEST.exists() and CSV_DEST.stat().st_size > 0:
        reporter(f"[OK] CSV brut deja present : {CSV_DEST}")
    else:
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
        except Exception as exc:
            tmp.unlink(missing_ok=True)
            if CSV_DEST.exists() and CSV_DEST.stat().st_size == 0:
                CSV_DEST.unlink(missing_ok=True)
            reporter(f"[ERREUR] Telechargement echoue : {exc}")
            raise

    cleaned_csv = config.CSV_CLEAN_PATH
    try:
        reporter("[INFO] Nettoyage des donnees en cours...")
        cleaned_csv = clean_csv_data(CSV_DEST, cleaned_csv, report=reporter)
        reporter(f"[OK] CSV nettoye : {cleaned_csv}")
    except Exception as e:
        reporter(f"[ERREUR] Nettoyage impossible : {e}")
        raise

    return CSV_DEST, cleaned_csv


def summarise_database(report: Reporter) -> None:
    """Affiche quelques statistiques sur la base chargee et valide avec Pydantic.

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
            from pydantic import ValidationError
            _, EffectifOut = as_pydantic_models()
            
            # Valider un échantillon plus large pour vérifier l'intégrité
            sample_size = min(100, total_orm)
            rows = session.query(Effectif).limit(sample_size).all()
            
            valid_count = 0
            invalid_count = 0
            errors_sample: list[str] = []
            
            for idx, row in enumerate(rows, start=1):
                try:
                    model = EffectifOut.model_validate(row)
                    valid_count += 1
                    # Afficher seulement les 3 premiers exemples
                    if idx <= 3:
                        report(f"[ORM/Pydantic] exemple {idx}: {model.model_dump()}")
                except ValidationError as e:
                    invalid_count += 1
                    if len(errors_sample) < 3:
                        errors_sample.append(f"Ligne {idx}: {e.error_count()} erreur(s)")
            
            # Rapport de validation
            report(f"[Pydantic Validation] {valid_count}/{sample_size} lignes valides")
            if invalid_count > 0:
                report(f"[Pydantic WARNING] {invalid_count} ligne(s) invalide(s) détectée(s):")
                for err in errors_sample:
                    report(f"  - {err}")
            else:
                report("[Pydantic OK] ✅ Toutes les lignes testées sont valides")
                
        except Exception as exc:
            report(f"[WARNING] Validation Pydantic échouée ({exc.__class__.__name__}: {exc})")


def verify_and_clean_pathologies(report: Reporter) -> None:
    """Verifie les labels de pathologies et les nettoie si necessaire.

    Args:
        report (Reporter): Fonction de log recevant les messages d'avancement.

    Returns:
        None
    """
    try:
        pathologies = verify_pathologie_labels(DB_PATH, report=lambda msg: None)

        labels_longs = [p for p in pathologies if p['est_long']]

        if labels_longs:
            count_long = len(labels_longs)
            report(f"[INFO] Detection de {count_long} labels de pathologies trop longs")
            report("[INFO] Nettoyage automatique des labels en cours...")

            stats = clean_pathologie_labels(DB_PATH, dry_run=False, report=lambda msg: None)

            count_modified = stats['pathologies_modifiees']
            count_affected = stats['lignes_affectees']
            report(f"[OK] {count_modified} pathologies raccourcies")
            report(f"[OK] {count_affected:,} lignes mises a jour")
        else:
            report("[OK] Tous les labels de pathologies sont deja au bon format")

    except Exception as exc:
        report(f"[AVERTISSEMENT] Impossible de verifier/nettoyer les labels : {exc}")


def perform_initialization(report: Reporter) -> bool:
    """Effectue toutes les etapes d'initialisation des donnees.

    Args:
        report (Reporter): Fonction de log recevant les messages d'avancement.

    Returns:
        bool: True si toutes les etapes se sont bien deroulees, False sinon.
    """
    try:
        report("[STEP] Initialisation des donnees")
        report("[STEP] Telechargement du JSON departements-regions")
        ensure_departements_regions_json(report=report)
        report("[STEP] Telechargement du CSV")
        _, cleaned_csv_path = ensure_effectifs_csv(report=report)
        report("[STEP] Initialisation de la base SQLite")
        bootstrap_db_from_csv(
            DB_PATH,
            cleaned_csv_path,
            TABLE_NAME,
            force_reimport=False,
            report=report,
        )
        report("[STEP] Verification des donnees")
        summarise_database(report)
        report("[STEP] Verification et nettoyage des labels de pathologies")
        verify_and_clean_pathologies(report)
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


def needs_label_cleaning() -> bool:
    """Determine si les labels de pathologies doivent etre nettoyes.

    Returns:
        bool: True si des labels trop longs sont detectes.
    """
    if not DB_PATH.exists():
        return False

    try:
        pathologies = verify_pathologie_labels(DB_PATH, report=lambda msg: None)
        labels_longs = [p for p in pathologies if p['est_long']]
        return len(labels_longs) > 0
    except Exception:
        return False


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


def start_background_label_cleaning() -> None:
    """Lance le nettoyage des labels dans un thread de fond.

    Returns:
        None
    """
    init_state.set_step("Verification des labels de pathologies...")

    def worker() -> None:
        try:
            init_state.log("[INFO] Verification des labels de pathologies...")
            pathologies = verify_pathologie_labels(DB_PATH, report=lambda msg: None)
            labels_longs = [p for p in pathologies if p['est_long']]

            if labels_longs:
                init_state.log(f"[INFO] Detection de {len(labels_longs)} labels trop longs")
                init_state.set_step("Nettoyage des labels en cours...")
                init_state.log("[INFO] Nettoyage automatique des labels...")

                stats = clean_pathologie_labels(
                    DB_PATH,
                    dry_run=False,
                    report=init_state.log
                )

                count_modified = stats['pathologies_modifiees']
                count_affected = stats['lignes_affectees']
                init_state.log(f"[OK] {count_modified} pathologies raccourcies")
                init_state.log(f"[OK] {count_affected:,} lignes mises a jour")
            else:
                init_state.log("[OK] Tous les labels sont deja au bon format")

            init_state.mark_complete(success=True)
        except Exception as exc:
            init_state.log(f"[ERREUR] Nettoyage des labels echoue : {exc}")
            init_state.mark_complete(success=False)

    Thread(target=worker, daemon=True).start()


def prepare_database(report: Reporter | None = None) -> None:
    """Prepare la base synchronement pour les scripts ou tests.

    Utilisation :
        from src.utils.prepare_data import prepare_database
        prepare_database()  # Initialise la base de manière synchrone

    Args:
        report (Reporter | None): Fonction de log personnalisee ou None pour print.

    Raises:
        RuntimeError: Si l'initialisation echoue.
    """
    reporter = report or print
    success = perform_initialization(reporter)
    if not success:
        raise RuntimeError("Initialisation des donnees echouee")
