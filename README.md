# Projet — Effectifs & prévalence (data.ameli.fr)

## Données
- Source CSV (Open Data Assurance Maladie) :  
  `https://data.ameli.fr/api/explore/v2.1/catalog/datasets/effectifs/exports/csv?use_labels=true`  
- Enregistrements par (année, pathologie, âge, sexe, territoire) avec `Ntop` (effectifs), `Npop`, `prev`.

## Objectif
- **MVP** : télécharger le CSV s’il manque, créer une base **SQLite** locale et **importer** la table `effectifs`.  
- Prochaine étape : vues analytiques + dashboard (histogrammes & carte).

## Lancer
```bash
git clone <url-du-depot>
cd <repo>
python -m pip install -r requirements.txt
python main.py
