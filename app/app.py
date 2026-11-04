from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_mantine_components as dmc

from dash import Dash, html, dcc, Input, Output, _dash_renderer


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

# Configure React 19 BEFORE creating the app
_dash_renderer._set_react_version("19.2.4")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "players_engineered.csv"

df = pd.read_csv(DATA_PATH)

ATTRIBUTE_COLUMNS = {
    "Finishing": "Finishing_Score",
    "Creativity": "Creativity_Score",
    "Passing": "Passing_Score",
    "Progression": "Progression_Score",
    "Defending": "Defending_Score",
    "Ball Security": "BallSecurity_Score",
    "Aerial": "Aerial_Score",
}

POSITION_COLORS = {
    "DF": "#38BDF8",
    "MF": "#A3E635",
    "FW": "#F59E0B",
}

POSITION_LABELS = {
    "FW": "Forwards",
    "MF": "Midfielders",
    "DF": "Defenders",
    "ALL": "All Positions",
}

BG = "#101827"
PANEL = "#172438"
BORDER = "#263449"
TEXT = "#F8FAFC"
MUTED = "#94A3B8"
ACCENT = "#84CC16"


# --------------------------------------------------
# DATA SUMMARY
# --------------------------------------------------

total_players = len(df)
position_counts = df["Pos"].value_counts()

total_defenders = int(position_counts.get("DF", 0))
total_midfielders = int(position_counts.get("MF", 0))
total_forwards = int(position_counts.get("FW", 0))


# --------------------------------------------------
# CHART THEME
# --------------------------------------------------

