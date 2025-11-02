"""
Package: components
-------------------
Ce module regroupe les différents composants du dashboard : 
en-tête, pied de page, barre de navigation et icônes.
"""

from .header import *
from .footer import *
from .navbar import *
from .icons import *

__all__ = [
    "header",
    "footer",
    "navbar",
    "icons",
]
