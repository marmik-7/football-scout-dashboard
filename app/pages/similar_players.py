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
    get_unique_competitions,
    get_unique_subroles,
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
unique_competitions = get_unique_competitions()
unique_subroles = get_unique_subroles()

DEFAULT_PLAYER = "Trent Alexander-Arnold" if "Trent Alexander-Arnold" in all_player_names else all_player_names[0]


def layout(player=None, **kwargs):
    initial_player = player if player and get_player_by_name(player) is not None else DEFAULT_PLAYER

    return dmc.Container(
        [
            create_page_header(
                title="Statistical Twins",
                subtitle="Recruitment target discovery and succession modeling. Pinpoint closest statistical matches using 7D cosine similarity.",
                badge_text="SIMILARITY ENGINE",
            ),

            # FILTER AND CONFIG PANEL
            create_section_card(
                dmc.Box([
                    # Row 1: Reference Player & Positional / Geographic Filters
                    dmc.Grid(
                        [
                            dmc.GridCol(
                                dmc.Select(
                                    id="similar-ref-player",
                                    label="Reference Benchmark Player",
                                    placeholder="Choose reference player...",
                                    data=[{"label": name, "value": name} for name in all_player_names],
                                    value=initial_player,
                                    searchable=True,
                                    allowDeselect=False,
                                ),
                                span={"base": 12, "sm": 6, "md": 3},
                            ),
                            dmc.GridCol(
                                dmc.Select(
                                    id="similar-pos-filter",
                                    label="Position Scope",
                                    data=[
                                        {"label": "Same Position Group", "value": "SAME"},
                                        {"label": "All Positions (Cross-Position)", "value": "ALL"},
                                        {"label": "Defenders Only (DF)", "value": "DF"},
                                        {"label": "Midfielders Only (MF)", "value": "MF"},
                                        {"label": "Forwards Only (FW)", "value": "FW"},
                                    ],
                                    value="SAME",
                                    allowDeselect=False,
                                ),
                                span={"base": 12, "sm": 6, "md": 2},
                            ),
                            dmc.GridCol(
                                dmc.Select(
                                    id="similar-subrole-filter",
                                    label="Tactical Sub-Role",
                                    data=[{"label": "All Sub-Roles", "value": "ALL"}] + [
                                        {"label": s, "value": s} for s in unique_subroles
                                    ],
                                    value="ALL",
                                    allowDeselect=False,
                                ),
                                span={"base": 12, "sm": 6, "md": 2.5},
                            ),
                            dmc.GridCol(
                                dmc.Select(
                                    id="similar-comp-filter",
                                    label="Target League",
                                    data=[{"label": "All 5 Leagues", "value": "ALL"}] + [
                                        {"label": c, "value": c} for c in unique_competitions
                                    ],
                                    value="ALL",
                                    allowDeselect=False,
                                ),
                                span={"base": 12, "sm": 6, "md": 2.5},
                            ),
                            dmc.GridCol(
                                dmc.Select(
                                    id="similar-age-filter",
                                    label="Succession Cap",
                                    data=[
                                        {"label": "Any Age", "value": "ALL"},
                                        {"label": "U-21 Only (≤21)", "value": "21"},
                                        {"label": "U-23 Only (≤23)", "value": "23"},
                                        {"label": "Peak / Young (≤26)", "value": "26"},
                                    ],
                                    value="ALL",
                                    allowDeselect=False,
                                ),
                                span={"base": 12, "sm": 6, "md": 2},
                            ),
                        ],
                        gap="sm",
                    ),

                    dmc.Space(h=10),

                    # Row 2: Candidate Club & Depth
                    dmc.Grid(
                        [
                            dmc.GridCol(
                                dmc.Select(
                                    id="similar-club-filter",
                                    label="Candidate Club",
                                    data=[{"label": "All Clubs", "value": "ALL"}] + [
                                        {"label": s, "value": s} for s in unique_squads
                                    ],
                                    value="ALL",
                                    searchable=True,
                                    allowDeselect=False,
                                ),
                                span={"base": 12, "sm": 8, "md": 9},
                            ),
                            dmc.GridCol(
                                dmc.Select(
                                    id="similar-top-n",
                                    label="Results Depth",
                                    data=[
                                        {"label": "Top 5 Candidates", "value": 5},
                                        {"label": "Top 10 Candidates", "value": 10},
                                        {"label": "Top 15 Candidates", "value": 15},
                                        {"label": "Top 20 Candidates", "value": 20},
                                    ],
                                    value=10,
                                    allowDeselect=False,
                                ),
                                span={"base": 12, "sm": 4, "md": 3},
                            ),
                        ],
                        gap="sm",
                    ),
                ]),
                title="Similarity Query Parameters",
                subtitle="Configure the target reference benchmark and candidate filtering criteria",
            ),

            dmc.Space(h=16),

            # REFERENCE PLAYER SUMMARY & BEST MATCH HIGHLIGHT
            html.Div(id="similar-banner-container"),

            dmc.Space(h=16),

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
                            title="Similarity Intelligence & Scouting Methodology",
                            subtitle="Algorithmic details and tactical interpretation of cosine similarity",
                        ),
                        span={"base": 12, "lg": 6},
                    ),
                ],
                gap="md",
            ),

            dmc.Space(h=16),

            # SIMILAR PLAYERS LEADERBOARD TABLE
            create_section_card(
                html.Div(id="similar-table-container", style={"overflowX": "auto"}),
                title="Top Statistical Twins",
                subtitle="Ranked candidate cohort with similarity indices, positional percentiles, and direct dossier navigation",
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
    Input("similar-subrole-filter", "value"),
    Input("similar-club-filter", "value"),
    Input("similar-comp-filter", "value"),
    Input("similar-age-filter", "value"),
    Input("similar-top-n", "value"),
)
def update_similar_players(ref_name, pos_filter, subrole_filter, club_filter, comp_filter, max_age, top_n):
    ref_player = get_player_by_name(ref_name)
    if ref_player is None:
        ref_player = get_player_by_name(DEFAULT_PLAYER)

    top_n = int(top_n) if top_n else 10
    sim_results = find_similar_players(
        ref_player["Player_Unique"],
        position_filter=pos_filter,
        club_filter=club_filter,
        comp_filter=comp_filter,
        max_age=max_age,
        subrole_filter=subrole_filter,
        top_n=top_n,
    )

    # 1. Reference & Top Match Banner
    ref_pos_color = "blue" if ref_player["Pos"] == "DF" else "emerald" if ref_player["Pos"] == "MF" else "orange"

    if not sim_results.empty:
        best_match = sim_results.iloc[0]
        match_pos_color = "blue" if best_match["Pos"] == "DF" else "emerald" if best_match["Pos"] == "MF" else "orange"
        best_sim_pct = best_match["Similarity_Pct"]

        banner = dmc.Grid(
            [
                dmc.GridCol(
                    dmc.Box(
                        [
                            dmc.Text("REFERENCE BENCHMARK", size="10px", fw=700, c="dimmed", style={"letterSpacing": "0.8px"}),
                            dmc.Title(ref_player["Player"], order=3, c="white", mt=2, style={"fontSize": "18px"}),
                            dmc.Group(
                                [
                                    dmc.Badge(ref_player["Pos"], color=ref_pos_color, variant="filled", size="xs"),
                                    dmc.Badge(ref_player.get("SubRole", "Specialist"), color="cyan", variant="light", size="xs"),
                                    dmc.Text(f"{ref_player['Squad']} • {ref_player.get('Comp_Clean', 'Big 5')}", size="xs", c="dimmed"),
                                    dmc.Text(f"Min: {ref_player['Min']:,}m", size="xs", c="dimmed", style={"fontVariantNumeric": "tabular-nums"}),
                                ],
                                gap="xs",
                                mt=6,
                            ),
                            dmc.Text(f"Tactical Style: {ref_player.get('PlayingStyle_Name', 'Specialist')}", size="xs", style={"color": ACCENT}, mt=4),
                        ],
                        style={
                            "backgroundColor": "#0D131F",
                            "border": f"1px solid {BORDER}",
                            "borderLeft": f"3px solid {ACCENT}",
                            "borderRadius": "4px",
                            "padding": "12px 16px",
                        },
                    ),
                    span={"base": 12, "md": 6},
                ),
                dmc.GridCol(
                    dmc.Box(
                        [
                            dmc.Group([
                                dmc.Text("#1 CLOSEST STATISTICAL TWIN", size="10px", fw=700, c="dimmed", style={"letterSpacing": "0.8px"}),
                                dmc.Badge(f"{best_sim_pct:.1f}% SIMILARITY", color="emerald", variant="filled", size="sm"),
                            ], justify="space-between"),
                            dmc.Title(best_match["Player"], order=3, c="white", mt=2, style={"fontSize": "18px"}),
                            dmc.Group(
                                [
                                    dmc.Badge(best_match["Pos"], color=match_pos_color, variant="filled", size="xs"),
                                    dmc.Badge(best_match.get("SubRole", "Specialist"), color="cyan", variant="light", size="xs"),
                                    dmc.Text(f"{best_match['Squad']} • {best_match.get('Comp_Clean', 'Big 5')}", size="xs", c="dimmed"),
                                    dmc.Text(f"Min: {best_match['Min']:,}m", size="xs", c="dimmed", style={"fontVariantNumeric": "tabular-nums"}),
                                ],
                                gap="xs",
                                mt=6,
                            ),
                            dmc.Text(f"Tactical Style: {best_match.get('PlayingStyle_Name', 'Specialist')}", size="xs", c="cyan", mt=4),
                        ],
                        style={
                            "backgroundColor": "#0D131F",
                            "border": f"1px solid {BORDER}",
                            "borderLeft": "3px solid #38BDF8",
                            "borderRadius": "4px",
                            "padding": "12px 16px",
                        },
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
            radius="sm",
        )

    # 2. Radar Chart (Reference vs Top Match)
    if not sim_results.empty:
        compare_players = [ref_player, sim_results.iloc[0]]
        radar_fig = build_radar_chart(players=compare_players, height=370)
    else:
        radar_fig = build_radar_chart(players=[ref_player], height=370)

    # 3. Methodology & Context
    methodology = html.Div([
        dmc.Text(
            "SCOUT's similarity algorithm computes multi-dimensional cosine distance across 7 position-standardized percentile dimensions: "
            "Finishing, Creativity, Passing, Progression, Defending (pAdj), Ball Security, and Aerial Dominance.",
            size="xs",
            c="#CBD5E1",
            style={"lineHeight": 1.6},
        ),
        dmc.Divider(my="xs", color=BORDER),
        dmc.Text("PRIMARY RECRUITMENT USE CASES", size="10px", fw=700, c="dimmed", style={"letterSpacing": "0.6px"}, mb=6),
        dmc.Stack([
            dmc.Box([
                dmc.Text("Replacement Succession:", size="xs", fw=600, style={"color": ACCENT}),
                dmc.Text("Identify direct tactical successors who replicate departing key starters' output.", size="10px", c="dimmed"),
            ]),
            dmc.Box([
                dmc.Text("Value Arbitrage:", size="xs", fw=600, c="cyan"),
                dmc.Text("Discover budget-friendly alternatives in secondary markets with equivalent production.", size="10px", c="dimmed"),
            ]),
            dmc.Box([
                dmc.Text("Positional Transitions:", size="xs", fw=600, c="orange"),
                dmc.Text("Find versatile candidates in adjacent positions displaying needed technical attributes.", size="10px", c="dimmed"),
            ]),
        ], gap="xs"),
        dmc.Divider(my="xs", color=BORDER),
        dmc.Text(
            "Note: The benchmark reference player is omitted from result sets to guarantee distinct candidate recommendations.",
            size="10px",
            c="dimmed",
        ),
    ])

    # 4. Similar Players Table
    if sim_results.empty:
        table_container = dmc.Alert(
            "No candidates satisfied the filter constraints.",
            color="yellow",
            variant="light",
            radius="sm",
        )
        return banner, radar_fig, methodology, table_container

    thead = dmc.TableThead(
        dmc.TableTr([
            dmc.TableTh("RANK", style={"color": TEXT, "width": "50px", "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh("CANDIDATE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh("SQUAD / LEAGUE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh("ROLE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh("NAT", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh("SIMILARITY", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh("TACTICAL DNA", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh("FIN", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("CRE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("PAS", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("PRG", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("DEF", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("SEC", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("AER", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("ACTION", style={"color": TEXT, "textAlign": "center", "fontSize": "10px", "letterSpacing": "0.6px"}),
        ])
    )

    rows = []
    for rank, (_, r) in enumerate(sim_results.iterrows(), start=1):
        pos_badge_color = "blue" if r["Pos"] == "DF" else "emerald" if r["Pos"] == "MF" else "orange"
        sim_pct = r["Similarity_Pct"]

        if rank == 1:
            rank_badge = dmc.Badge(f"#{rank}", color="yellow", variant="filled", size="xs")
        elif rank == 2:
            rank_badge = dmc.Badge(f"#{rank}", color="gray", variant="light", size="xs")
        elif rank == 3:
            rank_badge = dmc.Badge(f"#{rank}", color="orange", variant="light", size="xs")
        else:
            rank_badge = dmc.Text(f"#{rank}", size="xs", c="dimmed", style={"fontVariantNumeric": "tabular-nums"})

        sim_color = ACCENT if sim_pct >= 95 else "#38BDF8" if sim_pct >= 85 else "#F59E0B"
        profile_url = f"/player-profile?player={r['Player_Unique']}"

        rows.append(
            dmc.TableTr([
                dmc.TableTd(rank_badge),
                dmc.TableTd([
                    dmc.Text(r["Player"], size="xs", fw=600, c="white"),
                    dmc.Text(f"Age {r.get('Age', '-')}", size="10px", c="dimmed"),
                ]),
                dmc.TableTd([
                    dmc.Text(r["Squad"], size="xs", fw=500, c="white"),
                    dmc.Text(r.get("Comp_Clean", ""), size="10px", c="dimmed"),
                ]),
                dmc.TableTd([
                    dmc.Badge(r["Pos"], color=pos_badge_color, variant="light", size="xs"),
                    dmc.Text(r.get("SubRole", ""), size="10px", c="dimmed", mt=2),
                ]),
                dmc.TableTd(dmc.Text(r.get("Nation_Display", r["Nation_Clean"]), size="xs", c="dimmed")),
                dmc.TableTd(
                    dmc.Badge(
                        f"{sim_pct:.1f}%",
                        size="xs",
                        variant="light",
                        color="emerald" if sim_pct >= 95 else "cyan" if sim_pct >= 85 else "orange",
                    )
                ),
                dmc.TableTd(dmc.Text(r.get("PlayingStyle_Name", "Specialist"), size="xs", c="dimmed")),

                dmc.TableTd(dmc.Text(f"{r['Finishing_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Finishing_Score'])["color"], "fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                dmc.TableTd(dmc.Text(f"{r['Creativity_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Creativity_Score'])["color"], "fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                dmc.TableTd(dmc.Text(f"{r['Passing_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Passing_Score'])["color"], "fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                dmc.TableTd(dmc.Text(f"{r['Progression_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Progression_Score'])["color"], "fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                dmc.TableTd(dmc.Text(f"{r['Defending_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Defending_Score'])["color"], "fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                dmc.TableTd(dmc.Text(f"{r['BallSecurity_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['BallSecurity_Score'])["color"], "fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                dmc.TableTd(dmc.Text(f"{r['Aerial_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Aerial_Score'])["color"], "fontVariantNumeric": "tabular-nums", "textAlign": "right"})),

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

    tbody = dmc.TableTbody(rows)
    table = dmc.Table(
        [thead, tbody],
        striped=True,
        highlightOnHover=True,
        withTableBorder=True,
        style={"backgroundColor": PANEL, "fontSize": "12px", "borderColor": BORDER},
    )

    return banner, radar_fig, methodology, table
