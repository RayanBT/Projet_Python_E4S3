from src.components import header, footer

"""
Package: components
-------------------
Ce module regroupe les différents composants du dashboard : 
en-tête, pied de page, barre de navigation et composants personnalisés.
"""

from .header import *
from .footer import *
from .navbar import *


__all__ = [
    "header",
    "footer",
    "navbar",
]
