"""Utilitaires pour la creation et l'alimentation de la base SQLite."""

import csv
import sqlite3
from pathlib import Path
from typing import Callable, Final, Optional

# Constantes
CHUNK_SIZE: Final[int] = 20_000
DEFAULT_DELIMITER = ";"
FALLBACK_DELIMITER = ","

# Type aliases
Reporter = Callable[[str], None]

# Schema dans l'ordre attendu
EFFECTIFS_COLUMNS: list[tuple[str, str]] = [
    ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
    ("annee", "INTEGER"),
    ("patho_niv1", "TEXT"),
    ("patho_niv2", "TEXT"),
    ("patho_niv3", "TEXT"),
    ("top", "TEXT"),
    ("cla_age_5", "TEXT"),
    ("sexe", "INTEGER"),
    ("region", "TEXT"),
    ("dept", "TEXT"),
    ("Ntop", "INTEGER"),
    ("Npop", "INTEGER"),
    ("prev", "TEXT"),
    ("Niveau prioritaire", "TEXT"),
    ("libelle_classe_age", "TEXT"),
    ("libelle_sexe", "TEXT"),
    ("tri", "REAL"),
]


def bootstrap_db_from_csv(
    db_path: Path,
    csv_path: Path,
    table_name: str,
    *,
    force_reimport: bool = False,
    report: Optional[Reporter] = None,
) -> None:
    """Cree la table SQLite et importe le CSV si necessaire.

    Args:
        db_path: Chemin vers le fichier SQLite a alimenter.
        csv_path: Chemin du fichier CSV source.
        table_name: Nom de la table cible dans SQLite.
        force_reimport: True pour reinjecter meme si des donnees existent.
        report: Fonction de log pour suivre la progression.
    """
    report_fn = report or print
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        # Creer la table si elle n'existe pas
        cols_sql = ", ".join(f'"{name}" {col_type}' for name, col_type in EFFECTIFS_COLUMNS)
        conn.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({cols_sql});')
        conn.commit()

        # Verifier si des donnees existent deja
        cursor = conn.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        existing = cursor.fetchone()[0]

        if existing > 0 and not force_reimport:
            report_fn(f"[OK] Donnees deja presentes dans {table_name} - import ignore.")
            return

        if existing > 0 and force_reimport:
            conn.execute(f'DELETE FROM "{table_name}";')
            conn.commit()
            report_fn(f"[INFO] Table videe : {table_name}")

    inserted = import_csv_to_sqlite(csv_path, db_path, table_name)
    report_fn(f"[OK] Import SQLite termine - {inserted} lignes.")


def import_csv_to_sqlite(csv_path: Path, db_path: Path, table_name: str) -> int:
    """Insere le contenu d'un CSV dans une table SQLite.

    Args:
        csv_path: Chemin du fichier CSV a parcourir.
        db_path: Chemin du fichier SQLite.
        table_name: Nom de la table cible.

    Returns:
        Nombre total de lignes inserees dans la table.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        # 1) S'assurer que la table existe
        cols_sql = ", ".join(f'"{name}" {col_type}' for name, col_type in EFFECTIFS_COLUMNS)
        conn.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({cols_sql});')
        conn.commit()

        # 2) Preparer la requete INSERT (SQLite gere l'auto-increment de l'id)
        cols = [name for name, _ in EFFECTIFS_COLUMNS if name != "id"]
        placeholders = ", ".join("?" for _ in cols)
        cols_quoted = ", ".join(f'"{col}"' for col in cols)
        insert_sql = f'INSERT INTO "{table_name}" ({cols_quoted}) VALUES ({placeholders});'

        # 3) Detecter le delimiteur
        with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
            header = file.readline()
            delim = DEFAULT_DELIMITER if DEFAULT_DELIMITER in header else (
                FALLBACK_DELIMITER if FALLBACK_DELIMITER in header else DEFAULT_DELIMITER
            )
            file.seek(0)
            reader = csv.DictReader(file, delimiter=delim)

            # 4) Insertion par lots
            batch, total = [], 0
            for row in reader:
                batch.append([row.get(col) for col in cols])
                if len(batch) >= CHUNK_SIZE:
                    conn.executemany(insert_sql, batch)
                    conn.commit()
                    total += len(batch)
                    batch.clear()

            # Inserer le dernier lot
            if batch:
                conn.executemany(insert_sql, batch)
                conn.commit()
                total += len(batch)

        return total


def count_rows_raw(db_path: Path, table_name: str) -> int:
    """Compte le nombre de lignes d'une table via SQL brut.

    Args:
        db_path: Chemin du fichier SQLite.
        table_name: Nom de la table a compter.

    Returns:
        Nombre de lignes presentes dans la table.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        return int(cursor.fetchone()[0])
