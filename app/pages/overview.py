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
# STATIC OVERVIEW FIGURES (PROGRESSIVE DISCLOSURE)
# --------------------------------------------------

# 1. Squad Composition Donut
position_data = (
    df["Pos"]
    .value_counts()
    .rename_axis("Position")
    .reset_index(name="Players")
)
position_data["Position"] = position_data["Position"].map({
    "DF": "Defenders",
    "MF": "Midfielders",
    "FW": "Forwards",
})

position_fig = px.pie(
    position_data,
    names="Position",
    values="Players",
    hole=0.70,
    color="Position",
    color_discrete_map={
        "Defenders": POSITION_COLORS["DF"],
        "Midfielders": POSITION_COLORS["MF"],
        "Forwards": POSITION_COLORS["FW"],
    },
)
position_fig.update_traces(
    textposition="outside",
    textinfo="percent",
    textfont=dict(color=MUTED, size=11),
    marker=dict(line=dict(color="#0F172A", width=2.5)),
)
position_fig.add_annotation(
    text=f"<b>{total_players}</b><br><span style='font-size:11px;color:{MUTED}'>Qualified</span>",
    x=0.5,
    y=0.5,
    showarrow=False,
    font=dict(size=20, color="#FFFFFF"),
)
position_fig = style_figure(position_fig, 300)
position_fig.update_layout(
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.18,
        xanchor="center",
        x=0.5,
        font=dict(color=MUTED, size=11),
    ),
    margin=dict(l=20, r=20, t=15, b=35),
)

# 2. Attribute Distribution Box Plots
attribute_melted = df[list(ATTRIBUTE_COLUMNS.values())].melt(
    var_name="Attribute_Col",
    value_name="Score",
)
col_to_name = {v: k for k, v in ATTRIBUTE_COLUMNS.items()}
attribute_melted["Attribute"] = attribute_melted["Attribute_Col"].map(col_to_name)

attribute_box_fig = px.box(
    attribute_melted,
    x="Score",
    y="Attribute",
    orientation="h",
    category_orders={"Attribute": list(ATTRIBUTE_COLUMNS.keys())},
)
attribute_box_fig.update_traces(
    marker_color="#10B981",
    line_color="#10B981",
    fillcolor="rgba(16, 185, 129, 0.15)",
    boxpoints=False,
)
attribute_box_fig = style_figure(attribute_box_fig, 300)
attribute_box_fig.update_layout(
    xaxis=dict(
        title=dict(text="Percentile Score (0–100)", font=dict(color=MUTED, size=11)),
        range=[0, 100],
        dtick=20,
        gridcolor="rgba(255, 255, 255, 0.05)",
        tickfont=dict(color=MUTED, size=10),
    ),
    yaxis=dict(
        title="",
        categoryorder="array",
        categoryarray=list(ATTRIBUTE_COLUMNS.keys()),
        autorange="reversed",
        gridcolor="rgba(255, 255, 255, 0.05)",
        tickfont=dict(color=TEXT, size=11),
        automargin=True,
    ),
    margin=dict(l=95, r=25, t=15, b=35),
)


# --------------------------------------------------
# PAGE LAYOUT
# --------------------------------------------------

