from dash import html

def header(title="Mon Dashboard"):
    """Composant d'en-tête du dashboard."""
    return html.Header(
        children=[
            html.H1(title, style={"textAlign": "center", "margin": "20px 0"}),
        ],
        style={"backgroundColor": "#1E90FF", "color": "white", "padding": "10px"},
    )
