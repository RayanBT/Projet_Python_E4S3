import csv
import sqlite3
from pathlib import Path
from typing import Callable, Final, Optional

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

CHUNK: Final[int] = 20_000
Reporter = Callable[[str], None]


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
        db_path (Path): Chemin vers le fichier SQLite a alimenter.
        csv_path (Path): Chemin du fichier CSV source.
        table_name (str): Nom de la table cible dans SQLite.
        force_reimport (bool): True pour reinjecter meme si des donnees existent.
        report (Reporter | None): Fonction de log pour suivre la progression.

    Returns:
        None
    """
    report_fn = report or print
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        cols_sql = ", ".join(f'"{n}" {t}' for n, t in EFFECTIFS_COLUMNS)
        conn.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({cols_sql});')
        conn.commit()

        existing = conn.execute(
            f'SELECT COUNT(*) FROM "{table_name}"'
        ).fetchone()[0]
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
        csv_path (Path): Chemin du fichier CSV a parcourir.
        db_path (Path): Chemin du fichier SQLite.
        table_name (str): Nom de la table cible.

    Returns:
        int: Nombre total de lignes inserees dans la table.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        # 1) Ensure the table exists
        cols_sql = ", ".join(f'"{n}" {t}' for n, t in EFFECTIFS_COLUMNS)
        conn.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({cols_sql});')
        conn.commit()

        # 2) Prepare the INSERT statement (SQLite handles the auto id)
        cols = [n for n, _ in EFFECTIFS_COLUMNS if n != "id"]
        placeholders = ", ".join("?" for _ in cols)
        cols_quoted = ", ".join(f'"{c}"' for c in cols)
        insert_sql = f'INSERT INTO "{table_name}" ({cols_quoted}) VALUES ({placeholders});'

        # 3) Detect the delimiter
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            header = f.readline()
            delim = ";" if ";" in header else ("," if "," in header else ";")
            f.seek(0)
            reader = csv.DictReader(f, delimiter=delim)

            # 4) Batch insert
            batch, total = [], 0
            for row in reader:
                batch.append([row.get(c) for c in cols])
                if len(batch) >= CHUNK:
                    conn.executemany(insert_sql, batch)
                    conn.commit()
                    total += len(batch)
                    batch.clear()
            if batch:
                conn.executemany(insert_sql, batch)
                conn.commit()
                total += len(batch)

        return total


def count_rows_raw(db_path: Path, table_name: str) -> int:
    """Compte le nombre de lignes d'une table via SQL brut.

    Args:
        db_path (Path): Chemin du fichier SQLite.
        table_name (str): Nom de la table a compter.

    Returns:
        int: Nombre de lignes presentes dans la table.
    """
    with sqlite3.connect(db_path) as conn:
        return int(conn.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0])
