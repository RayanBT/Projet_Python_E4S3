from dash import html
from datetime import datetime

def footer():
    """Pied de page du dashboard."""
    current_year = datetime.now().year
    return html.Footer(
        children=[
            html.P(f"© {current_year} - Mon Dashboard | Tous droits réservés", 
                   style={"textAlign": "center", "color": "#888", "fontSize": "14px"})
        ],
        style={"marginTop": "50px", "padding": "20px", "borderTop": "1px solid #ddd"}
    )
