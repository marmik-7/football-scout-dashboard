import dash
from dash import html, dcc, Input, Output, callback
import dash_mantine_components as dmc
import plotly.graph_objects as go
import pandas as pd

from app.utils.data_loader import load_data, load_cluster_summary
from app.utils.styling import (
    PANEL,
    BORDER,
    TEXT,
    MUTED,
    ACCENT,
    POSITION_COLORS,
    CLUSTER_COLORS,
    ATTRIBUTE_COLUMNS,
    create_page_header,
    create_section_card,
    get_percentile_tier,
)
from app.utils.charts import build_pca_cluster_scatter, build_cluster_dna_radar

dash.register_page(__name__, path="/playing-styles", name="Playing Styles", order=6)

df = load_data()
summary_df = load_cluster_summary()


# --------------------------------------------------
# PAGE LAYOUT
# --------------------------------------------------

layout = dmc.Container(
    [
        create_page_header(
            title="Tactical Playing Styles",
            subtitle="Unsupervised machine learning archetypes. Discover tactical sub-roles and spatial distributions using K-Means clustering and PCA.",
            badge_text="K-MEANS & PCA MODELING",
        ),

        # POSITION AND CLUSTER CONTROLS
        create_section_card(
            dmc.Grid(
                [
                    dmc.GridCol(
                        dmc.Select(
                            id="styles-pos-select",
                            label="Position Group",
                            data=[
                                {"label": "Forwards (FW)", "value": "FW"},
                                {"label": "Midfielders (MF)", "value": "MF"},
                                {"label": "Defenders (DF)", "value": "DF"},
                            ],
                            value="FW",
                            allowDeselect=False,
                        ),
                        span={"base": 12, "sm": 6, "md": 4},
                    ),
                    dmc.GridCol(
                        dmc.Select(
                            id="styles-cluster-select",
                            label="Cluster Filter",
                            data=[
                                {"label": "All 4 Clusters", "value": "ALL"},
                                {"label": "Cluster 0", "value": "0"},
                                {"label": "Cluster 1", "value": "1"},
                                {"label": "Cluster 2", "value": "2"},
                                {"label": "Cluster 3", "value": "3"},
                            ],
                            value="ALL",
                            allowDeselect=False,
                        ),
                        span={"base": 12, "sm": 6, "md": 4},
                    ),
                    dmc.GridCol(
                        dmc.Select(
                            id="styles-player-locator",
                            label="📍 Pinpoint Candidate in Tactical Space",
                            placeholder="Search candidate to plot pin...",
                            data=[{"label": "None (View All)", "value": "NONE"}] + [
                                {"label": name, "value": name}
                                for name in sorted(df[df["Pos"] == "FW"]["Player"].unique())
                            ],
                            value="NONE",
                            searchable=True,
                            clearable=True,
                        ),
                        span={"base": 12, "md": 4},
                    ),
                ],
                gap="md",
            ),
            title="Tactical Scope",
            subtitle="Select position peer group, target playing style cluster, and locate specific players",
        ),

        dmc.Space(h=20),

        # CLUSTER KPI CARDS
        html.Div(id="styles-cards-container"),

        dmc.Space(h=20),

        # VISUALIZATIONS: PCA SCATTER + RADAR DNA
        dmc.Grid(
            [
                dmc.GridCol(
                    create_section_card(
                        dcc.Graph(
                            id="styles-pca-scatter",
                            config={"displayModeBar": False},
                            responsive=True,
                        ),
                        title="Principal Component Analysis (PCA)",
                        subtitle="2D projection of player attribute space highlighting spatial clusters",
                    ),
                    span={"base": 12, "lg": 7},
                ),
                dmc.GridCol(
                    create_section_card(
                        dcc.Graph(
                            id="styles-dna-radar",
                            config={"displayModeBar": False},
                            responsive=True,
                        ),
                        title="Tactical DNA Archetype Radar",
                        subtitle="Comparative mean profiles of the 4 positional clusters",
                    ),
                    span={"base": 12, "lg": 5},
                ),
            ],
            gap="lg",
        ),

        dmc.Space(h=25),

        # CLUSTER PROFILES COMPARISON TABLE
        create_section_card(
            html.Div(id="styles-summary-table-container", style={"overflowX": "auto"}),
            title="Cluster Attribute Means Matrix",
            subtitle="Mean percentile scores (0–100) across all 7 dimensions for each identified playing style",
        ),

        dmc.Space(h=25),

        # REPRESENTATIVE ROSTER TABLE
        create_section_card(
            html.Div(id="styles-roster-table-container", style={"overflowX": "auto"}),
            title="Cluster Player Roster & Representatives",
            subtitle="Explore qualified players assigned to the selected playing style archetype",
        ),
    ],
    fluid=True,
    p=0,
)


