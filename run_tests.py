"""
Script de développement multiplateforme pour le projet.

Ce script fournit une interface simple pour toutes les tâches de développement :
tests, installation des dépendances, lancement de l'application, nettoyage.

Usage:
    python run_tests.py test                # Tous les tests
    python run_tests.py test --unit         # Tests unitaires seulement
    python run_tests.py test --cov          # Avec couverture de code
    python run_tests.py install             # Installer les dépendances
    python run_tests.py run                 # Lancer l'application
    python run_tests.py clean               # Nettoyer les fichiers temporaires
    python run_tests.py help                # Afficher l'aide
"""

import sys
import subprocess
import shutil
import webbrowser
from pathlib import Path


def run_command(cmd: list[str]) -> int:
    """
    Exécute une commande et retourne le code de sortie.
    
    Args:
        cmd: Liste des arguments de la commande
        
    Returns:
        Code de sortie (0 = succès, non-0 = échec)
    """
    print(f"🔧 Exécution: {' '.join(cmd)}\n")
    result = subprocess.run(cmd)
    return result.returncode


def show_help():
    """Affiche l'aide complète."""
    print(__doc__)
    print("\n🔧 Commandes disponibles:\n")
    print("  TESTS:")
    print("    test                Exécuter tous les tests")
    print("    test --unit         Exécuter uniquement les tests unitaires (rapides)")
    print("    test --integration  Exécuter les tests d'intégration")
    print("    test --cov          Générer un rapport de couverture")
    print("    test --html         Générer un rapport HTML de couverture")
    print("    test --failed       Ré-exécuter les tests qui ont échoué")
    print("    test --verbose      Mode verbeux")
    print("    test --pdb          Ouvrir le debugger en cas d'échec")
    print()
    print("  INSTALLATION:")
    print("    install             Installer les dépendances du projet")
    print("    install --dev       Installer les dépendances de développement")
    print()
    print("  APPLICATION:")
    print("    run                 Lancer l'application Dash")
    print()
    print("  MAINTENANCE:")
    print("    clean               Nettoyer les fichiers temporaires")
    print()
    print("  AIDE:")
    print("    help                Afficher ce message d'aide")
    print()


def install_dependencies(dev=False):
    """Installe les dépendances du projet."""
    print("📦 Installation des dépendances..." + (" de développement" if dev else ""))
    
    cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    result = subprocess.run(cmd)
    
    if dev:
        print("\n📦 Installation des outils de développement...")
        dev_packages = ["pytest", "pytest-cov", "pytest-mock", "pytest-asyncio", "pytest-timeout"]
        cmd = [sys.executable, "-m", "pip", "install"] + dev_packages
        result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n✅ Installation terminée!")
    else:
        print("\n❌ Erreur lors de l'installation.")
    
    return result.returncode


def run_application():
    """Lance l'application Dash."""
    print("🚀 Lancement de l'application Dash...\n")
    cmd = [sys.executable, "main.py"]
    result = subprocess.run(cmd)
    return result.returncode


def clean_temp_files():
    """Nettoie les fichiers temporaires du projet."""
    print("🧹 Nettoyage des fichiers temporaires...\n")
    
    cleaned = []
    
    # Suppression des __pycache__
    for pycache in Path(".").rglob("__pycache__"):
        shutil.rmtree(pycache, ignore_errors=True)
        cleaned.append(f"  ✓ {pycache}")
    
    # Suppression des .pyc
    for pyc in Path(".").rglob("*.pyc"):
        pyc.unlink(missing_ok=True)
        cleaned.append(f"  ✓ {pyc}")
    
    # Suppression du dossier htmlcov
    htmlcov = Path("htmlcov")
    if htmlcov.exists():
        shutil.rmtree(htmlcov, ignore_errors=True)
        cleaned.append("  ✓ htmlcov/")
    
    # Suppression du dossier .pytest_cache
    pytest_cache = Path(".pytest_cache")
    if pytest_cache.exists():
        shutil.rmtree(pytest_cache, ignore_errors=True)
        cleaned.append("  ✓ .pytest_cache/")
    
    # Suppression du fichier .coverage
    coverage_file = Path(".coverage")
    if coverage_file.exists():
        coverage_file.unlink(missing_ok=True)
        cleaned.append("  ✓ .coverage")
    
    if cleaned:
        for item in cleaned[:10]:  # Afficher max 10 items
            print(item)
        if len(cleaned) > 10:
            print(f"  ... et {len(cleaned) - 10} autres fichiers")
    
    print("\n✅ Nettoyage terminé!")
    return 0


def run_tests(test_args):
    """Exécute les tests avec les arguments spécifiés."""
    # Construction de la commande pytest de base
    cmd = ["pytest"]
    
    # Application des options
    if "--unit" in test_args:
        cmd.extend(["-m", "unit"])
        test_args.remove("--unit")
    
    if "--integration" in test_args:
        cmd.extend(["-m", "integration"])
        test_args.remove("--integration")
    
    if "--cov" in test_args:
        cmd.extend(["--cov=src", "--cov-report=term-missing"])
        test_args.remove("--cov")
    
    if "--html" in test_args:
        cmd.extend(["--cov=src", "--cov-report=html"])
        test_args.remove("--html")
        print("📊 Le rapport HTML sera généré dans htmlcov/index.html\n")
    
    if "--verbose" in test_args:
        cmd.append("-v")
        test_args.remove("--verbose")
    
    if "--slow" not in test_args:
        # Par défaut, exclure les tests lents sauf si --slow est spécifié
        if "-m" not in cmd:
            cmd.extend(["-m", "not slow"])
    else:
        test_args.remove("--slow")
    
    if "--failed" in test_args:
        cmd.append("--lf")  # last-failed
        test_args.remove("--failed")
    
    if "--pdb" in test_args:
        cmd.append("--pdb")
        test_args.remove("--pdb")
    
    # Ajouter les arguments restants
    cmd.extend(test_args)
    
    # Exécution des tests
    exit_code = run_command(cmd)
    
    # Ouvrir le rapport HTML si généré
    if "--cov-report=html" in cmd:
        htmlcov_index = Path("htmlcov/index.html")
        if htmlcov_index.exists():
            print("\n📊 Ouverture du rapport de couverture...")
            webbrowser.open(htmlcov_index.absolute().as_uri())
    
    # Message de fin
    if exit_code == 0:
        print("\n✅ Tous les tests ont réussi!")
    else:
        print(f"\n❌ Des tests ont échoué (code: {exit_code}).")
    
    return exit_code


def main():
    """Point d'entrée principal du script."""
    args = sys.argv[1:]
    
    # Pas d'arguments ou aide demandée
    if not args or args[0] in ["help", "--help", "-h"]:
        show_help()
        return 0
    
    # Récupération de la commande principale
    command = args[0].lower()
    remaining_args = args[1:]
    
    # Exécution de la commande appropriée
    if command == "test":
        return run_tests(remaining_args)
    
    elif command == "install":
        dev_mode = "--dev" in remaining_args
        return install_dependencies(dev=dev_mode)
    
    elif command == "run":
        return run_application()
    
    elif command == "clean":
        return clean_temp_files()
    
    else:
        print(f"❌ Commande inconnue: {command}")
        print("Utilisez 'python run_tests.py help' pour voir les commandes disponibles.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
