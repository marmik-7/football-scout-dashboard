import dash
from dash import html, dcc, Input, Output, callback
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from app.utils.data_loader import load_data
from app.utils.styling import (
    PANEL,
    BORDER,
    TEXT,
    MUTED,
    SUBTLE,
    ACCENT,
    POSITION_COLORS,
    POSITION_NAMES,
    ATTRIBUTE_COLUMNS,
    create_page_header,
    create_metric_card,
    create_section_card,
    style_figure,
)
from app.utils.player_portraits import render_player_portrait

dash.register_page(__name__, path="/", name="Overview", order=1)

df = load_data()

total_players = len(df)
u21_prospects = int(len(df[(df["Age"] <= 21) & (df["Age"] > 0)]))
clinical_finishers = int(len(df[df.get("G-xG", 0.0) >= 2.0]))
elite_defenders = int(len(df[df.get("Defending_Score", 0.0) >= 80.0]))


def _build_overview_kpi_card(
    title,
    value,
    description,
    criteria,
    kind_label,
    badge_color="gray",
    value_color="var(--scout-text-primary)",
):
    """Build an Overview KPI card distinguishing cohort counts from performance filters."""
    return dmc.Box(
        [
            dmc.Box(
                [
                    dmc.Group(
                        [
                            dmc.Text(
                                title.upper(),
                                size="10.5px",
                                fw=700,
                                style={
                                    "letterSpacing": "0.6px",
                                    "color": "var(--scout-text-secondary)",
                                    "lineHeight": 1.3,
                                    "flex": "1 1 110px",
                                    "minWidth": 0,
                                },
                            ),
                            dmc.Badge(
                                kind_label,
                                color=badge_color,
                                variant="light",
                                size="xs",
                                style={"flexShrink": 0},
                            ),
                        ],
                        justify="space-between",
                        align="center",
                        gap="6px",
                        wrap="wrap",
                    ),
                    dmc.Text(
                        str(value),
                        fw=700,
                        mt=8,
                        style={
                            "fontVariantNumeric": "tabular-nums",
                            "fontWeight": 700,
                            "letterSpacing": "-0.025em",
                            "fontSize": "25px",
                            "lineHeight": 1.15,
                            "color": value_color,
                        },
                    ),
                    dmc.Text(
                        description,
                        size="12px",
                        mt=6,
                        style={
                            "lineHeight": 1.4,
                            "color": "var(--scout-text-secondary)",
                        },
                    ),
                ]
            ),
            dmc.Text(
                criteria,
                className="scout-overview-kpi__criteria",
            ),
        ],
        className="scout-overview-kpi",
    )


def _build_spotlight_card(
    player_name,
    category_label,
    role_label,
    meta_line,
    summary,
    accent_color,
):
    """Build a consistent Spotlight candidate card with player name as primary anchor."""
    return dmc.Box(
        [
            dmc.Box(
                [
                    dmc.Group(
                        [
                            dmc.Badge(
                                category_label,
                                color=accent_color,
                                variant="light",
                                size="xs",
                            ),
                            dmc.Text(
                                role_label,
                                size="11px",
                                fw=600,
                                c="var(--scout-text-muted)",
                            ),
                        ],
                        justify="space-between",
                        align="center",
                        gap="xs",
                    ),
                    dmc.Group(
                        [
                            render_player_portrait(player_name, size=36, radius=6),
                            dmc.Box(
                                [
                                    dmc.Text(
                                        player_name,
                                        fw=700,
                                        c="var(--scout-text-primary)",
                                        style={
                                            "fontSize": "15.5px",
                                            "lineHeight": 1.25,
                                            "letterSpacing": "-0.015em",
                                        },
                                    ),
                                    dmc.Text(
                                        meta_line,
                                        size="xs",
                                        c="var(--scout-text-secondary)",
                                        mt=2,
                                        style={"lineHeight": 1.35},
                                    ),
                                ],
                                style={"minWidth": 0, "flex": 1},
                            ),
                        ],
                        gap="sm",
                        align="center",
                        mt=10,
                        wrap="nowrap",
                    ),
                    dmc.Text(
                        summary,
                        c="var(--scout-text-secondary)",
                        mt=10,
                        style={"fontSize": "12.5px", "lineHeight": 1.48},
                    ),
                ]
            ),
            dmc.Box(
                dcc.Link(
                    dmc.Button(
                        "Open Dossier →",
                        size="xs",
                        variant="subtle",
                        color=accent_color,
                        fw=600,
                        p=0,
                    ),
                    href=f"/player-profile?player={player_name}",
                    style={"textDecoration": "none"},
                ),
                mt=12,
            ),
        ],
        className="scout-spotlight-card",
    )


