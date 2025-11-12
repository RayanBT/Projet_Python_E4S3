"""Composants d'icônes utilisant des emojis modernes."""

from dash import html


def icon_home(class_name: str = "icon") -> html.Span:
    """Icône Maison/Accueil."""
    return html.Span("🏠", className=class_name)


def icon_chart_bar(class_name: str = "icon") -> html.Span:
    """Icône Graphique en barres."""
    return html.Span("📊", className=class_name)


def icon_chart_line(class_name: str = "icon") -> html.Span:
    """Icône Graphique en ligne."""
    return html.Span("📈", className=class_name)


def icon_info(class_name: str = "icon") -> html.Span:
    """Icône Information."""
    return html.Span("ℹ️", className=class_name)


def icon_map(class_name: str = "icon") -> html.Span:
    """Icône Carte."""
    return html.Span("🗺️", className=class_name)


def icon_video(class_name: str = "icon-large") -> html.Span:
    """Icône Vidéo."""
    return html.Span("🎥", className=class_name, style={'color': '#95a5a6'})


def icon_pin(class_name: str = "icon") -> html.Span:
    """Icône Épingle/Pin."""
    return html.Span("📌", className=class_name)


def icon_chart_spider(class_name: str = "icon") -> html.Span:
    """Icône Graphique en toile d'araignée/radar."""
    return html.Span("🕸️", className=class_name)


def icon_pie_chart(class_name: str = "icon") -> html.Span:
    """Icône Graphique en camembert."""
    return html.Span("🧀", className=class_name)

