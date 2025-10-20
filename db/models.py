# db/models.py
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import MetaData, create_engine, Table, Column, Integer, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker, registry


def get_engine(db_path: Path) -> Engine:
    """Retourne un moteur SQLAlchemy pour la base SQLite donnée."""
    return create_engine(f"sqlite:///{db_path}", future=True)


@contextmanager
def get_session(engine: Engine) -> Generator[Session, None, None]:
    """Context manager : ouvre et ferme proprement une session SQLAlchemy."""
    SessionLocal = sessionmaker(bind=engine, future=True)
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def reflect_effectifs(engine: Engine, table_name: str):
    """Reflète la table `table_name` et la mappe en ORM de manière impérative.

    - Si la PK n'est pas correctement détectée par SQLite, on force `id` comme PK.
    - Cette approche évite les écueils d'automap sur certaines tables volumineuses.
    """
    insp = inspect(engine)
    tables = insp.get_table_names()
    if table_name not in tables:
        raise LookupError(f"Table introuvable dans la base : '{table_name}'. Tables vues: {tables}")

    # Vérifie la PK détectée
    pk_info = insp.get_pk_constraint(table_name) or {}
    pk_cols = pk_info.get("constrained_columns") or []

    mapper_registry = registry()
    metadata: MetaData = mapper_registry.metadata

    if not pk_cols:
        # Fallback : on force 'id' comme PK si présent (créée par le bootstrap)
        # autoload_with=engine récupère toutes les colonnes depuis la DB
        table = Table(
            table_name,
            metadata,
            Column("id", Integer, primary_key=True),  # indice pour SQLAlchemy si SQLite hésite
            autoload_with=engine,
        )
    else:
        table = Table(table_name, metadata, autoload_with=engine)

    # Classe "vide" mappée à la table
    class Effectif:  # noqa: D401 - classe de données mappée
        """Enregistrement de la table effectifs."""

    mapper_registry.map_imperatively(Effectif, table)
    return Effectif


def count_rows_orm(session: Session, Effectif) -> int:
    """Exemple ORM : comptage de lignes via SQLAlchemy."""
    return session.query(Effectif).count()