# --------------------------------------------------
# PAGE LAYOUT
# --------------------------------------------------

layout = dmc.Container(
    [
        create_page_header(
            title="Executive Market Briefing",
            subtitle="Recruitment intelligence, standout breakout talents, clinical finishers, and positional leaders across Europe's top 5 leagues.",
            badge_text="2024–25 SEASON",
        ),

        # RECRUITMENT MARKET KPI CARDS (STRICT LIMIT: 4 CARDS)
        dmc.Grid(
            [
                dmc.GridCol(
                    _build_overview_kpi_card(
                        title="Qualified Talent Pool",
                        value=f"{total_players:,}",
                        description="Eligible outfielders across Europe's Big 5 leagues",
                        criteria="Pool: ≥600 mins played (2024–25)",
                        kind_label="Population",
                        badge_color="gray",
                        value_color="var(--scout-text-primary)",
                    ),
                    span={"base": 12, "sm": 6, "lg": 3},
                ),
                dmc.GridCol(
                    _build_overview_kpi_card(
                        title="U-21 Elite Prospects",
                        value=u21_prospects,
                        description="Emerging young players aged 21 or under in the pool",
                        criteria="Pool filter: Age ≤ 21 • ≥600 mins",
                        kind_label="Age Cohort",
                        badge_color="cyan",
                        value_color="var(--scout-semantic-blue)",
                    ),
                    span={"base": 12, "sm": 6, "lg": 3},
                ),
                dmc.GridCol(
                    _build_overview_kpi_card(
                        title="Clinical Outperformers",
                        value=clinical_finishers,
                        description="Finishers significantly outscoring expected goals",
                        criteria="Performance: G − xG ≥ +2.0 • ≥600 mins",
                        kind_label="Perf. Filter",
                        badge_color="teal",
                        value_color="var(--scout-semantic-emerald)",
                    ),
                    span={"base": 12, "sm": 6, "lg": 3},
                ),
                dmc.GridCol(
                    _build_overview_kpi_card(
                        title="Elite Ball Winners",
                        value=elite_defenders,
                        description="Top 20th-percentile performers in positional defending",
                        criteria="Performance: Defending ≥ 80th pct • ≥600 mins",
                        kind_label="Perf. Filter",
                        badge_color="blue",
                        value_color="var(--scout-semantic-blue)",
                    ),
                    span={"base": 12, "sm": 6, "lg": 3},
                ),
            ],
            gap="md",
            align="stretch",
        ),

        dmc.Space(h=16),

        # MARKET SPOTLIGHTS: HIGH-POTENTIAL RECRUITMENT OPPORTUNITIES
        create_section_card(
            dmc.Grid(
                [
                    dmc.GridCol(
                        _build_spotlight_card(
                            player_name="Lamine Yamal",
                            category_label="Breakthrough",
                            role_label="U-21 Winger",
                            meta_line="Barcelona • La Liga • Age 17",
                            summary="96.1th pct Creativity, elite 1v1 take-on volume and box entries.",
                            accent_color="cyan",
                        ),
                        span={"base": 12, "md": 4},
                    ),
                    dmc.GridCol(
                        _build_spotlight_card(
                            player_name="Erling Haaland",
                            category_label="Clinical Target",
                            role_label="Center Forward",
                            meta_line="Manchester City • Premier League • Age 24",
                            summary="0.85 Gls/90, 98.4th pct Finishing, unmatched box gravity.",
                            accent_color="teal",
                        ),
                        span={"base": 12, "md": 4},
                    ),
                    dmc.GridCol(
                        _build_spotlight_card(
                            player_name="William Saliba",
                            category_label="Defensive Anchor",
                            role_label="Center-Back",
                            meta_line="Arsenal • Premier League • Age 23",
                            summary="97.2th pct Ball Retention, 93.8% pass accuracy, recovery speed.",
                            accent_color="blue",
                        ),
                        span={"base": 12, "md": 4},
                    ),
                ],
                gap="md",
                align="stretch",
            ),
            title="Recruitment Market Spotlights",
            subtitle="Curated standout targets across primary scouting profiles in Europe's top 5 leagues",
        ),

        dmc.Space(h=16),

        # TOP PERFORMERS LEADERBOARD CHART (LAYER 1 PRIMARY VISUAL)
        create_section_card(
            [
                html.Div(id="overview-limitation-notice", style={"marginTop": "2px"}),
                dmc.Space(h=10),
                html.Div(
                    dcc.Graph(
                        id="overview-top-players-chart",
                        config={"displayModeBar": False, "responsive": True},
                        responsive=True,
                    ),
                    className="scout-chart-container",
                ),
            ],
            title="Top Benchmark Performers",
            subtitle="Leading candidates ranked by position-relative percentile scores",
            extra_header=dmc.Box(
                [
                    dmc.Select(
                        id="overview-position-select",
                        data=[
                            {"label": "Forwards (FW)", "value": "FW"},
                            {"label": "Midfielders (MF)", "value": "MF"},
                            {"label": "Defenders (DF)", "value": "DF"},
                            {"label": "All Positions", "value": "ALL"},
                        ],
                        value="FW",
                        size="xs",
                        allowDeselect=False,
                    ),
                    dmc.Select(
                        id="overview-attribute-select",
                        data=[
                            {"label": name, "value": name}
                            for name in ATTRIBUTE_COLUMNS
                        ],
                        value="Finishing",
                        size="xs",
                        allowDeselect=False,
                    ),
                ],
                className="scout-overview-selectors",
            ),
        ),
    ],
    fluid=True,
    p=0,
)


