import dash
from dash import html, dcc, Input, Output, callback
import dash_mantine_components as dmc
import plotly.graph_objects as go
import pandas as pd

from app.utils.data_loader import (
    load_data,
    get_player_by_name,
    get_all_player_names,
    get_unique_squads,
)
from app.utils.styling import (
    PANEL,
    BORDER,
    TEXT,
    MUTED,
    ACCENT,
    POSITION_COLORS,
    ATTRIBUTE_COLUMNS,
    create_page_header,
    create_section_card,
    get_percentile_tier,
)
from app.utils.similarity import find_similar_players
from app.utils.charts import build_radar_chart

dash.register_page(__name__, path="/similar-players", name="Similar Players", order=5)

df = load_data()
all_player_names = get_all_player_names()
unique_squads = get_unique_squads()

DEFAULT_PLAYER = "Trent Alexander-Arnold" if "Trent Alexander-Arnold" in all_player_names else all_player_names[0]


def layout(player=None, **kwargs):
    initial_player = player if player and get_player_by_name(player) is not None else DEFAULT_PLAYER

    return dmc.Container(
        [
            create_page_header(
                title="Similar Players",
                subtitle="Player recruitment & replacement modeling. Discover the closest statistical matches using position-standardized cosine similarity.",
                badge_text="COSINE SIMILARITY ENGINE",
            ),

            # FILTER AND CONFIG PANEL
            create_section_card(
                dmc.Grid(
                    [
                        dmc.GridCol(
                            dmc.Select(
                                id="similar-ref-player",
                                label="Target / Reference Player",
                                placeholder="Choose reference player...",
                                data=[{"label": name, "value": name} for name in all_player_names],
                                value=initial_player,
                                searchable=True,
                                allowDeselect=False,
                            ),
                            span={"base": 12, "sm": 6, "md": 4},
                        ),
                        dmc.GridCol(
                            dmc.Select(
                                id="similar-pos-filter",
                                label="Candidate Position Scope",
                                data=[
                                    {"label": "Same Position (Recommended)", "value": "SAME"},
                                    {"label": "All Positions (Cross-Position)", "value": "ALL"},
                                    {"label": "Defenders Only (DF)", "value": "DF"},
                                    {"label": "Midfielders Only (MF)", "value": "MF"},
                                    {"label": "Forwards Only (FW)", "value": "FW"},
                                ],
                                value="SAME",
                                allowDeselect=False,
                            ),
                            span={"base": 12, "sm": 6, "md": 3},
                        ),
                        dmc.GridCol(
                            dmc.Select(
                                id="similar-club-filter",
                                label="Filter Candidate Club",
                                data=[{"label": "All Clubs", "value": "ALL"}] + [
                                    {"label": s, "value": s} for s in unique_squads
                                ],
                                value="ALL",
                                searchable=True,
                                allowDeselect=False,
                            ),
                            span={"base": 12, "sm": 6, "md": 3},
                        ),
                        dmc.GridCol(
                            dmc.Select(
                                id="similar-top-n",
                                label="Results Count",
                                data=[
                                    {"label": "Top 5 Matches", "value": 5},
                                    {"label": "Top 10 Matches", "value": 10},
                                    {"label": "Top 15 Matches", "value": 15},
                                    {"label": "Top 20 Matches", "value": 20},
                                ],
                                value=10,
                                allowDeselect=False,
                            ),
                            span={"base": 12, "sm": 6, "md": 2},
                        ),
                    ],
                    gap="md",
                ),
                title="Similarity Query Parameters",
                subtitle="Select the benchmark player and configure candidate search constraints",
            ),

            dmc.Space(h=20),

            # REFERENCE PLAYER SUMMARY & BEST MATCH HIGHLIGHT
            html.Div(id="similar-banner-container"),

            dmc.Space(h=20),

            # COMPARISON RADAR: REFERENCE VS #1 MATCH
            dmc.Grid(
                [
                    dmc.GridCol(
                        create_section_card(
                            dcc.Graph(
                                id="similar-radar-chart",
                                config={"displayModeBar": False},
                                responsive=True,
                            ),
                            title="Reference vs Closest Match Radar",
                            subtitle="Direct 7D fingerprint comparison between reference and top statistical twin",
                        ),
                        span={"base": 12, "lg": 6},
                    ),
                    dmc.GridCol(
                        create_section_card(
                            html.Div(id="similar-methodology-container"),
                            title="Analytical Methodology & Match Quality",
                            subtitle="Algorithmic details and tactical interpretation of cosine similarity",
                        ),
                        span={"base": 12, "lg": 6},
                    ),
                ],
                gap="lg",
            ),

            dmc.Space(h=25),

            # SIMILAR PLAYERS LEADERBOARD TABLE
            create_section_card(
                html.Div(id="similar-table-container", style={"overflowX": "auto"}),
                title="Top Statistical Twins",
                subtitle="Ranked list of matching candidates with similarity indices and core percentiles",
            ),
        ],
        fluid=True,
        p=0,
    )


