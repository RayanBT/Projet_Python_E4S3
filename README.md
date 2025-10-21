# Projet_Python_E4S3

Projet — Effectifs & prévalence (data.ameli.fr)

Données
Source CSV (Open Data Assurance Maladie) :
https://data.ameli.fr/api/explore/v2.1/catalog/datasets/effectifs/exports/csv?use_labels=true

Enregistrements par (année, pathologie, âge, sexe, territoire) avec Ntop (effectifs), Npop, prev.

Objectif
MVP : télécharger le CSV s’il manque, créer une SQLite locale et importer la table effectifs.

Prochaine étape : vues analytiques + dashboard (histogrammes & carte).

Lancer
git clone <url-du-depot>
cd <repo>
python -m pip install -r requirements.txt
python main.py
Structure
.
├── main.py
├── db/
│   ├── models.py    # mapping SQLAlchemy
│   ├── schema.py    # modèles Pydantic
│   └── utils.py     # import CSV -> SQLite, helpers
└── data/
    ├── effectifs.csv       # téléchargé auto si absent
    └── effectifs.sqlite3   # base locale
Notes
Volume important (~5,2 M lignes) : prévoir un peu d’espace disque.

Certaines valeurs vides sont normalisées en None (validation Pydantic).

Vérifier licence/mentions sur la page data.ameli.fr.