# --------------------------------------------------
# CALLBACKS
# --------------------------------------------------

@callback(
    Output("styles-player-locator", "data"),
    Output("styles-player-locator", "value"),
    Input("styles-pos-select", "value"),
)
def update_locator_dropdown(pos):
    pos = pos or "FW"
    pos_players = sorted(df[df["Pos"] == pos]["Player"].unique())
    options = [{"label": "None (View All)", "value": "NONE"}] + [
        {"label": name, "value": name} for name in pos_players
    ]
    return options, "NONE"


@callback(
    Output("styles-cards-container", "children"),
    Output("styles-pca-scatter", "figure"),
    Output("styles-dna-radar", "figure"),
    Output("styles-summary-table-container", "children"),
    Output("styles-roster-table-container", "children"),
    Input("styles-pos-select", "value"),
    Input("styles-cluster-select", "value"),
    Input("styles-player-locator", "value"),
)
def update_playing_styles(pos, cluster_filter, locator_player="NONE"):
    if not pos:
        pos = "FW"

    sub_summary = summary_df[summary_df["Pos"] == pos].sort_values("PlayingStyle_Cluster")
    pos_players = df[df["Pos"] == pos]
    total_pos_players = len(pos_players)

    # 1. Cluster KPI Cards
    cards = []
    for idx, r in sub_summary.iterrows():
        c_id = int(r["PlayingStyle_Cluster"])
        c_name = r["Cluster_Name"]
        c_count = int(r["Player_Count"])
        c_pct = (c_count / total_pos_players) * 100.0
        color = CLUSTER_COLORS[c_id % len(CLUSTER_COLORS)]

        is_selected = cluster_filter != "ALL" and str(cluster_filter) == str(c_id)

        # Identify top 2 highest mean attributes for this cluster
        attr_means = {
            "Finishing": r["Finishing"],
            "Creativity": r["Creativity"],
            "Passing": r["Passing"],
            "Progression": r["Progression"],
            "Defending": r["Defending"],
            "Security": r["BallSecurity"],
            "Aerial": r["Aerial"],
        }
        top_2 = sorted(attr_means.items(), key=lambda x: x[1], reverse=True)[:2]
        traits_str = f"Signature: {top_2[0][0]} ({top_2[0][1]:.1f}), {top_2[1][0]} ({top_2[1][1]:.1f})"

        cards.append(
            dmc.GridCol(
                dmc.Card(
                    [
                        dmc.Group([
                            dmc.Badge(f"Cluster {c_id}", color=color, variant="filled", size="xs"),
                            dmc.Text(f"{c_count} players ({c_pct:.1f}%)", size="xs", c="dimmed"),
                        ], justify="space-between"),
                        dmc.Title(c_name, order=4, c="white", mt=6),
                        dmc.Text(traits_str, size="xs", c="dimmed", mt=4),
                    ],
                    withBorder=True,
                    radius="md",
                    p="md",
                    style={
                        "backgroundColor": "#131E30",
                        "borderColor": color if is_selected else BORDER,
                        "borderTop": f"3px solid {color}",
                    },
                ),
                span={"base": 12, "sm": 6, "lg": 3},
            )
        )
    cards_container = dmc.Grid(cards, gap="md")

    # 2. PCA Scatter Plot with Optional Candidate Highlight Pin
    pca_fig = build_pca_cluster_scatter(
        df,
        pos=pos,
        selected_cluster=cluster_filter,
        highlight_player=locator_player,
        height=450,
    )

    # 3. Cluster DNA Radar
    radar_fig = build_cluster_dna_radar(summary_df, pos=pos, height=420)

    # 4. Cluster Summary Means Table
    thead_summary = dmc.TableThead(
        dmc.TableTr([
            dmc.TableTh("Cluster", style={"color": TEXT}),
            dmc.TableTh("Archetype Name", style={"color": TEXT}),
            dmc.TableTh("Players", style={"color": TEXT}),
            dmc.TableTh("Finishing", style={"color": TEXT}),
            dmc.TableTh("Creativity", style={"color": TEXT}),
            dmc.TableTh("Passing", style={"color": TEXT}),
            dmc.TableTh("Progression", style={"color": TEXT}),
            dmc.TableTh("Defending", style={"color": TEXT}),
            dmc.TableTh("Security", style={"color": TEXT}),
            dmc.TableTh("Aerial", style={"color": TEXT}),
        ])
    )

    summary_rows = []
    for idx, r in sub_summary.iterrows():
        c_id = int(r["PlayingStyle_Cluster"])
        color = CLUSTER_COLORS[c_id % len(CLUSTER_COLORS)]

        def fmt_cell(val):
            v = float(val)
            c = "#84CC16" if v >= 65 else "#38BDF8" if v >= 50 else "#F59E0B" if v >= 35 else "#EF4444"
            return dmc.Text(f"{v:.1f}", fw=600, style={"color": c})

        summary_rows.append(
            dmc.TableTr([
                dmc.TableTd(dmc.Badge(f"Cluster {c_id}", color=color, variant="filled", size="xs")),
                dmc.TableTd(dmc.Text(r["Cluster_Name"], fw=600, c="white")),
                dmc.TableTd(dmc.Text(str(int(r["Player_Count"])), c="dimmed")),
                dmc.TableTd(fmt_cell(r["Finishing"])),
                dmc.TableTd(fmt_cell(r["Creativity"])),
                dmc.TableTd(fmt_cell(r["Passing"])),
                dmc.TableTd(fmt_cell(r["Progression"])),
                dmc.TableTd(fmt_cell(r["Defending"])),
                dmc.TableTd(fmt_cell(r["BallSecurity"])),
                dmc.TableTd(fmt_cell(r["Aerial"])),
            ])
        )

    summary_table = dmc.Table(
        [thead_summary, dmc.TableTbody(summary_rows)],
        striped=True,
        highlightOnHover=True,
        withTableBorder=True,
        style={"backgroundColor": PANEL, "fontSize": "13px", "borderColor": BORDER},
    )

    # 5. Roster Table for Cluster
    roster_df = pos_players.copy()
    if cluster_filter != "ALL":
        c_num = int(cluster_filter)
        roster_df = roster_df[roster_df["PlayingStyle_Cluster"] == c_num]

    roster_df = roster_df.sort_values("Min", ascending=False).head(25)

    thead_roster = dmc.TableThead(
        dmc.TableTr([
            dmc.TableTh("Player", style={"color": TEXT}),
            dmc.TableTh("Club", style={"color": TEXT}),
            dmc.TableTh("Cluster / Archetype", style={"color": TEXT}),
            dmc.TableTh("Min", style={"color": TEXT}),
            dmc.TableTh("G+A", style={"color": TEXT}),
            dmc.TableTh("Finishing", style={"color": TEXT}),
            dmc.TableTh("Creativity", style={"color": TEXT}),
            dmc.TableTh("Passing", style={"color": TEXT}),
            dmc.TableTh("Progression", style={"color": TEXT}),
            dmc.TableTh("Defending", style={"color": TEXT}),
            dmc.TableTh("Action", style={"color": TEXT, "textAlign": "center"}),
        ])
    )

    roster_rows = []
    for _, r in roster_df.iterrows():
        c_id = int(r["PlayingStyle_Cluster"])
        color = CLUSTER_COLORS[c_id % len(CLUSTER_COLORS)]
        profile_url = f"/player-profile?player={r['Player_Unique']}"
        ga = int(r.get("Gls", 0) + r.get("Ast", 0))

        roster_rows.append(
            dmc.TableTr([
                dmc.TableTd(dmc.Text(r["Player"], fw=600, c="white")),
                dmc.TableTd(dmc.Text(r["Squad"], size="xs", c="dimmed")),
                dmc.TableTd(dmc.Badge(r.get("PlayingStyle_Name", f"Cluster {c_id}"), color=color, variant="light", size="xs")),
                dmc.TableTd(dmc.Text(f"{r['Min']:,}m", size="xs", c="dimmed")),
                dmc.TableTd(dmc.Text(str(ga), size="xs", fw=600, c="white")),
                dmc.TableTd(dmc.Text(f"{r['Finishing_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Finishing_Score'])["color"]})),
                dmc.TableTd(dmc.Text(f"{r['Creativity_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Creativity_Score'])["color"]})),
                dmc.TableTd(dmc.Text(f"{r['Passing_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Passing_Score'])["color"]})),
                dmc.TableTd(dmc.Text(f"{r['Progression_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Progression_Score'])["color"]})),
                dmc.TableTd(dmc.Text(f"{r['Defending_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Defending_Score'])["color"]})),
                dmc.TableTd(
                    dcc.Link(
                        dmc.Button("Profile →", size="xs", variant="light", color="lime"),
                        href=profile_url,
                        style={"textDecoration": "none"},
                    ),
                    style={"textAlign": "center"},
                ),
            ])
        )

    roster_table = dmc.Table(
        [thead_roster, dmc.TableTbody(roster_rows)],
        striped=True,
        highlightOnHover=True,
        withTableBorder=True,
        style={"backgroundColor": PANEL, "fontSize": "13px", "borderColor": BORDER},
    )

    return cards_container, pca_fig, radar_fig, summary_table, roster_table

