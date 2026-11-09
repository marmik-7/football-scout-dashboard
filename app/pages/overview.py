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

dash.register_page(__name__, path="/", name="Overview", order=1)

df = load_data()

total_players = len(df)
u21_prospects = int(len(df[(df["Age"] <= 21) & (df["Age"] > 0)]))
clinical_finishers = int(len(df[df.get("G-xG", 0.0) >= 2.0]))
elite_defenders = int(len(df[df.get("Defending_Score", 0.0) >= 80.0]))


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
                    create_metric_card(
                        "Qualified Talent Pool",
                        f"{total_players:,}",
                        "European Big 5 leagues (≥600 mins)",
                        color=TEXT,
                    ),
                    span={"base": 12, "sm": 6, "lg": 3},
                ),
                dmc.GridCol(
                    create_metric_card(
                        "U-21 Elite Prospects",
                        u21_prospects,
                        "Emerging players age ≤21 in database",
                        color="cyan",
                    ),
                    span={"base": 12, "sm": 6, "lg": 3},
                ),
                dmc.GridCol(
                    create_metric_card(
                        "Clinical Outperformers",
                        clinical_finishers,
                        "Finishing variance G - xG ≥ +2.0",
                        color="emerald",
                    ),
                    span={"base": 12, "sm": 6, "lg": 3},
                ),
                dmc.GridCol(
                    create_metric_card(
                        "Elite Ball Winners",
                        elite_defenders,
                        "Top 20th percentile defensive actions",
                        color="blue",
                    ),
                    span={"base": 12, "sm": 6, "lg": 3},
                ),
            ],
            gap="md",
        ),

        dmc.Space(h=16),

        # MARKET SPOTLIGHTS: HIGH-POTENTIAL RECRUITMENT OPPORTUNITIES
        create_section_card(
            dmc.Grid(
                [
                    dmc.GridCol(
                        dmc.Box(
                            [
                                dmc.Group([
                                    dmc.Badge("Breakthrough", color="cyan", variant="light", size="xs"),
                                    dmc.Text("U-21 Winger", size="10px", c="var(--scout-text-muted)"),
                                ], justify="space-between"),
                                dmc.Text("Lamine Yamal", size="sm", fw=700, c="var(--scout-text-primary)", mt=6),
                                dmc.Text("Barcelona • La Liga • Age 17", size="xs", c="var(--scout-text-secondary)"),
                                dmc.Text("96.1th pct Creativity, elite 1v1 take-on volume and box entries.", size="xs", c="var(--scout-text-secondary)", mt=4),
                                dcc.Link(
                                    dmc.Button("Open Dossier →", size="xs", variant="subtle", color="cyan", p=0, mt=8),
                                    href="/player-profile?player=Lamine Yamal",
                                    style={"textDecoration": "none"},
                                ),
                            ],
                            style={
                                "backgroundColor": "var(--scout-surface-secondary)",
                                "border": "1px solid var(--scout-border)",
                                "borderRadius": "6px",
                                "padding": "14px 16px",
                            },
                        ),
                        span={"base": 12, "md": 4},
                    ),
                    dmc.GridCol(
                        dmc.Box(
                            [
                                dmc.Group([
                                    dmc.Badge("Clinical Target", color="emerald", variant="light", size="xs"),
                                    dmc.Text("Center Forward", size="10px", c="var(--scout-text-muted)"),
                                ], justify="space-between"),
                                dmc.Text("Erling Haaland", size="sm", fw=700, c="var(--scout-text-primary)", mt=6),
                                dmc.Text("Manchester City • Premier League • Age 24", size="xs", c="var(--scout-text-secondary)"),
                                dmc.Text("0.85 Gls/90, 98.4th pct Finishing, unmatched box gravity.", size="xs", c="var(--scout-text-secondary)", mt=4),
                                dcc.Link(
                                    dmc.Button("Open Dossier →", size="xs", variant="subtle", color="emerald", p=0, mt=8),
                                    href="/player-profile?player=Erling Haaland",
                                    style={"textDecoration": "none"},
                                ),
                            ],
                            style={
                                "backgroundColor": "var(--scout-surface-secondary)",
                                "border": "1px solid var(--scout-border)",
                                "borderRadius": "6px",
                                "padding": "14px 16px",
                            },
                        ),
                        span={"base": 12, "md": 4},
                    ),
                    dmc.GridCol(
                        dmc.Box(
                            [
                                dmc.Group([
                                    dmc.Badge("Defensive Anchor", color="blue", variant="light", size="xs"),
                                    dmc.Text("Center-Back", size="10px", c="var(--scout-text-muted)"),
                                ], justify="space-between"),
                                dmc.Text("William Saliba", size="sm", fw=700, c="var(--scout-text-primary)", mt=6),
                                dmc.Text("Arsenal • Premier League • Age 23", size="xs", c="var(--scout-text-secondary)"),
                                dmc.Text("97.2th pct Ball Retention, 93.8% pass accuracy, recovery speed.", size="xs", c="var(--scout-text-secondary)", mt=4),
                                dcc.Link(
                                    dmc.Button("Open Dossier →", size="xs", variant="subtle", color="blue", p=0, mt=8),
                                    href="/player-profile?player=William Saliba",
                                    style={"textDecoration": "none"},
                                ),
                            ],
                            style={
                                "backgroundColor": "var(--scout-surface-secondary)",
                                "border": "1px solid var(--scout-border)",
                                "borderRadius": "6px",
                                "padding": "14px 16px",
                            },
                        ),
                        span={"base": 12, "md": 4},
                    ),
                ],
                gap="md",
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
                dcc.Graph(
                    id="overview-top-players-chart",
                    config={"displayModeBar": False},
                    responsive=True,
                ),
            ],
            title="Top Benchmark Performers",
            subtitle="Leading candidates ranked by position-relative percentile scores",
            extra_header=dmc.Group(
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
                        w=165,
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
                        w=165,
                        size="xs",
                        allowDeselect=False,
                    ),
                ],
                gap="xs",
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
    Input("scout-analyst-mode", "data"),
    Input("theme-store", "data"),
)
def update_overview_top_players(position, attribute, scout_analyst_mode="scout", theme="dark"):
    scout_analyst_mode = scout_analyst_mode or "scout"
    theme = theme or "dark"
    is_light = (theme == "light")
    text_color = "#0F172A" if is_light else "#F8FAFC"
    muted_color = "#64748B" if is_light else "#94A3B8"
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
        notice = dmc.Alert(
            "Analytical Note: Percentile scores are benchmarked within each player's position peer group. Direct comparisons across different positions reflect within-position rank rather than absolute skill parity.",
            title="Cross-Position Percentile Comparison",
            color="yellow",
            variant="light",
            radius="sm",
            p="xs",
            style={
                "backgroundColor": "rgba(245, 158, 11, 0.05)",
                "borderColor": "rgba(245, 158, 11, 0.20)",
                "color": "var(--scout-text-primary, #F8FAFC)",
                "fontSize": "12px",
            },
        )
    else:
        filtered_df = df[df["Pos"] == position]
        pos_display = POSITION_NAMES.get(position, position)
        title_text = f"Top 10 {pos_display} — {attribute}"
        notice = dmc.Text(
            f"Rankings benchmarked strictly against other {pos_display.lower()} with ≥600 minutes played. Scores span 0 to 100 percentile.",
            size="xs",
            c="var(--scout-text-secondary, #94A3B8)",
        )

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
        fig = style_figure(fig, 380, theme=theme)
        return fig, notice

    top_players = (
        filtered_df.nlargest(10, column)
        .sort_values(column, ascending=True)
        .copy()
    )

    nat_col = "Nation_Display" if "Nation_Display" in top_players.columns else "Nation_Clean"

    fig = go.Figure(
        go.Bar(
            x=top_players[column],
            y=top_players["Player_Unique"],
            orientation="h",
            marker=dict(
                color="#10B981",
                line=dict(color="rgba(16, 185, 129, 0.3)", width=1),
            ),
            text=top_players[column].apply(lambda v: f"{v:.1f}"),
            textposition="outside",
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

    fig = style_figure(fig, 380, theme=theme)
    fig.update_layout(
        title=dict(text=title_text, font=dict(color=text_color, size=14)),
        xaxis=dict(
            title=dict(text="Percentile Score", font=dict(color=muted_color, size=11)),
            range=[0, 110],
            gridcolor=grid_color,
            tickfont=dict(color=muted_color, size=10),
        ),
        yaxis=dict(
            title="",
            gridcolor=grid_color,
            tickfont=dict(color=text_color, size=11),
            categoryorder="array",
            categoryarray=top_players["Player_Unique"].tolist(),
            automargin=True,
        ),
        margin=dict(l=150, r=35, t=45, b=35),
    )

    return fig, notice
