import plotly.graph_objects as go
import dash_mantine_components as dmc
from dash import html

# --------------------------------------------------
# COLOR PALETTE & DESIGN SYSTEM
# --------------------------------------------------

BG = "#101827"
PANEL = "#172438"
PANEL_ALT = "#131E30"
BORDER = "#263449"
TEXT = "#F8FAFC"
MUTED = "#94A3B8"
ACCENT = "#84CC16"

# Positional and cluster accents
POSITION_COLORS = {
    "DF": "#38BDF8",  # Defender Cyan / Blue
    "MF": "#A3E635",  # Midfielder Lime
    "FW": "#F59E0B",  # Forward Amber / Orange
}

POSITION_NAMES = {
    "DF": "Defenders",
    "MF": "Midfielders",
    "FW": "Forwards",
    "ALL": "All Positions",
}

ATTRIBUTE_COLUMNS = {
    "Finishing": "Finishing_Score",
    "Creativity": "Creativity_Score",
    "Passing": "Passing_Score",
    "Progression": "Progression_Score",
    "Defending": "Defending_Score",
    "Ball Security": "BallSecurity_Score",
    "Aerial": "Aerial_Score",
}

CLUSTER_COLORS = [
    "#38BDF8",  # Cyan
    "#84CC16",  # Lime
    "#F59E0B",  # Amber
    "#EC4899",  # Pink
]


# --------------------------------------------------
# CHART STYLING HELPER
# --------------------------------------------------

def style_figure(fig, height=350, show_grid=True):
    """
    Applies consistent SCOUT dark navy / lime styling to Plotly figures.
    """
    fig.update_layout(
        height=height,
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        font=dict(color=TEXT, family="Inter, sans-serif"),
        title=dict(
            font=dict(color=TEXT, size=15, family="Inter, sans-serif"),
            subtitle=dict(font=dict(color=MUTED, size=12, family="Inter, sans-serif")),
        ),
        margin=dict(l=35, r=25, t=45, b=30),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=MUTED, size=11),
        ),
        xaxis=dict(
            gridcolor=BORDER if show_grid else "rgba(0,0,0,0)",
            zerolinecolor=BORDER if show_grid else "rgba(0,0,0,0)",
            tickfont=dict(color=MUTED, size=11),
            title=dict(font=dict(color=MUTED, size=12)),
        ),
        yaxis=dict(
            gridcolor=BORDER if show_grid else "rgba(0,0,0,0)",
            zerolinecolor=BORDER if show_grid else "rgba(0,0,0,0)",
            tickfont=dict(color=TEXT, size=11),
            title=dict(font=dict(color=MUTED, size=12)),
        ),
        hoverlabel=dict(
            bgcolor=PANEL,
            font_size=12,
            font_family="Inter, sans-serif",
            font_color=TEXT,
            bordercolor=BORDER,
        ),
    )
    return fig


# --------------------------------------------------
# UI COMPONENT HELPERS
# --------------------------------------------------

def create_page_header(title, subtitle=None, badge_text=None):
    """
    Creates a standardized page title header with clean typography.
    """
    elements = [
        dmc.Title(title, order=1, c="white"),
    ]
    if subtitle:
        elements.append(
            dmc.Text(subtitle, size="sm", c="dimmed", mt=6)
        )

    return dmc.Group(
        [
            dmc.Box(elements),
            dmc.Badge(badge_text, color="lime", variant="light") if badge_text else html.Div(),
        ],
        justify="space-between",
        align="flex-start",
        mb="xl",
    )


def create_metric_card(title, value, description=None, color=None):
    """
    Creates a KPI metric card with consistent styling.
    """
    return dmc.Card(
        children=[
            dmc.Text(title.upper(), size="xs", fw=700, c="dimmed"),
            dmc.Title(str(value), order=2, mt=8, c=color if color else "white"),
            dmc.Text(description, size="xs", c="dimmed", mt=4) if description else html.Div(),
        ],
        withBorder=True,
        radius="md",
        p="lg",
        style={
            "backgroundColor": PANEL,
            "borderColor": BORDER,
            "height": "100%",
        },
    )


def create_section_card(children, title=None, subtitle=None, extra_header=None, style=None):
    """
    Creates a container card for a chart or section.
    """
    card_children = []

    if title or extra_header:
        header_box = dmc.Box([
            dmc.Title(title, order=4, c="white") if title else html.Div(),
            dmc.Text(subtitle, size="xs", c="dimmed", mt=2) if subtitle else html.Div(),
        ])
        if extra_header:
            card_children.append(
                dmc.Group([header_box, extra_header], justify="space-between", align="center", wrap="wrap", mb="md")
            )
        else:
            card_children.append(dmc.Box(header_box, mb="md"))

    if isinstance(children, list):
        card_children.extend(children)
    else:
        card_children.append(children)

    base_style = {
        "backgroundColor": PANEL,
        "borderColor": BORDER,
    }
    if style:
        base_style.update(style)

    return dmc.Card(
        card_children,
        withBorder=True,
        radius="md",
        p="lg",
        style=base_style,
    )


def position_percentile_warning():
    """
    Returns an analytical alert notice clarifying position-relative percentiles.
    """
    return dmc.Alert(
        "Analytical Notice: Attribute scores are position-relative percentiles (0–100) benchmarked against each player's specific position peer group. Comparisons across different positions reflect relative standing within that position, not absolute equivalence.",
        title="Position-Relative Percentile Benchmarking",
        color="yellow",
        variant="light",
        radius="md",
        p="xs",
        style={
            "backgroundColor": "rgba(245, 158, 11, 0.08)",
            "borderColor": "rgba(245, 158, 11, 0.25)",
            "color": "#F8FAFC",
        },
    )
