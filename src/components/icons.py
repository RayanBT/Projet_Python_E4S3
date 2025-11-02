"""Composants d'icônes utilisant des emojis modernes."""

from dash import html


def icon_home(class_name="icon"):
    """Icône Maison/Accueil."""
    return html.Span("🏠", className=class_name)


def icon_chart_bar(class_name="icon"):
    """Icône Graphique en barres."""
    return html.Span("📊", className=class_name)


def icon_chart_line(class_name="icon"):
    """Icône Graphique en ligne."""
    return html.Span("📈", className=class_name)


def icon_info(class_name="icon"):
    """Icône Information."""
    return html.Span("ℹ️", className=class_name)


def icon_map(class_name="icon"):
    """Icône Carte."""
    return html.Span("🗺️", className=class_name)


def icon_video(class_name="icon-large"):
    """Icône Vidéo."""
    return html.Span("🎥", className=class_name, style={'color': '#95a5a6'})


def icon_pin(class_name="icon"):
    """Icône Épingle/Pin."""
    return html.Span("📌", className=class_name)


def icon_check(class_name="icon"):
    """Icône Check/Validation."""
    return html.Span("✅", className=class_name)


def icon_warning(class_name="icon"):
    """Icône Avertissement."""
    return html.Span("⚠️", className=class_name)


def icon_close(class_name="icon"):
    """Icône Fermer/Erreur."""
    return html.Span("❌", className=class_name)


def icon_refresh(class_name="icon"):
    """Icône Actualiser/Rafraîchir."""
    return html.Span("🔄", className=class_name)
