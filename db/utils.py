import csv
import sqlite3
from pathlib import Path
from typing import Final

# Schéma dans l'ordre attendu
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


def bootstrap_db_from_csv(
    db_path: Path, csv_path: Path, table_name: str, *, force_reimport: bool = False
) -> None:
    """Assure la table et importe le CSV si nécessaire.

    - Crée la table avec PK `id` si absente.
    - Si des données existent et `force_reimport` est False, ne fait rien.
    - Si `force_reimport` est True, vide la table puis réimporte.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        cols_sql = ", ".join(f'"{n}" {t}' for n, t in EFFECTIFS_COLUMNS)
        conn.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({cols_sql});')
        conn.commit()

        existing = conn.execute(
            f'SELECT COUNT(*) FROM "{table_name}"'
        ).fetchone()[0]
        if existing > 0 and not force_reimport:
            print(f"[OK] Données déjà présentes dans {table_name} → import ignoré.")
            return
        if existing > 0 and force_reimport:
            conn.execute(f'DELETE FROM "{table_name}";')
            conn.commit()
            print(f"[INFO] Table vidée : {table_name}")

    inserted = import_csv_to_sqlite(csv_path, db_path, table_name)
    print(f"[OK] Import SQLite terminé → {inserted} lignes.")


def import_csv_to_sqlite(csv_path: Path, db_path: Path, table_name: str) -> int:
    """Importe `csv_path` dans `table_name` (création de table si besoin)."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        # 1) Assure la table (id auto + colonnes typées)
        cols_sql = ", ".join(f'"{n}" {t}' for n, t in EFFECTIFS_COLUMNS)
        conn.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({cols_sql});')
        conn.commit()

        # 2) Préparer l'INSERT (on laisse SQLite gérer id)
        cols = [n for n, _ in EFFECTIFS_COLUMNS if n != "id"]
        placeholders = ", ".join("?" for _ in cols)
        cols_quoted = ", ".join(f'"{c}"' for c in cols)
        insert_sql = f'INSERT INTO "{table_name}" ({cols_quoted}) VALUES ({placeholders});'

        # 3) Détecter le délimiteur
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            header = f.readline()
            delim = ";" if ";" in header else ("," if "," in header else ";")
            f.seek(0)
            reader = csv.DictReader(f, delimiter=delim)

            # 4) Insertions par lots
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
    with sqlite3.connect(db_path) as conn:
        return int(conn.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0])