# --------------------------------------------------
# CALLBACK
# --------------------------------------------------

@callback(
    Output("overview-top-players-chart", "figure"),
    Output("overview-limitation-notice", "children"),
    Input("overview-position-select", "value"),
    Input("overview-attribute-select", "value"),
    Input("theme-store", "data"),
)
def update_overview_top_players(position, attribute, theme="dark", *args, **kwargs):
    # Support backward compatibility if someone passes (pos, attr, scout_analyst_mode, theme)
    if args and isinstance(args[0], str) and args[0] in ["dark", "light"]:
        theme = args[0]
    elif theme not in ["dark", "light"] and args:
        theme = args[0]
    theme = theme or "dark"
    if theme not in ["dark", "light"]:
        theme = "dark"
    is_light = (theme == "light")
    text_color = "#0F172A" if is_light else "#F8FAFC"
    muted_color = "#475569" if is_light else "#CBD5E1"
    grid_color = "rgba(15, 23, 42, 0.08)" if is_light else "rgba(128, 128, 128, 0.12)"

    if not attribute or attribute not in ATTRIBUTE_COLUMNS:
        attribute = "Finishing"
    if not position or position not in ["FW", "MF", "DF", "ALL"]:
        position = "FW"

    column = ATTRIBUTE_COLUMNS[attribute]

    if position == "ALL":
        filtered_df = df
        pos_display = "Players (All Positions)"
        title_text = f"Top 10 Candidates (All Positions) — {attribute}"
        cohort_label = f"All Positions (n={len(filtered_df):,})"
        scale_note = "0–100 percentile within each player's own position group"
    else:
        filtered_df = df[df["Pos"] == position]
        pos_display = POSITION_NAMES.get(position, position)
        title_text = f"Top 10 {pos_display} — {attribute}"
        cohort_label = f"{pos_display} only (n={len(filtered_df):,})"
        scale_note = f"0–100 rank strictly within qualified {pos_display.lower()}"

    context_bar = dmc.Box(
        [
            dmc.Group(
                [
                    dmc.Badge("2024–25 Big 5", color="teal", variant="light", size="xs"),
                    dmc.Text(
                        f"Cohort: {cohort_label}",
                        size="xs",
                        fw=600,
                        c="var(--scout-text-primary)",
                    ),
                ],
                gap="xs",
                align="center",
            ),
            dmc.Text(
                f"Eligibility: ≥600 mins played  •  Percentile Scale: {scale_note}",
                size="xs",
                c="var(--scout-text-secondary)",
                style={"lineHeight": 1.4},
            ),
        ],
        className="scout-benchmark-context",
    )

    if position == "ALL":
        notice = dmc.Stack(
            [
                context_bar,
                dmc.Alert(
                    "Analytical Note: Percentile scores are benchmarked within each player's position peer group. Direct comparisons across different positions reflect within-position rank rather than absolute skill parity.",
                    title="Cross-Position Percentile Comparison",
                    color="yellow",
                    variant="light",
                    radius="sm",
                    p="xs",
                    style={
                        "fontSize": "12px",
                        "color": "var(--scout-text-primary)",
                    },
                ),
            ],
            gap="xs",
        )
    else:
        notice = context_bar

    if filtered_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No players found matching the selected criteria.",
            showarrow=False,
            font=dict(color=muted_color, size=13),
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
        )
        fig = style_figure(fig, 390, theme=theme)
        return fig, notice

    top_players = (
        filtered_df.nlargest(10, column)
        .sort_values(column, ascending=True)
        .copy()
    )

    nat_col = "Nation_Display" if "Nation_Display" in top_players.columns else "Nation_Clean"
    bar_color = "#059669" if is_light else "#10B981"
    bar_border = "rgba(4, 120, 87, 0.35)" if is_light else "rgba(52, 211, 153, 0.35)"

    fig = go.Figure(
        go.Bar(
            x=top_players[column],
            y=top_players["Player_Unique"],
            orientation="h",
            marker=dict(
                color=bar_color,
                line=dict(color=bar_border, width=1),
            ),
            text=top_players[column].apply(lambda v: f"{v:.1f}"),
            textposition="outside",
            textfont=dict(
                color=text_color,
                size=11,
                family="'Twemoji Country Flags', Inter, sans-serif",
            ),
            cliponaxis=False,
            customdata=top_players[["Player", "Squad", "Pos", nat_col]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Percentile Score: <b>%{x:.1f}</b><br>"
                "Club: %{customdata[1]}<br>"
                "Position: %{customdata[2]}<br>"
                "Nationality: %{customdata[3]}"
                "<extra></extra>"
            ),
        )
    )

    fig = style_figure(fig, 390, theme=theme)
    fig.update_layout(
        autosize=True,
        title=dict(
            text=title_text,
            x=0,
            xref="container",
            font=dict(color=text_color, size=13),
        ),
        xaxis=dict(
            title=dict(text="Percentile Score (0–100)", font=dict(color=muted_color, size=11)),
            range=[0, 109],
            tickvals=[0, 20, 40, 60, 80, 100],
            gridcolor=grid_color,
            tickfont=dict(color=muted_color, size=10),
        ),
        yaxis=dict(
            title="",
            gridcolor=grid_color,
            tickfont=dict(color=text_color, size=11),
            ticklabelstandoff=8,
            categoryorder="array",
            categoryarray=top_players["Player_Unique"].tolist(),
            automargin=True,
        ),
        margin=dict(l=12, r=28, t=42, b=38),
    )

    return fig, notice
