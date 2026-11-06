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
from app.utils.metric_definitions import get_sample_size_badge, SAMPLE_SIZE_THRESHOLD

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
            subtitle="Unsupervised machine learning archetypes. Spatial 2D projection and cluster DNA via K-Means clustering and PCA.",
            badge_text="TACTICAL ARCHETYPES",
        ),

        # POSITION AND CLUSTER CONTROLS
        create_section_card(
            dmc.Grid(
                [
                    dmc.GridCol(
                        dmc.Select(
                            id="styles-pos-select",
                            label="Position Cohort",
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
                            label="Tactical Archetype Filter",
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
                            label="Pinpoint Candidate in 2D Space",
                            placeholder="Select candidate to plot beacon pin...",
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
                gap="sm",
            ),
            title="Archetype Scope & Locator",
            subtitle="Select position peer group, filter specific playing style clusters, or pinpoint an individual player's coordinates",
        ),

        dmc.Space(h=16),

        # CLUSTER KPI CARDS
        html.Div(id="styles-cards-container"),

        dmc.Space(h=16),

        # VISUALIZATIONS: PCA SCATTER + RADAR DNA
        dmc.Grid(
            [
                dmc.GridCol(
                    create_section_card(
                        dcc.Graph(
                            id="styles-pca-scatter",
                            config={"displayModeBar": False},
                            responsive=True,
                            style={"height": "430px", "width": "100%"},
                        ),
                        title="Principal Component Analysis (PCA)",
                        subtitle="2D projection of player attribute space highlighting spatial archetype clusters",
                    ),
                    span={"base": 12, "lg": 7},
                ),
                dmc.GridCol(
                    create_section_card(
                        dcc.Graph(
                            id="styles-dna-radar",
                            config={"displayModeBar": False},
                            responsive=True,
                            style={"height": "430px", "width": "100%"},
                        ),
                        title="Tactical DNA Archetype Radar",
                        subtitle="Comparative mean fingerprint profiles across the 4 positional clusters",
                    ),
                    span={"base": 12, "lg": 5},
                ),
            ],
            gap="md",
        ),

        dmc.Space(h=16),

        # CLUSTER PROFILES COMPARISON TABLE
        create_section_card(
            html.Div(id="styles-summary-table-container", style={"overflowX": "auto"}),
            title="Cluster Attribute Means Matrix",
            subtitle="Mean percentile scores (0–100) across all 7 tactical dimensions for each identified archetype",
        ),

        dmc.Space(h=16),

        # REPRESENTATIVE ROSTER TABLE
        create_section_card(
            html.Div(id="styles-roster-table-container", style={"overflowX": "auto"}),
            title="Archetype Player Roster & Representatives",
            subtitle="Qualified candidates classified under the selected playing style archetype",
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
    Input("scout-analyst-mode", "data"),
)
def update_playing_styles(pos, cluster_filter, locator_player="NONE", scout_analyst_mode="scout"):
    scout_analyst_mode = scout_analyst_mode or "scout"
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
        traits_str = f"Signature Traits: {top_2[0][0]} ({top_2[0][1]:.1f}) • {top_2[1][0]} ({top_2[1][1]:.1f})"

        # Identify top recognizable anchors
        top_anchors = pos_players[pos_players["PlayingStyle_Cluster"] == c_id].sort_values("Min", ascending=False)["Player"].head(3).tolist()
        anchors_str = "Anchors: " + ", ".join(top_anchors) if top_anchors else ""

        cards.append(
            dmc.GridCol(
                dmc.Box(
                    [
                        dmc.Group([
                            dmc.Group([
                                html.Span("●", style={"color": color, "fontSize": "12px", "lineHeight": 1}),
                                dmc.Text(f"CLUSTER {c_id}", size="10px", fw=700, c="dimmed", style={"letterSpacing": "0.6px"}),
                            ], gap=6),
                            dmc.Text(f"{c_count} players ({c_pct:.1f}%)", size="10px", c="dimmed", style={"fontVariantNumeric": "tabular-nums"}),
                        ], justify="space-between"),
                        dmc.Title(c_name, order=4, c="white", mt=4, style={"fontSize": "15px"}),
                        dmc.Text(traits_str, size="10px", c="#CBD5E1", mt=4),
                        dmc.Text(anchors_str, size="9.5px", c="#94A3B8", mt=2, lineClamp=1),
                    ],
                    style={
                        "backgroundColor": "#0D131F",
                        "border": f"1px solid {color if is_selected else BORDER}",
                        "borderTop": f"2px solid {color}",
                        "borderRadius": "4px",
                        "padding": "12px 14px",
                    },
                ),
                span={"base": 12, "sm": 6, "lg": 3},
            )
        )

    guide_banner = dmc.Box(
        [
            dmc.Group([
                dmc.Text(f"EMPIRICAL {pos} TACTICAL ARCHETYPES (DATA-SUPPORTED)", size="10.5px", fw=800, c="teal", style={"letterSpacing": "0.8px"}),
                dmc.Badge(
                    "👤 SCOUT VIEW" if scout_analyst_mode == "scout" else "🔬 ANALYST VIEW",
                    color="teal" if scout_analyst_mode == "scout" else "indigo",
                    variant="filled",
                    size="xs",
                ),
            ], justify="space-between", align="center", mb="xs"),
            dmc.Text(
                f"The 4 {pos} playing styles below are derived through unsupervised K-Means clustering across 7 standardized match dimensions. "
                "Archetypes describe observed feature distributions and tactical roles directly from match event data, without imposing artificial axis definitions.",
                size="11px",
                c="#CBD5E1",
                style={"lineHeight": 1.45},
            ),
        ],
        style={
            "backgroundColor": "#0D131F",
            "border": f"1px solid {BORDER}",
            "borderLeft": "3px solid #10B981",
            "borderRadius": "4px",
            "padding": "10px 14px",
            "marginBottom": "12px",
        },
    )

    cards_container = html.Div([
        guide_banner,
        dmc.Grid(cards, gap="md"),
    ])

    # 2. PCA Scatter Plot with Optional Candidate Highlight Pin
    pca_fig = build_pca_cluster_scatter(
        df,
        pos=pos,
        selected_cluster=cluster_filter,
        highlight_player=locator_player,
        height=420,
    )

    # 3. Cluster DNA Radar
    radar_fig = build_cluster_dna_radar(summary_df, pos=pos, height=400)

    # 4. Cluster Summary Means Table
    thead_summary = dmc.TableThead(
        dmc.TableTr([
            dmc.TableTh("CLUSTER", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "width": "110px"}),
            dmc.TableTh("ARCHETYPE NAME", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh("PLAYERS", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh("FINISHING", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("CREATIVITY", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("PASSING", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("PROGRESSION", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("DEFENDING", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("SECURITY", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("AERIAL", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
        ])
    )

    summary_rows = []
    for idx, r in sub_summary.iterrows():
        c_id = int(r["PlayingStyle_Cluster"])
        color = CLUSTER_COLORS[c_id % len(CLUSTER_COLORS)]

        def fmt_cell(val):
            v = float(val)
            c = ACCENT if v >= 65 else "#38BDF8" if v >= 50 else "#F59E0B" if v >= 35 else "#EF4444"
            return dmc.TableTd(dmc.Text(f"{v:.1f}", fw=600, size="xs", style={"color": c, "fontVariantNumeric": "tabular-nums", "textAlign": "right"}))

        summary_rows.append(
            dmc.TableTr([
                dmc.TableTd(
                    dmc.Group([
                        html.Span("●", style={"color": color, "fontSize": "12px", "lineHeight": 1}),
                        dmc.Text(f"Cluster {c_id}", size="xs", fw=600, c="white"),
                    ], gap=6)
                ),
                dmc.TableTd(dmc.Text(r["Cluster_Name"], fw=600, size="xs", c="white")),
                dmc.TableTd(dmc.Text(str(int(r["Player_Count"])), size="xs", c="dimmed", style={"fontVariantNumeric": "tabular-nums"})),
                fmt_cell(r["Finishing"]),
                fmt_cell(r["Creativity"]),
                fmt_cell(r["Passing"]),
                fmt_cell(r["Progression"]),
                fmt_cell(r["Defending"]),
                fmt_cell(r["BallSecurity"]),
                fmt_cell(r["Aerial"]),
            ])
        )

    summary_table = dmc.Table(
        [thead_summary, dmc.TableTbody(summary_rows)],
        striped=True,
        highlightOnHover=True,
        withTableBorder=True,
        style={"backgroundColor": PANEL, "fontSize": "12px", "borderColor": BORDER},
    )

    # 5. Roster Table for Cluster
    roster_df = pos_players.copy()
    if cluster_filter != "ALL":
        c_num = int(cluster_filter)
        roster_df = roster_df[roster_df["PlayingStyle_Cluster"] == c_num]

    roster_df = roster_df.sort_values("Min", ascending=False).head(25)

    thead_roster = dmc.TableThead(
        dmc.TableTr([
            dmc.TableTh("PLAYER", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh("SQUAD", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh("ARCHETYPE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh("MINUTES", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh("G+A", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh("FIN", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("CRE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("PAS", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("PRG", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("DEF", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("ACTION", style={"color": TEXT, "textAlign": "center", "fontSize": "10px", "letterSpacing": "0.6px"}),
        ])
    )

    roster_rows = []
    for _, r in roster_df.iterrows():
        c_id = int(r["PlayingStyle_Cluster"])
        color = CLUSTER_COLORS[c_id % len(CLUSTER_COLORS)]
        profile_url = f"/player-profile?player={r['Player_Unique']}"
        ga = int(r.get("Gls", 0) + r.get("Ast", 0))
        mins = float(r.get("Min", 0))
        sample_pill = dmc.Badge(f"{int(mins)}m (Low)", color="orange", variant="outline", size="xs", style={"fontSize": "8.5px", "height": "14px", "padding": "0 3px"}) if mins < SAMPLE_SIZE_THRESHOLD else None

        roster_rows.append(
            dmc.TableTr([
                dmc.TableTd([
                    dmc.Group([
                        dmc.Text(r["Player"], fw=600, size="xs", c="white"),
                        *([sample_pill] if sample_pill else []),
                    ], gap=4, align="center"),
                ]),
                dmc.TableTd(dmc.Text(r["Squad"], size="xs", c="dimmed")),
                dmc.TableTd(
                    dmc.Badge(r.get("PlayingStyle_Name", f"Cluster {c_id}"), color="gray", variant="light", size="xs")
                ),
                dmc.TableTd(dmc.Text(f"{r['Min']:,}m", size="xs", c="dimmed", style={"fontVariantNumeric": "tabular-nums"})),
                dmc.TableTd(dmc.Text(str(ga), size="xs", fw=600, c="white", style={"fontVariantNumeric": "tabular-nums"})),
                dmc.TableTd(dmc.Text(f"{r['Finishing_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Finishing_Score'])["color"], "fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                dmc.TableTd(dmc.Text(f"{r['Creativity_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Creativity_Score'])["color"], "fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                dmc.TableTd(dmc.Text(f"{r['Passing_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Passing_Score'])["color"], "fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                dmc.TableTd(dmc.Text(f"{r['Progression_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Progression_Score'])["color"], "fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                dmc.TableTd(dmc.Text(f"{r['Defending_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Defending_Score'])["color"], "fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                dmc.TableTd(
                    dcc.Link(
                        dmc.Button("Dossier →", size="xs", variant="subtle", color="emerald"),
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
        style={"backgroundColor": PANEL, "fontSize": "12px", "borderColor": BORDER},
    )

    return cards_container, pca_fig, radar_fig, summary_table, roster_table
