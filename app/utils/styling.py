import plotly.graph_objects as go
import dash_mantine_components as dmc
from dash import html

# --------------------------------------------------
# DESIGN SYSTEM TOKENS (SCOUT LINEAR × STATSBOMB)
# Supports complete Dark & Light theme switching
# --------------------------------------------------

THEME_TOKENS = {
    "dark": {
        "bg_canvas": "#080C12",
        "bg_surface_primary": "#111827",
        "bg_surface_secondary": "#1E293B",
        "bg_surface_elevated": "#1E293B",
        "border_hairline": "rgba(255, 255, 255, 0.08)",
        "border_subtle": "rgba(255, 255, 255, 0.04)",
        "border_focus": "#10B981",
        "text_primary": "#F8FAFC",
        "text_secondary": "#CBD5E1",
        "text_muted": "#94A3B8",
        "accent_emerald": "#10B981",
        "accent_emerald_dim": "rgba(16, 185, 129, 0.12)",
        "accent_emerald_border": "rgba(16, 185, 129, 0.25)",
        "card_bg": "#111827",
    },
    "light": {
        "bg_canvas": "#F8FAFC",
        "bg_surface_primary": "#FFFFFF",
        "bg_surface_secondary": "#F1F5F9",
        "bg_surface_elevated": "#FFFFFF",
        "border_hairline": "rgba(15, 23, 42, 0.08)",
        "border_subtle": "rgba(15, 23, 42, 0.04)",
        "border_focus": "#059669",
        "text_primary": "#0F172A",
        "text_secondary": "#334155",
        "text_muted": "#475569",
        "accent_emerald": "#059669",
        "accent_emerald_dim": "rgba(5, 150, 105, 0.08)",
        "accent_emerald_border": "rgba(5, 150, 105, 0.20)",
        "card_bg": "#FFFFFF",
    },
}

# CSS variable references for seamless CSS-driven theme reactivity
BG = "var(--scout-bg, #080C12)"
PANEL = "var(--scout-surface-primary, #111827)"
PANEL_ALT = "var(--scout-surface-secondary, #1E293B)"
BORDER = "var(--scout-border, rgba(255, 255, 255, 0.08))"
BORDER_SUBTLE = "var(--scout-border-subtle, rgba(255, 255, 255, 0.04))"
TEXT = "var(--scout-text-primary, #F8FAFC)"
MUTED = "var(--scout-text-secondary, #CBD5E1)"
SUBTLE = "var(--scout-text-muted, #94A3B8)"
ACCENT = "var(--scout-accent, #10B981)"
ACCENT_BG = "var(--scout-accent-dim, rgba(16, 185, 129, 0.12))"
ACCENT_BORDER = "var(--scout-accent-border, rgba(16, 185, 129, 0.25))"

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
        return {"tier": "Average", "color": "var(--scout-text-secondary)", "badge_color": "gray"}
    elif val >= 25:
        return {"tier": "Developing", "color": "#F59E0B", "badge_color": "yellow"}
    else:
        return {"tier": "Concern", "color": "#F43F5E", "badge_color": "red"}


# --------------------------------------------------
# PLOTLY FIGURE STYLING (THEME-AWARE)
# --------------------------------------------------

def style_figure(fig, height=350, show_grid=True, theme="dark"):
    """
    Applies consistent theme-aware styling to Plotly figures.
    Adapts seamlessly between dark and light modes.
    """
    is_light = (theme == "light")
    
    paper_bg = "rgba(0, 0, 0, 0)"
    plot_bg = "rgba(0, 0, 0, 0)"
    text_color = "#0F172A" if is_light else "#F8FAFC"
    muted_color = "#475569" if is_light else "#CBD5E1"
    grid_color = "rgba(15, 23, 42, 0.08)" if is_light else "rgba(255, 255, 255, 0.06)"
    zeroline_color = "rgba(15, 23, 42, 0.12)" if is_light else "rgba(255, 255, 255, 0.08)"
    hover_bg = "#FFFFFF" if is_light else "#1E293B"
    hover_text = "#0F172A" if is_light else "#FFFFFF"
    hover_border = "#94A3B8" if is_light else "rgba(255, 255, 255, 0.15)"

    fig.update_layout(
        height=height,
        paper_bgcolor=paper_bg,
        plot_bgcolor=plot_bg,
        font=dict(color=text_color, family="'Twemoji Country Flags', Inter, -apple-system, BlinkMacSystemFont, sans-serif"),
        title=dict(
            font=dict(color=text_color, size=14, family="'Twemoji Country Flags', Inter, sans-serif", weight=600),
            subtitle=dict(font=dict(color=muted_color, size=11, family="'Twemoji Country Flags', Inter, sans-serif")),
        ),
        margin=dict(l=35, r=25, t=40, b=30),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=muted_color, size=11),
        ),
        xaxis=dict(
            gridcolor=grid_color if show_grid else "rgba(0,0,0,0)",
            zerolinecolor=zeroline_color if show_grid else "rgba(0,0,0,0)",
            tickfont=dict(color=muted_color, size=10),
            title=dict(font=dict(color=muted_color, size=11)),
        ),
        yaxis=dict(
            gridcolor=grid_color if show_grid else "rgba(0,0,0,0)",
            zerolinecolor=zeroline_color if show_grid else "rgba(0,0,0,0)",
            tickfont=dict(color=muted_color, size=10),
            title=dict(font=dict(color=muted_color, size=11)),
        ),
        hoverlabel=dict(
            bgcolor=hover_bg,
            font_size=11,
            font_family="'Twemoji Country Flags', Inter, sans-serif",
            font_color=hover_text,
            bordercolor=hover_border,
        ),
    )
    return fig


