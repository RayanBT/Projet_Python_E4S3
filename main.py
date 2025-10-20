""""""
from pathlib import Path
from typing import Final
import requests

URL: Final[str] = (
    "https://data.ameli.fr/api/explore/v2.1/catalog/datasets/effectifs/exports/csv?use_labels=true"
)
DEST: Final[Path] = Path(__file__).resolve().parent / "data" / "effectifs.csv"


def ensure_effectifs_csv() -> Path:
    """Garantit la présence du fichier CSV local.

    Comportement :
        - Si `DEST` existe et est non vide : on le réutilise.
        - Sinon : on télécharge depuis `URL` en écrivant d'abord dans un fichier
          temporaire (.part), puis on remplace atomiquement le fichier final.

    Returns:
        Path: le chemin absolu du CSV local (`DEST`).

    Raises:
        Exception: en cas d'erreur réseau (HTTP, timeout) ou d'écriture disque.
    """
    DEST.parent.mkdir(parents=True, exist_ok=True)
    if DEST.exists() and DEST.stat().st_size > 0:
        print(f"[OK] CSV déjà présent : {DEST}")
        return DEST

    print("[INFO] Installation du CSV en cours... (merci de patienter)")
    tmp = DEST.with_suffix(".part")
    try:
        with requests.get(URL, stream=True, timeout=60) as r:
            r.raise_for_status()
            with tmp.open("wb") as f:
                for chunk in r.iter_content(chunk_size=1_048_576):  # 1 MiB
                    if chunk:
                        f.write(chunk)
        tmp.replace(DEST)  # écriture atomique
        print(f"[OK] Installation terminée : {DEST}")
        return DEST
    except Exception:
        tmp.unlink(missing_ok=True)
        if DEST.exists() and DEST.stat().st_size == 0:
            DEST.unlink(missing_ok=True)
        raise


if __name__ == "__main__":
    ensure_effectifs_csv()