layout = dmc.Container(
    [
        create_page_header(
            title="Executive Market Briefing",
            subtitle="Recruitment intelligence, standout breakout talents, clinical finishers, and top positional leaders across Europe's top 5 leagues.",
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
                        color="#FFFFFF",
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
                                    dmc.Badge("★ BREAKTHROUGH TALENT", color="cyan", variant="filled", size="xs"),
                                    dmc.Text("U-21 Winger", size="10px", c="dimmed"),
                                ], justify="space-between"),
                                dmc.Text("Lamine Yamal", size="sm", fw=700, c="white", mt=4),
                                dmc.Text("Barcelona • La Liga • Age 17", size="xs", c="dimmed"),
                                dmc.Text("96.1th pct Creativity, elite 1v1 take-on volume and box entries.", size="xs", c="#CBD5E1", mt=4),
                                dmc.Anchor(
                                    dmc.Button("Open Dossier →", size="xs", variant="subtle", color="cyan", p=0, mt=6),
                                    href="/player-profile?player=Lamine Yamal",
                                ),
                            ],
                            style={"backgroundColor": "#090D14", "border": f"1px solid {BORDER}", "borderRadius": "4px", "padding": "12px 14px"},
                        ),
                        span={"base": 12, "md": 4},
                    ),
                    dmc.GridCol(
                        dmc.Box(
                            [
                                dmc.Group([
                                    dmc.Badge("🎯 CLINICAL TARGET", color="emerald", variant="filled", size="xs"),
                                    dmc.Text("Center Forward", size="10px", c="dimmed"),
                                ], justify="space-between"),
                                dmc.Text("Erling Haaland", size="sm", fw=700, c="white", mt=4),
                                dmc.Text("Manchester City • Premier League • Age 24", size="xs", c="dimmed"),
                                dmc.Text("0.85 Gls/90, 98.4th pct Finishing, unmatched box gravity.", size="xs", c="#CBD5E1", mt=4),
                                dmc.Anchor(
                                    dmc.Button("Open Dossier →", size="xs", variant="subtle", color="emerald", p=0, mt=6),
                                    href="/player-profile?player=Erling Haaland",
                                ),
                            ],
                            style={"backgroundColor": "#090D14", "border": f"1px solid {BORDER}", "borderRadius": "4px", "padding": "12px 14px"},
                        ),
                        span={"base": 12, "md": 4},
                    ),
                    dmc.GridCol(
                        dmc.Box(
                            [
                                dmc.Group([
                                    dmc.Badge("🛡️ DEFENSIVE ANCHOR", color="blue", variant="filled", size="xs"),
                                    dmc.Text("Center-Back", size="10px", c="dimmed"),
                                ], justify="space-between"),
                                dmc.Text("William Saliba", size="sm", fw=700, c="white", mt=4),
                                dmc.Text("Arsenal • Premier League • Age 23", size="xs", c="dimmed"),
                                dmc.Text("97.2th pct Ball Retention, 93.8% pass accuracy, recovery speed.", size="xs", c="#CBD5E1", mt=4),
                                dmc.Anchor(
                                    dmc.Button("Open Dossier →", size="xs", variant="subtle", color="blue", p=0, mt=6),
                                    href="/player-profile?player=William Saliba",
                                ),
                            ],
                            style={"backgroundColor": "#090D14", "border": f"1px solid {BORDER}", "borderRadius": "4px", "padding": "12px 14px"},
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

        dmc.Space(h=16),

        # STATISTICAL COHORT DISTRIBUTIONS (LAYER 3 PROGRESSIVE DISCLOSURE ACCORDION)
        dmc.Accordion(
            styles={
                "item": {
                    "backgroundColor": PANEL,
                    "border": f"1px solid {BORDER}",
                    "borderRadius": "6px",
                    "marginBottom": "12px",
                },
                "control": {
                    "color": "white",
                    "padding": "12px 18px",
                },
                "panel": {
                    "padding": "0px 18px 18px 18px",
                },
            },
            children=[
                dmc.AccordionItem(
                    [
                        dmc.AccordionControl(
                            dmc.Group([
                                dmc.Text("Cohort Distribution Analysis & Position Balance", fw=700, size="sm", c="white"),
                                dmc.Badge("DATABASE BENCHMARKS", color="indigo", variant="light", size="xs"),
                                dmc.Text("Squad composition donut and attribute quartile boxplots across 1,692 qualified players", size="xs", c="dimmed"),
                            ], gap="xs")
                        ),
                        dmc.AccordionPanel(
                            dmc.Grid(
                                [
                                    dmc.GridCol(
                                        dmc.Box([
                                            dmc.Text("Positional Cohort Balance", fw=600, size="xs", c="white", mb=4),
                                            dcc.Graph(figure=position_fig, config={"displayModeBar": False}, responsive=True, style={"height": "300px"}),
                                        ]),
                                        span={"base": 12, "md": 5},
                                    ),
                                    dmc.GridCol(
                                        dmc.Box([
                                            dmc.Text("Scouting Attribute Quartiles (Q1, Median, Q3)", fw=600, size="xs", c="white", mb=4),
                                            dcc.Graph(figure=attribute_box_fig, config={"displayModeBar": False}, responsive=True, style={"height": "300px"}),
                                        ]),
                                        span={"base": 12, "md": 7},
                                    ),
                                ],
                                gap="md",
                            )
                        ),
                    ],
                    value="distributions",
                )
            ],
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
)
def update_overview_top_players(position, attribute, scout_analyst_mode="scout"):
    scout_analyst_mode = scout_analyst_mode or "scout"
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
                "color": "#F8FAFC",
                "fontSize": "12px",
            },
        )
    else:
        filtered_df = df[df["Pos"] == position]
        pos_display = POSITION_NAMES.get(position, position)
        title_text = f"Top 10 {pos_display} — {attribute}"
        notice = dmc.Group([
            dmc.Badge("●", color="teal", variant="transparent", size="xs", p=0),
            dmc.Text(
                f"Rankings benchmarked strictly against other {pos_display.lower()} with ≥600 minutes played. Scores span 0 to 100 percentile.",
                size="xs",
                c=MUTED,
            ),
        ], gap=6)

    if filtered_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No players found matching the selected criteria.",
            showarrow=False,
            font=dict(color=MUTED, size=13),
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
        )
        fig = style_figure(fig, 380)
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
                line=dict(color="#090D14", width=1),
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

    fig = style_figure(fig, 380)
    fig.update_layout(
        title=dict(text=title_text, font=dict(color="#FFFFFF", size=14)),
        xaxis=dict(
            title=dict(text="Percentile Score", font=dict(color=MUTED, size=11)),
            range=[0, 110],
            gridcolor="rgba(255, 255, 255, 0.05)",
            tickfont=dict(color=MUTED, size=10),
        ),
        yaxis=dict(
            title="",
            gridcolor="rgba(255, 255, 255, 0.05)",
            tickfont=dict(color=TEXT, size=11),
            categoryorder="array",
            categoryarray=top_players["Player_Unique"].tolist(),
            automargin=True,
        ),
        margin=dict(l=150, r=35, t=45, b=35),
    )

    return fig, notice
