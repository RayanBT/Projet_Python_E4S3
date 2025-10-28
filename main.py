from pathlib import Path
from typing import Final
import os
import requests

# --- Imports internes projet (DB et footer console) -----------------------------
from db.utils import bootstrap_db_from_csv, count_rows_raw  # type: ignore
from db.models import get_engine, get_session, reflect_effectifs, count_rows_orm  # type: ignore
from db.schema import as_pydantic_models  # type: ignore

# --- Dash imports ---------------------------------------------------------------
from dash import Dash, html, dcc, Input, Output
from src.components.header import header
from src.components.navbar import navbar
from src.components.footer import footer
from src.pages.home import create_app
from src.pages.simple_page import layout as simple_page_layout


# --- Constantes et chemins ------------------------------------------------------
ROOT: Final[Path] = Path(__file__).resolve().parent
DATA_DIR: Final[Path] = ROOT / "data"
CSV_URL: Final[str] = "https://data.ameli.fr/api/explore/v2.1/catalog/datasets/effectifs/exports/csv?use_labels=true"
CSV_DEST: Final[Path] = DATA_DIR / "raw/effectifs.csv"
DB_PATH: Final[Path] = DATA_DIR / "effectifs.sqlite3"
TABLE_NAME: Final[str] = "effectifs"


# --- Téléchargement du CSV si nécessaire ----------------------------------------
def ensure_effectifs_csv() -> Path:
    """Télécharge le CSV si nécessaire"""
    CSV_DEST.parent.mkdir(parents=True, exist_ok=True)

    if CSV_DEST.exists() and CSV_DEST.stat().st_size > 0:
        print(f"[OK] CSV déjà présent : {CSV_DEST}")
        return CSV_DEST

    print("[INFO] Téléchargement du CSV en cours...")
    tmp = CSV_DEST.with_suffix(".part")

    try:
        with requests.get(CSV_URL, stream=True, timeout=60) as response:
            response.raise_for_status()
            with tmp.open("wb") as fh:
                for chunk in response.iter_content(chunk_size=1_048_576):
                    if chunk:
                        fh.write(chunk)
        tmp.replace(CSV_DEST)
        print(f"[OK] CSV téléchargé : {CSV_DEST}")
        return CSV_DEST
    except Exception:
        tmp.unlink(missing_ok=True)
        if CSV_DEST.exists() and CSV_DEST.stat().st_size == 0:
            CSV_DEST.unlink(missing_ok=True)
        raise

# --- Entry point -----------------------------------------------------------------

def main() -> None:
    """Ensure CSV, import into SQLite, and run simple checks."""
    csv_path = ensure_effectifs_csv()

    bootstrap_db_from_csv(DB_PATH, csv_path, TABLE_NAME, force_reimport=False)

    total_raw = count_rows_raw(DB_PATH, TABLE_NAME)
    print(f"[RAW SQL] {TABLE_NAME} -> {total_raw} lignes")

    engine = get_engine(DB_PATH)
    Effectif = reflect_effectifs(engine, TABLE_NAME)
    with get_session(engine) as session:
        total_orm = count_rows_orm(session, Effectif)
        print(f"[ORM] {TABLE_NAME} -> {total_orm} lignes")

        # Try to project a few rows through the Pydantic models (demo only)
        try:
            _, EffectifOut = as_pydantic_models()
            rows = session.query(Effectif).limit(3).all()
            for idx, row in enumerate(rows, start=1):
                model = EffectifOut.model_validate(row)
                print(f"[ORM/Pydantic] exemple {idx}: {model.model_dump()}")
        except Exception as exc:
            print(f"[INFO] Pydantic ignore ({exc.__class__.__name__}: {exc})")


# --- Partie "data" --------------------------------------------------------------
def prepare_database() -> None:
    """Crée la base SQLite à partir du CSV"""
    csv_path = ensure_effectifs_csv()
    bootstrap_db_from_csv(DB_PATH, csv_path, TABLE_NAME, force_reimport=False)

    total_raw = count_rows_raw(DB_PATH, TABLE_NAME)
    print(f"[RAW SQL] {TABLE_NAME} -> {total_raw} lignes")

    engine = get_engine(DB_PATH)
    Effectif = reflect_effectifs(engine, TABLE_NAME)
    with get_session(engine) as session:
        total_orm = count_rows_orm(session, Effectif)
        print(f"[ORM] {TABLE_NAME} -> {total_orm} lignes")

        try:
            _, EffectifOut = as_pydantic_models()
            rows = session.query(Effectif).limit(3).all()
            for idx, row in enumerate(rows, start=1):
                model = EffectifOut.model_validate(row)
                print(f"[ORM/Pydantic] exemple {idx}: {model.model_dump()}")
        except Exception as exc:
            print(f"[INFO] Pydantic ignoré ({exc.__class__.__name__}: {exc})")


# --- Point d'entrée du script ---------------------------------------------------

if __name__ == "__main__":
    # Exécuter la préparation de la base seulement dans le vrai processus Dash
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        prepare_database()
        print("\n[INFO] Lancement du serveur Dash sur http://127.0.0.1:8050 ...")

    app = create_app()
    app.run(debug=True)

