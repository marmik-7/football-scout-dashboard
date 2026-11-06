import plotly.graph_objects as go
import dash_mantine_components as dmc
from dash import html

# --------------------------------------------------
# COLOR PALETTE & DESIGN SYSTEM (SCOUT PITCH BLACK)
# --------------------------------------------------

BG = "#090D14"  # Deep pitch black obsidian canvas
PANEL = "#0F172A"  # Slate-900 surface for cards and charts
PANEL_ALT = "#0B1120"  # Deeper panel surface for sub-elements
BORDER = "rgba(255, 255, 255, 0.08)"  # Clean 1px hairline border
BORDER_SUBTLE = "rgba(255, 255, 255, 0.04)"
TEXT = "#F8FAFC"  # High-contrast white
MUTED = "#94A3B8"  # Slate-400 secondary text
SUBTLE = "#64748B"  # Slate-500 micro-labels
ACCENT = "#10B981"  # Pitch Emerald (primary sports-tech accent)
ACCENT_BG = "rgba(16, 185, 129, 0.10)"
ACCENT_BORDER = "rgba(16, 185, 129, 0.25)"

# Positional and cluster accents
POSITION_COLORS = {
    "DF": "#38BDF8",  # Defender Sky Blue
    "MF": "#10B981",  # Midfielder Pitch Emerald
    "FW": "#F59E0B",  # Forward Amber
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
    "#38BDF8",  # Sky Blue
    "#10B981",  # Pitch Emerald
    "#F59E0B",  # Amber
    "#EC4899",  # Pink
]


# --------------------------------------------------
# STANDARDIZED 5-TIER SCOUTING SCALE
# --------------------------------------------------

def get_percentile_tier(score):
    """
    Standardized 5-tier professional scouting classification:
    - 90–100: Elite (#10B981 / Pitch Emerald)
    - 75–89:  Strong (#38BDF8 / Sky Blue)
    - 50–74:  Average (#94A3B8 / Slate)
    - 25–49:  Developing (#F59E0B / Amber)
    - 0–24:   Concern (#F43F5E / Crimson)
    """
    try:
        val = float(score)
    except (TypeError, ValueError):
        val = 50.0

    if val >= 90:
        return {"tier": "Elite", "color": "#10B981", "badge_color": "teal"}
    elif val >= 75:
        return {"tier": "Strong", "color": "#38BDF8", "badge_color": "cyan"}
    elif val >= 50:
        return {"tier": "Average", "color": "#94A3B8", "badge_color": "gray"}
    elif val >= 25:
        return {"tier": "Developing", "color": "#F59E0B", "badge_color": "yellow"}
    else:
        return {"tier": "Concern", "color": "#F43F5E", "badge_color": "red"}


# --------------------------------------------------
# CHART STYLING HELPER (HIGH-DENSITY FLAT SLATE)
# --------------------------------------------------

def style_figure(fig, height=350, show_grid=True):
    """
    Applies consistent SCOUT pitch black / slate styling to Plotly figures.
    """
    fig.update_layout(
        height=height,
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        font=dict(color=TEXT, family="Inter, -apple-system, BlinkMacSystemFont, sans-serif"),
        title=dict(
            font=dict(color="#FFFFFF", size=14, family="Inter, sans-serif", weight=600),
            subtitle=dict(font=dict(color=MUTED, size=11, family="Inter, sans-serif")),
        ),
        margin=dict(l=35, r=25, t=40, b=30),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=MUTED, size=11),
        ),
        xaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.05)" if show_grid else "rgba(0,0,0,0)",
            zerolinecolor="rgba(255, 255, 255, 0.07)" if show_grid else "rgba(0,0,0,0)",
            tickfont=dict(color=MUTED, size=10),
            title=dict(font=dict(color=MUTED, size=11)),
        ),
        yaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.05)" if show_grid else "rgba(0,0,0,0)",
            zerolinecolor="rgba(255, 255, 255, 0.07)" if show_grid else "rgba(0,0,0,0)",
            tickfont=dict(color=MUTED, size=10),
            title=dict(font=dict(color=MUTED, size=11)),
        ),
        hoverlabel=dict(
            bgcolor="#1E293B",
            font_size=11,
            font_family="Inter, sans-serif",
            font_color="#FFFFFF",
            bordercolor="rgba(255, 255, 255, 0.15)",
        ),
    )
    return fig


# --------------------------------------------------
# UI COMPONENT HELPERS
# --------------------------------------------------

def create_page_header(title, subtitle=None, badge_text=None):
    """
    Creates an elite, minimalist header with modern typography.
    """
    badge_el = None
    if badge_text:
        badge_el = dmc.Badge(
            badge_text,
            color="teal",
            variant="light",
            size="sm",
            style={
                "letterSpacing": "0.6px",
                "fontSize": "10px",
                "fontWeight": 700,
                "textTransform": "uppercase",
                "backgroundColor": ACCENT_BG,
                "color": "#34D399",
                "borderColor": ACCENT_BORDER,
            },
        )

    elements = [
        dmc.Group([
            dmc.Title(title, order=2, c="#FFFFFF", style={"fontWeight": 700, "letterSpacing": "-0.5px", "fontSize": "22px"}),
            badge_el if badge_el else html.Div(),
        ], gap="sm", align="center"),
    ]
    if subtitle:
        elements.append(
            dmc.Text(subtitle, size="xs", c=MUTED, mt=4, style={"lineHeight": 1.5, "maxWidth": "850px"})
        )

    return dmc.Box(elements, mb="lg")


def create_metric_card(title, value, description=None, color=None):
    """
    Creates a minimalist KPI metric card with clean typography and hairline borders.
    """
    return dmc.Card(
        children=[
            dmc.Text(title.upper(), size="10px", fw=700, c=SUBTLE, style={"letterSpacing": "0.8px"}),
            dmc.Title(
                str(value),
                order=2,
                mt=4,
                c=color if color else "#FFFFFF",
                style={"fontVariantNumeric": "tabular-nums", "fontWeight": 700, "letterSpacing": "-0.5px", "fontSize": "24px"},
            ),
            dmc.Text(description, size="xs", c=MUTED, mt=4, style={"lineHeight": 1.3}) if description else html.Div(),
        ],
        withBorder=True,
        radius="sm",
        p="md",
        style={
            "backgroundColor": PANEL,
            "borderColor": BORDER,
            "boxShadow": "none",
            "height": "100%",
        },
    )


def create_section_card(children, title=None, subtitle=None, extra_header=None, style=None):
    """
    Creates an architectural panel with subtle hairline border and flat surface.
    """
    card_children = []

    if title or extra_header is not None:
        header_box = dmc.Box([
            dmc.Title(title, order=4, c="#FFFFFF", style={"fontWeight": 600, "letterSpacing": "-0.3px", "fontSize": "15px"}) if title else html.Div(),
            dmc.Text(subtitle, size="xs", c=MUTED, mt=2, style={"lineHeight": 1.4}) if subtitle else html.Div(),
        ])
        if extra_header is not None:
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
        "boxShadow": "none",
    }
    if style:
        base_style.update(style)

    return dmc.Card(
        card_children,
        withBorder=True,
        radius="sm",
        p="md",
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
        radius="sm",
        p="sm",
        style={
            "backgroundColor": "rgba(245, 158, 11, 0.05)",
            "borderColor": "rgba(245, 158, 11, 0.20)",
            "color": "#F8FAFC",
            "fontSize": "12px",
        },
    )
