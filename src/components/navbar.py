from dash import html

def navbar():
    """Barre de navigation simple."""
    nav_links = [
        html.A("Accueil", href="/", style={"marginRight": "20px"}),
        html.A("Page simple", href="/simple", style={"marginRight": "20px"}),
        html.A("À propos", href="/about"),
    ]

    return html.Nav(
        children=nav_links,
        style={
            "display": "flex",
            "justifyContent": "center",
            "alignItems": "center",
            "backgroundColor": "#f8f9fa",
            "padding": "10px",
            "borderBottom": "1px solid #ddd",
        },
    )