# --------------------------------------------------
# REUSABLE UI COMPONENT HELPERS
# --------------------------------------------------

def create_page_header(title, subtitle=None, badge_text=None, extra=None):
    """
    Creates a refined, minimalist header with Linear-inspired typography.
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
                "color": "var(--scout-accent-light, #34D399)",
                "borderColor": ACCENT_BORDER,
            },
        )

    title_group = dmc.Group([
        dmc.Title(
            title,
            order=2,
            style={
                "fontWeight": 700,
                "letterSpacing": "-0.025em",
                "fontSize": "22px",
                "color": "var(--scout-text-primary, #F8FAFC)",
            },
        ),
        badge_el if badge_el else html.Div(),
    ], gap="sm", align="center")

    elements = [title_group]
    if subtitle:
        elements.append(
            dmc.Text(
                subtitle,
                size="xs",
                mt=4,
                style={
                    "lineHeight": 1.5,
                    "maxWidth": "850px",
                    "color": "var(--scout-text-secondary, #CBD5E1)",
                },
            )
        )

    header_content = dmc.Box(elements)
    
    if extra:
        return dmc.Group([header_content, extra], justify="space-between", align="flex-start", mb="lg", wrap="wrap")

    return dmc.Box(header_content, mb="lg")


def create_metric_card(title, value, description=None, color=None):
    """
    Creates a minimalist KPI metric card with clean typography and hairline borders.
    """
    val_color = color if color and color.startswith("#") else "var(--scout-text-primary, #F8FAFC)"
    if color in ["cyan", "blue"]:
        val_color = "#38BDF8"
    elif color in ["emerald", "teal"]:
        val_color = "#10B981"
    elif color in ["amber", "yellow"]:
        val_color = "#F59E0B"
    elif color in ["crimson", "red"]:
        val_color = "#F43F5E"

    return dmc.Card(
        children=[
            dmc.Text(
                title.upper(),
                size="10px",
                fw=700,
                style={
                    "letterSpacing": "0.8px",
                    "color": "var(--scout-text-muted, #94A3B8)",
                },
            ),
            dmc.Title(
                str(value),
                order=2,
                mt=4,
                style={
                    "fontVariantNumeric": "tabular-nums",
                    "fontWeight": 700,
                    "letterSpacing": "-0.03em",
                    "fontSize": "24px",
                    "color": val_color,
                },
            ),
            dmc.Text(
                description,
                size="xs",
                mt=4,
                style={
                    "lineHeight": 1.35,
                    "color": "var(--scout-text-secondary, #CBD5E1)",
                },
            ) if description else html.Div(),
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
            dmc.Title(
                title,
                order=4,
                style={
                    "fontWeight": 600,
                    "letterSpacing": "-0.02em",
                    "fontSize": "15px",
                    "color": "var(--scout-text-primary, #F8FAFC)",
                },
            ) if title else html.Div(),
            dmc.Text(
                subtitle,
                size="xs",
                mt=2,
                style={
                    "lineHeight": 1.4,
                    "color": "var(--scout-text-secondary, #CBD5E1)",
                },
            ) if subtitle else html.Div(),
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


def create_empty_state(title="No Records Found", description="Try adjusting your filters or search terms.", icon=None):
    """
    Creates an elegant, minimalist empty state component.
    """
    children = []
    if icon:
        children.append(dmc.Text(icon, style={"fontSize": "24px", "opacity": 0.5}))
    children.extend([
        dmc.Text(title, fw=600, size="sm", c="var(--scout-text-primary, #F8FAFC)", mt="xs" if icon else 0),
        dmc.Text(description, size="xs", c="var(--scout-text-secondary, #CBD5E1)", mt=4),
    ])
    return dmc.Box(
        children,
        style={
            "textAlign": "center",
            "padding": "40px 20px",
            "backgroundColor": "transparent",
        },
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
            "color": "var(--scout-text-primary, #F8FAFC)",
            "fontSize": "12px",
        },
    )