# --------------------------------------------------
# CALLBACK
# --------------------------------------------------

@callback(
    Output("similar-banner-container", "children"),
    Output("similar-radar-chart", "figure"),
    Output("similar-methodology-container", "children"),
    Output("similar-table-container", "children"),
    Input("similar-ref-player", "value"),
    Input("similar-pos-filter", "value"),
    Input("similar-club-filter", "value"),
    Input("similar-top-n", "value"),
)
def update_similar_players(ref_name, pos_filter, club_filter, top_n):
    ref_player = get_player_by_name(ref_name)
    if ref_player is None:
        ref_player = get_player_by_name(DEFAULT_PLAYER)

    top_n = int(top_n) if top_n else 10
    sim_results = find_similar_players(
        ref_player["Player_Unique"],
        position_filter=pos_filter,
        club_filter=club_filter,
        top_n=top_n,
    )

    # 1. Reference & Top Match Banner
    ref_pos_color = "blue" if ref_player["Pos"] == "DF" else "lime" if ref_player["Pos"] == "MF" else "orange"

    if not sim_results.empty:
        best_match = sim_results.iloc[0]
        match_pos_color = "blue" if best_match["Pos"] == "DF" else "lime" if best_match["Pos"] == "MF" else "orange"
        best_sim_pct = best_match["Similarity_Pct"]

        banner = dmc.Grid(
            [
                dmc.GridCol(
                    dmc.Card(
                        [
                            dmc.Text("REFERENCE PLAYER", size="xs", fw=700, c="dimmed"),
                            dmc.Title(ref_player["Player"], order=3, c="white", mt=4),
                            dmc.Group(
                                [
                                    dmc.Badge(ref_player["Pos"], color=ref_pos_color, variant="filled", size="xs"),
                                    dmc.Text(f"{ref_player['Squad']} • {ref_player.get('Nation_Display', ref_player['Nation_Clean'])}", size="xs", c="dimmed"),
                                    dmc.Text(f"Min: {ref_player['Min']:,}m", size="xs", c="dimmed"),
                                ],
                                gap="xs",
                                mt=6,
                            ),
                            dmc.Text(f"Tactical Style: {ref_player.get('PlayingStyle_Name', 'Specialist')}", size="xs", c="lime", mt=6),
                        ],
                        withBorder=True,
                        radius="md",
                        p="md",
                        style={"backgroundColor": PANEL, "borderColor": BORDER, "borderLeft": "3px solid #84CC16"},
                    ),
                    span={"base": 12, "md": 6},
                ),
                dmc.GridCol(
                    dmc.Card(
                        [
                            dmc.Group([
                                dmc.Text("#1 CLOSEST MATCH", size="xs", fw=700, c="dimmed"),
                                dmc.Badge(f"{best_sim_pct:.1f}% SIMILARITY", color="lime", variant="filled", size="sm"),
                            ], justify="space-between"),
                            dmc.Title(best_match["Player"], order=3, c="white", mt=4),
                            dmc.Group(
                                [
                                    dmc.Badge(best_match["Pos"], color=match_pos_color, variant="filled", size="xs"),
                                    dmc.Text(f"{best_match['Squad']} • {best_match.get('Nation_Display', best_match['Nation_Clean'])}", size="xs", c="dimmed"),
                                    dmc.Text(f"Min: {best_match['Min']:,}m", size="xs", c="dimmed"),
                                ],
                                gap="xs",
                                mt=6,
                            ),
                            dmc.Text(f"Tactical Style: {best_match.get('PlayingStyle_Name', 'Specialist')}", size="xs", c="cyan", mt=6),
                        ],
                        withBorder=True,
                        radius="md",
                        p="md",
                        style={"backgroundColor": PANEL, "borderColor": BORDER, "borderLeft": "3px solid #38BDF8"},
                    ),
                    span={"base": 12, "md": 6},
                ),
            ],
            gap="md",
        )
    else:
        banner = dmc.Alert(
            "No matching candidates found for the specified position and club filters.",
            title="Empty Results",
            color="yellow",
            variant="light",
        )

    # 2. Radar Chart (Reference vs Top Match)
    if not sim_results.empty:
        compare_players = [ref_player, sim_results.iloc[0]]
        radar_fig = build_radar_chart(players=compare_players, height=380)
    else:
        radar_fig = build_radar_chart(players=[ref_player], height=380)

    # 3. Methodology & Context
    methodology = html.Div([
        dmc.Text(
            "SCOUT's similarity algorithm computes cosine distance across the 7 engineered percentile dimensions: "
            "Finishing, Creativity, Passing, Progression, Defending, Ball Security, and Aerial duel dominance.",
            size="sm",
            c="white",
            style={"lineHeight": 1.6},
        ),
        dmc.Divider(my="sm"),
        dmc.Text("KEY SCOUTING APPLICATIONS", size="xs", fw=700, c="lime", mb=6),
        html.Ul([
            html.Li(dmc.Text("Replacement Recruitment: Identify tactical successors who replicate outgoing key contributors.", size="xs", c="dimmed")),
            html.Li(dmc.Text("Value Arbitrage: Discover lower-profile or budget alternatives in less commercial leagues with equivalent output.", size="xs", c="dimmed")),
            html.Li(dmc.Text("Positional Transitions: Explore players in adjacent positions displaying the technical profile required for tactical role shifts.", size="xs", c="dimmed")),
        ], style={"paddingLeft": "18px", "margin": 0}),
        dmc.Divider(my="sm"),
        dmc.Text(
            "Note: The reference player is always excluded from candidate results to guarantee valid recommendations.",
            size="xs",
            c="dimmed",
        ),
    ])

    # 4. Similar Players Table
    if sim_results.empty:
        table_container = dmc.Alert(
            "No candidates satisfied the filter constraints.",
            color="yellow",
            variant="light",
        )
        return banner, radar_fig, methodology, table_container

    thead = dmc.TableThead(
        dmc.TableTr([
            dmc.TableTh("Rank", style={"color": TEXT}),
            dmc.TableTh("Player", style={"color": TEXT}),
            dmc.TableTh("Club", style={"color": TEXT}),
            dmc.TableTh("Pos", style={"color": TEXT}),
            dmc.TableTh("Nat", style={"color": TEXT}),
            dmc.TableTh("Similarity", style={"color": TEXT}),
            dmc.TableTh("Tactical Archetype", style={"color": TEXT}),
            dmc.TableTh("Finishing", style={"color": TEXT}),
            dmc.TableTh("Creativity", style={"color": TEXT}),
            dmc.TableTh("Passing", style={"color": TEXT}),
            dmc.TableTh("Progression", style={"color": TEXT}),
            dmc.TableTh("Defending", style={"color": TEXT}),
            dmc.TableTh("Security", style={"color": TEXT}),
            dmc.TableTh("Aerial", style={"color": TEXT}),
            dmc.TableTh("Action", style={"color": TEXT, "textAlign": "center"}),
        ])
    )

    rows = []
    for rank, (_, r) in enumerate(sim_results.iterrows(), start=1):
        pos_badge_color = "blue" if r["Pos"] == "DF" else "lime" if r["Pos"] == "MF" else "orange"
        sim_pct = r["Similarity_Pct"]
        sim_color = "#84CC16" if sim_pct >= 95 else "#38BDF8" if sim_pct >= 85 else "#F59E0B"

        profile_url = f"/player-profile?player={r['Player_Unique']}"

        rows.append(
            dmc.TableTr([
                dmc.TableTd(dmc.Badge(f"#{rank}", color="gray", variant="light", size="sm")),
                dmc.TableTd(dmc.Text(r["Player"], size="sm", fw=600, c="white")),
                dmc.TableTd(dmc.Text(r["Squad"], size="xs", c="dimmed")),
                dmc.TableTd(dmc.Badge(r["Pos"], color=pos_badge_color, variant="light", size="xs")),
                dmc.TableTd(dmc.Text(r.get("Nation_Display", r["Nation_Clean"]), size="xs", c="dimmed")),
                dmc.TableTd(
                    dmc.Badge(f"{sim_pct:.1f}%", style={"backgroundColor": "rgba(23, 36, 56, 0.9)", "color": sim_color, "border": f"1px solid {sim_color}"}, size="sm")
                ),
                dmc.TableTd(dmc.Text(r.get("PlayingStyle_Name", "Specialist"), size="xs", c="dimmed")),

                dmc.TableTd(dmc.Text(f"{r['Finishing_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Finishing_Score'])["color"]})),
                dmc.TableTd(dmc.Text(f"{r['Creativity_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Creativity_Score'])["color"]})),
                dmc.TableTd(dmc.Text(f"{r['Passing_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Passing_Score'])["color"]})),
                dmc.TableTd(dmc.Text(f"{r['Progression_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Progression_Score'])["color"]})),
                dmc.TableTd(dmc.Text(f"{r['Defending_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Defending_Score'])["color"]})),
                dmc.TableTd(dmc.Text(f"{r['BallSecurity_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['BallSecurity_Score'])["color"]})),
                dmc.TableTd(dmc.Text(f"{r['Aerial_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Aerial_Score'])["color"]})),

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

    tbody = dmc.TableTbody(rows)
    table = dmc.Table(
        [thead, tbody],
        striped=True,
        highlightOnHover=True,
        withTableBorder=True,
        style={"backgroundColor": PANEL, "fontSize": "13px", "borderColor": BORDER},
    )

    return banner, radar_fig, methodology, table