def style_figure(fig, height=350):
    fig.update_layout(
        height=height,
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        font=dict(color=TEXT, family="Inter, sans-serif"),
        title=dict(
            font=dict(color=TEXT, size=15, family="Inter, sans-serif"),
            subtitle=dict(font=dict(color=MUTED, size=12, family="Inter, sans-serif")),
        ),
        margin=dict(l=25, r=25, t=45, b=25),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=MUTED),
        ),
        xaxis=dict(
            gridcolor=BORDER,
            zerolinecolor=BORDER,
            tickfont=dict(color=MUTED),
            title=dict(font=dict(color=MUTED)),
        ),
        yaxis=dict(
            gridcolor=BORDER,
            zerolinecolor=BORDER,
            tickfont=dict(color=TEXT),
            title=dict(font=dict(color=MUTED)),
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
# METRIC CARD
# --------------------------------------------------

def create_metric_card(title, value, description):
    return dmc.Card(
        children=[
            dmc.Text(title.upper(), size="xs", fw=700, c="dimmed"),
            dmc.Title(str(value), order=2, mt=12, c="white"),
            dmc.Text(description, size="xs", c="dimmed", mt=6),
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


# --------------------------------------------------
# SQUAD COMPOSITION (DONUT CHART)
# --------------------------------------------------

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
    hole=0.68,
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
    textfont=dict(color=TEXT, size=12),
    marker=dict(line=dict(color=PANEL, width=3)),
)

position_fig.add_annotation(
    text=f"<b>{total_players}</b><br><span style='font-size:12px;color:{MUTED}'>Players</span>",
    x=0.5,
    y=0.5,
    showarrow=False,
    font=dict(size=22, color=TEXT),
)

position_fig = style_figure(position_fig, 330)
position_fig.update_layout(
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.15,
        xanchor="center",
        x=0.5,
        font=dict(color=MUTED, size=11),
    ),
    margin=dict(l=20, r=20, t=20, b=40),
)


# --------------------------------------------------
# ATTRIBUTE DISTRIBUTION (BOX PLOT)
# --------------------------------------------------

attribute_melted = df[list(ATTRIBUTE_COLUMNS.values())].melt(
    var_name="Attribute_Col",
    value_name="Score",
)
col_to_name = {v: k for k, v in ATTRIBUTE_COLUMNS.items()}
attribute_melted["Attribute"] = attribute_melted["Attribute_Col"].map(col_to_name)

attribute_fig = px.box(
    attribute_melted,
    x="Score",
    y="Attribute",
    orientation="h",
    category_orders={"Attribute": list(ATTRIBUTE_COLUMNS.keys())},
)

attribute_fig.update_traces(
    marker_color=ACCENT,
    line_color=ACCENT,
    fillcolor="rgba(132, 204, 22, 0.20)",
    boxpoints=False,
)

attribute_fig = style_figure(attribute_fig, 330)
attribute_fig.update_layout(
    xaxis=dict(
        title=dict(text="Percentile Score", font=dict(color=MUTED, size=11)),
        range=[0, 100],
        dtick=20,
        gridcolor=BORDER,
        zerolinecolor=BORDER,
        tickfont=dict(color=MUTED),
    ),
    yaxis=dict(
        title="",
        categoryorder="array",
        categoryarray=list(ATTRIBUTE_COLUMNS.keys()),
        autorange="reversed",
        gridcolor=BORDER,
        zerolinecolor=BORDER,
        tickfont=dict(color=TEXT, size=12),
        automargin=True,
    ),
    margin=dict(l=100, r=25, t=15, b=40),
)


# --------------------------------------------------
# DASH APP
# --------------------------------------------------

app = Dash(__name__)

app.layout = dmc.MantineProvider(
    forceColorScheme="dark",
    theme={
        "primaryColor": "lime",
        "fontFamily": "Inter, sans-serif",
        "defaultRadius": "md",
    },
    children=dmc.AppShell(
        [
            # SIDEBAR
            dmc.AppShellNavbar(
                [
                    dmc.Title("SCOUT", order=2, c="lime"),
                    dmc.Text("FOOTBALL ANALYTICS", size="xs", c="dimmed"),
                    dmc.Divider(my="lg"),

                    dmc.NavLink(label="01   Overview", active=True),
                    dmc.NavLink(label="02   Player Explorer"),
                    dmc.NavLink(label="03   Player Comparison"),
                    dmc.NavLink(label="04   Similar Players"),
                    dmc.NavLink(label="05   Playing Styles"),
                    dmc.NavLink(label="06   Rankings"),
                ],
                p="md",
            ),

            # HEADER
            dmc.AppShellHeader(
                dmc.Group(
                    [
                        dmc.Text("PLAYER SCOUTING PLATFORM", fw=700, size="sm", c="white"),
                        dmc.Badge("2024–25 SEASON", color="lime", variant="light"),
                    ],
                    justify="space-between",
                    px="lg",
                    h="100%",
                )
            ),

            # MAIN CONTENT
            dmc.AppShellMain(
                dmc.Container(
                    [
                        dmc.Title("Football Analytics", order=1, c="white"),
                        dmc.Text(
                            "Discover players. Analyse performance. Identify playing styles.",
                            c="dimmed",
                            mt=8,
                        ),

                        dmc.Space(h=30),

                        # METRIC CARDS
                        dmc.Grid(
                            [
                                dmc.GridCol(
                                    create_metric_card(
                                        "Total Players",
                                        total_players,
                                        "Players with at least 600 minutes",
                                    ),
                                    span={"base": 12, "sm": 6, "lg": 3},
                                ),
                                dmc.GridCol(
                                    create_metric_card(
                                        "Defenders",
                                        total_defenders,
                                        "DF position group",
                                    ),
                                    span={"base": 12, "sm": 6, "lg": 3},
                                ),
                                dmc.GridCol(
                                    create_metric_card(
                                        "Midfielders",
                                        total_midfielders,
                                        "MF position group",
                                    ),
                                    span={"base": 12, "sm": 6, "lg": 3},
                                ),
                                dmc.GridCol(
                                    create_metric_card(
                                        "Forwards",
                                        total_forwards,
                                        "FW position group",
                                    ),
                                    span={"base": 12, "sm": 6, "lg": 3},
                                ),
                            ],
                            gap="lg",
                        ),

                        dmc.Space(h=25),

                        # SQUAD COMPOSITION AND ATTRIBUTE DISTRIBUTION
                        dmc.Grid(
                            [
                                dmc.GridCol(
                                    dmc.Card(
                                        [
                                            dmc.Title(
                                                "Squad Composition",
                                                order=4,
                                                c="white",
                                            ),
                                            dmc.Text(
                                                "Player distribution across position groups",
                                                size="xs",
                                                c="dimmed",
                                                mt=2,
                                            ),
                                            dcc.Graph(
                                                figure=position_fig,
                                                config={"displayModeBar": False},
                                                responsive=True,
                                            ),
                                        ],
                                        withBorder=True,
                                        radius="md",
                                        p="md",
                                        style={
                                            "backgroundColor": PANEL,
                                            "borderColor": BORDER,
                                        },
                                    ),
                                    span={"base": 12, "md": 5},
                                ),

                                dmc.GridCol(
                                    dmc.Card(
                                        [
                                            dmc.Title(
                                                "Attribute Distribution",
                                                order=4,
                                                c="white",
                                            ),
                                            dmc.Text(
                                                "Percentile score distributions (median, quartiles, spread) across all 7 scouting attributes",
                                                size="xs",
                                                c="dimmed",
                                                mt=2,
                                            ),
                                            dcc.Graph(
                                                figure=attribute_fig,
                                                config={"displayModeBar": False},
                                                responsive=True,
                                            ),
                                        ],
                                        withBorder=True,
                                        radius="md",
                                        p="md",
                                        style={
                                            "backgroundColor": PANEL,
                                            "borderColor": BORDER,
                                        },
                                    ),
                                    span={"base": 12, "md": 7},
                                ),
                            ],
                            gap="lg",
                        ),

                        dmc.Space(h=25),

                        # TOP PERFORMERS
                        dmc.Card(
                            [
                                dmc.Group(
                                    [
                                        dmc.Box(
                                            [
                                                dmc.Title(
                                                    "Top Performers",
                                                    order=4,
                                                    c="white",
                                                ),
                                                dmc.Text(
                                                    "Explore leading players ranked by position-relative percentile scores",
                                                    size="xs",
                                                    c="dimmed",
                                                    mt=2,
                                                ),
                                            ],
                                        ),
                                        dmc.Group(
                                            [
                                                dmc.Select(
                                                    id="position-select",
                                                    data=[
                                                        {"label": "Forwards (FW)", "value": "FW"},
                                                        {"label": "Midfielders (MF)", "value": "MF"},
                                                        {"label": "Defenders (DF)", "value": "DF"},
                                                        {"label": "All Positions", "value": "ALL"},
                                                    ],
                                                    value="FW",
                                                    w=175,
                                                    allowDeselect=False,
                                                ),
                                                dmc.Select(
                                                    id="attribute-select",
                                                    data=[
                                                        {"label": name, "value": name}
                                                        for name in ATTRIBUTE_COLUMNS
                                                    ],
                                                    value="Finishing",
                                                    w=175,
                                                    allowDeselect=False,
                                                ),
                                            ],
                                            gap="sm",
                                            wrap="wrap",
                                        ),
                                    ],
                                    justify="space-between",
                                    align="center",
                                    wrap="wrap",
                                ),

                                html.Div(
                                    id="position-limitation-notice",
                                    style={"marginTop": "10px"},
                                ),

                                dmc.Space(h=15),

                                dcc.Graph(
                                    id="top-players-chart",
                                    config={"displayModeBar": False},
                                    responsive=True,
                                ),
                            ],
                            withBorder=True,
                            radius="md",
                            p="lg",
                            style={
                                "backgroundColor": PANEL,
                                "borderColor": BORDER,
                            },
                        ),

                    ],
                    fluid=True,
                    p="xl",
                )
            ),
        ],
        navbar={
            "width": 260,
            "breakpoint": "sm",
            "collapsed": {"mobile": True},
        },
        header={"height": 65},
        padding="md",
        styles={
            "main": {
                "backgroundColor": BG,
                "color": TEXT,
                "minHeight": "100vh",
            },
            "navbar": {
                "backgroundColor": "#151F30",
                "borderRight": f"1px solid {BORDER}",
            },
            "header": {
                "backgroundColor": "#151F30",
                "borderBottom": f"1px solid {BORDER}",
                "color": TEXT,
            },
        },
    ),
)


# --------------------------------------------------
# INTERACTIVE TOP PLAYERS CALLBACK
# --------------------------------------------------

@app.callback(
    Output("top-players-chart", "figure"),
    Output("position-limitation-notice", "children"),
    Input("position-select", "value"),
    Input("attribute-select", "value"),
)
def update_top_players(position, attribute):
    if not attribute or attribute not in ATTRIBUTE_COLUMNS:
        attribute = "Finishing"
    if not position or position not in ["FW", "MF", "DF", "ALL"]:
        position = "FW"

    column = ATTRIBUTE_COLUMNS[attribute]

    # Position-filtered slice and contextual notice
    if position == "ALL":
        filtered_df = df
        pos_display = "Players (All Positions)"
        title_text = f"Top 10 Players (All Positions) — {attribute}"
        notice = dmc.Alert(
            "Analytical Note: Percentile scores are benchmarked within each player's position peer group. Direct comparisons across different positions reflect within-position rank rather than absolute skill parity.",
            title="Cross-Position Percentile Comparison",
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
    else:
        filtered_df = df[df["Pos"] == position]
        pos_display = POSITION_LABELS.get(position, position)
        title_text = f"Top 10 {pos_display} — {attribute}"
        notice = dmc.Text(
            f"Rankings benchmarked strictly against other {pos_display.lower()} with ≥600 minutes played. Scores range from 0 to 100 percentile.",
            size="xs",
            c="dimmed",
            mt=4,
        )

    # Graceful handling for empty results
    if filtered_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No players found matching the selected criteria.",
            showarrow=False,
            font=dict(color=MUTED, size=14),
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
        )
        fig = style_figure(fig, 420)
        fig.update_layout(
            title=dict(
                text=title_text,
                font=dict(color=TEXT, size=15),
            ),
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        )
        return fig, notice

    # Top 10 players sorted ascending so the highest-ranked is at the top
    top_players = (
        filtered_df.nlargest(10, column)
        .sort_values(column, ascending=True)
        .copy()
    )

    # Disambiguate duplicate player names if any exist
    if top_players["Player"].duplicated().any():
        top_players["Player_Display"] = top_players.apply(
            lambda r: f"{r['Player']} ({r['Squad']})"
            if (top_players["Player"] == r["Player"]).sum() > 1
            else r["Player"],
            axis=1,
        )
    else:
        top_players["Player_Display"] = top_players["Player"]

    # Extract 3-letter country code or clean nation for hover tooltip
    top_players["Nation_Clean"] = top_players["Nation"].fillna("N/A").apply(
        lambda x: x.split()[-1] if x != "N/A" and str(x).strip() else "N/A"
    )

    fig = go.Figure(
        go.Bar(
            x=top_players[column],
            y=top_players["Player_Display"],
            orientation="h",
            marker=dict(
                color=ACCENT,
                line=dict(color=ACCENT, width=0),
            ),
            text=top_players[column].apply(lambda v: f"{v:.1f}"),
            textposition="outside",
            cliponaxis=False,
            customdata=top_players[["Player", "Squad", "Pos", "Nation_Clean"]].values,
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

    fig = style_figure(fig, 420)

    fig.update_layout(
        title=dict(
            text=title_text,
            font=dict(color=TEXT, size=15),
        ),
        xaxis=dict(
            title=dict(text="Percentile Score", font=dict(color=MUTED, size=12)),
            range=[0, 110],
            gridcolor=BORDER,
            zerolinecolor=BORDER,
            tickfont=dict(color=MUTED),
        ),
        yaxis=dict(
            title="",
            gridcolor=BORDER,
            zerolinecolor=BORDER,
            tickfont=dict(color=TEXT, size=12),
            categoryorder="array",
            categoryarray=top_players["Player_Display"].tolist(),
            automargin=True,
        ),
        margin=dict(l=150, r=35, t=55, b=40),
    )

    return fig, notice


if __name__ == "__main__":
    app.run(debug=True)
