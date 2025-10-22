"""
Package: pages
--------------
Contient les différentes pages du dashboard :
- page d'accueil
- page "À propos"
- pages simples et complexes
"""

#from .home import *
#from .about import *
from .simple_page import *
#from .more_complex_page import *

__all__ = [
    "home",
    "about",
    "simple_page",
    "more_complex_page",
]
