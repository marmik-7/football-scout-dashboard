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
position_counts = df["Pos"].value_counts()
total_defenders = int(position_counts.get("DF", 0))
total_midfielders = int(position_counts.get("MF", 0))
total_forwards = int(position_counts.get("FW", 0))


# --------------------------------------------------
# STATIC OVERVIEW FIGURES
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
position_fig = style_figure(position_fig, 320)
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
attribute_box_fig = style_figure(attribute_box_fig, 320)
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
            subtitle="High-level evaluation of squad composition, attribute distributions, and talent benchmarks across Europe's top 5 leagues.",
            badge_text="2024–25 SEASON",
        ),

        # METRIC CARDS
        dmc.Grid(
            [
                dmc.GridCol(
                    create_metric_card(
                        "Total Qualified Talent",
                        f"{total_players:,}",
                        "Players with ≥600 minutes played",
                        color="#FFFFFF",
                    ),
                    span={"base": 12, "sm": 6, "lg": 3},
                ),
                dmc.GridCol(
                    create_metric_card(
                        "Defenders",
                        total_defenders,
                        "DF cohort (41.5% of database)",
                        color=POSITION_COLORS["DF"],
                    ),
                    span={"base": 12, "sm": 6, "lg": 3},
                ),
                dmc.GridCol(
                    create_metric_card(
                        "Midfielders",
                        total_midfielders,
                        "MF cohort (33.3% of database)",
                        color=POSITION_COLORS["MF"],
                    ),
                    span={"base": 12, "sm": 6, "lg": 3},
                ),
                dmc.GridCol(
                    create_metric_card(
                        "Forwards",
                        total_forwards,
                        "FW cohort (25.2% of database)",
                        color=POSITION_COLORS["FW"],
                    ),
                    span={"base": 12, "sm": 6, "lg": 3},
                ),
            ],
            gap="md",
        ),

        dmc.Space(h=20),

        # SQUAD COMPOSITION AND ATTRIBUTE DISTRIBUTION
        dmc.Grid(
            [
                dmc.GridCol(
                    create_section_card(
                        dcc.Graph(figure=position_fig, config={"displayModeBar": False}, responsive=True),
                        title="Position Balance",
                        subtitle="Player distribution across positional cohorts",
                    ),
                    span={"base": 12, "md": 5},
                ),
                dmc.GridCol(
                    create_section_card(
                        dcc.Graph(figure=attribute_box_fig, config={"displayModeBar": False}, responsive=True),
                        title="Scouting Attribute Distributions",
                        subtitle="Quartiles ($Q_1$, median, $Q_3$) across all 7 scouting dimensions",
                    ),
                    span={"base": 12, "md": 7},
                ),
            ],
            gap="md",
        ),

        dmc.Space(h=20),

        # TOP PERFORMERS
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
)
def update_overview_top_players(position, attribute):
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
