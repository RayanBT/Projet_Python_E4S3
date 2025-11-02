"""Page d'affichage du loader pendant l'initialisation des donnees."""

from __future__ import annotations

from typing import Iterable

from dash import html

STEP_FLOW = [
    "Initialisation des donnees",
    "Telechargement du CSV",
    "Initialisation de la base SQLite",
    "Verification des donnees",
    "Initialisation terminee",
]


def _progress_ratio(step: str | None, success: bool) -> float:
    """Calcule la progression globale a partir de l'etape courante.

    Args:
        step (str | None): Libelle de l'etape en cours.
        success (bool): Indicateur de fin reussie.

    Returns:
        float: Ratio compris entre 0.0 et 1.0 representant la progression.
    """
    if success:
        return 1.0
    if not step or step not in STEP_FLOW:
        return 0.0
    index = STEP_FLOW.index(step)
    ratio = (index + 1) / len(STEP_FLOW)
    return min(max(ratio, 0.0), 1.0)


def render_setup_page(
    messages: Iterable[str],
    current_step: str | None,
    *,
    completed: bool,
    success: bool,
) -> html.Div:
    """Construit la page affichee pendant l'initialisation des donnees.

    Args:
        messages (Iterable[str]): Historique des messages emises.
        current_step (str | None): Etape en cours selon l'etat partage.
        completed (bool): Indique si la sequence est terminee.
        success (bool): Indique si toutes les etapes ont reussi.

    Returns:
        dash.html.Div: Contenu Dash a afficher durant l'attente.
    """
    messages_list = list(messages)[-50:]
    seen_steps = [
        msg[7:].strip()
        for msg in messages_list
        if msg.startswith("[STEP] ")
    ]
    last_seen_step = seen_steps[-1] if seen_steps else None
    clean_current_step = current_step or last_seen_step
    progress_ratio = _progress_ratio(clean_current_step, success)
    progress_percent = int(progress_ratio * 100)

    if not completed:
        status_text = clean_current_step or "Initialisation en cours..."
        help_text = "Merci de patienter pendant la preparation des donnees."
    elif success:
        status_text = "Initialisation terminee."
        help_text = "Redirection vers l'accueil en cours..."
    else:
        status_text = "Une erreur est survenue pendant l'initialisation."
        help_text = (
            clean_current_step
            if clean_current_step and clean_current_step not in STEP_FLOW
            else "Consultez le journal ci-dessous puis relancez l'application."
        )

    progress_bar = html.Div(
        [
            html.Div(
                style={
                    "width": f"{progress_percent}%",
                    "height": "100%",
                    "background": "linear-gradient(90deg,#2d9cdb,#27ae60)",
                    "borderRadius": "999px",
                    "transition": "width 0.6s ease",
                },
            )
        ],
        style={
            "height": "14px",
            "width": "100%",
            "backgroundColor": "#e4e7eb",
            "borderRadius": "999px",
            "overflow": "hidden",
            "boxShadow": "inset 0 1px 3px rgba(0,0,0,0.12)",
        },
    )

    steps_summary = html.Div(
        [
            html.Strong(f"{progress_percent}%"),
            html.Span(
                f" - {clean_current_step or 'Initialisation en cours...'}",
                style={"marginLeft": "8px"},
            ),
        ],
        style={
            "marginTop": "12px",
            "fontSize": "16px",
            "color": "#1f2933",
        },
    )

    def step_prefix(step: str) -> str:
        if success:
            return "[x]"
        if step == clean_current_step and not completed:
            return "[>]"
        if step in seen_steps:
            return "[x]"
        return "[ ]"

    step_list = html.Div(
        [
            html.Div(
                f"{step_prefix(step)} {step}",
                style={
                    "padding": "4px 0",
                    "color": "#1f2933" if step in seen_steps or success else "#7b8794",
                    "fontWeight": "600" if step == clean_current_step else "400",
                },
            )
            for step in STEP_FLOW
        ],
        style={"marginTop": "16px"},
    )

    content = html.Div(
        [
            html.H2(
                "Preparation des donnees",
                style={"marginBottom": "16px", "color": "#102a43"},
            ),
            html.P(status_text, style={"fontSize": "18px", "color": "#334155"}),
            html.P(help_text, style={"marginBottom": "24px", "color": "#52606d"}),
            progress_bar,
            steps_summary,
            step_list,
        ],
        style={
            "maxWidth": "640px",
            "margin": "60px auto",
            "padding": "32px",
            "backgroundColor": "white",
            "borderRadius": "12px",
            "boxShadow": "0 12px 32px rgba(15,23,42,0.12)",
            "border": "1px solid #e4e7eb",
        },
    )

    return html.Div(
        content,
        style={
            "background": "linear-gradient(135deg,#f3f4f6,#e0f2f1)",
            "minHeight": "100vh",
            "padding": "40px 16px",
        },
    )
