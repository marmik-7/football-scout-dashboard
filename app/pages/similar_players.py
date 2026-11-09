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
from app.utils.similarity import find_similar_players, explain_similarity
from app.utils.metric_definitions import get_sample_size_badge, SAMPLE_SIZE_THRESHOLD
from app.utils.charts import build_radar_chart
from app.utils.player_portraits import render_player_portrait

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

            # FILTER AND CONFIG PANEL (LAYER 1 + LAYER 2 PROGRESSIVE DISCLOSURE)
            create_section_card(
                dmc.Box([
                    # Row 1: Primary Query Controls (Immediate)
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
                                span={"base": 12, "sm": 6, "md": 5},
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
                                span={"base": 12, "sm": 6, "md": 3.5},
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
                                span={"base": 12, "sm": 6, "md": 3.5},
                            ),
                        ],
                        gap="sm",
                    ),

                    # Layer 2: Progressive Disclosure for Secondary Filters
                    dmc.Accordion(
                        styles={
                            "item": {"border": "none", "backgroundColor": "transparent"},
                            "control": {
                                "padding": "6px 0px",
                                "color": "var(--scout-text-secondary)",
                                "&:hover": {"backgroundColor": "transparent"},
                            },
                            "panel": {"padding": "8px 0px 0px 0px"},
                        },
                        children=[
                            dmc.AccordionItem(
                                [
                                    dmc.AccordionControl(
                                        dmc.Group([
                                            dmc.Text("Advanced Scope & Candidate Filters", size="xs", fw=600, c="var(--scout-text-secondary)"),
                                            dmc.Text("Sub-Role, League Scope, Club Filter & Results Depth", size="xs", c="dimmed"),
                                        ], gap="xs")
                                    ),
                                    dmc.AccordionPanel(
                                        dmc.Box([
                                            dmc.Divider(mb="sm", color="var(--scout-border-subtle)"),
                                            dmc.Grid(
                                                [
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
                                                        span={"base": 12, "sm": 6, "md": 4},
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
                                                        span={"base": 12, "sm": 6, "md": 4},
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
                                                        span={"base": 12, "sm": 6, "md": 4},
                                                    ),
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
                                                        span={"base": 12, "md": 12},
                                                    ),
                                                ],
                                                gap="sm",
                                            ),
                                        ])
                                    ),
                                ],
                                value="advanced",
                            )
                        ],
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
                                style={"height": "380px", "width": "100%"},
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
    Input("scout-analyst-mode", "data"),
    Input("theme-store", "data"),
)
def update_similar_players(ref_name, pos_filter, subrole_filter, club_filter, comp_filter, max_age, top_n, scout_analyst_mode="scout", theme="dark"):
    scout_analyst_mode = scout_analyst_mode or "scout"
    theme = theme or "dark"
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
    ref_sample_badge = get_sample_size_badge(ref_player.get("Min", 0))

    if not sim_results.empty:
        best_match = sim_results.iloc[0]
        match_pos_color = "blue" if best_match["Pos"] == "DF" else "emerald" if best_match["Pos"] == "MF" else "orange"
        best_sim_pct = best_match["Similarity_Pct"]
        match_sample_badge = get_sample_size_badge(best_match.get("Min", 0))
        sim_explanation = explain_similarity(ref_player, best_match)

        banner = dmc.Grid(
            [
                dmc.GridCol(
                    dmc.Box(
                        [
                            dmc.Group([
                                dmc.Text("REFERENCE BENCHMARK", size="10px", fw=700, c="dimmed", style={"letterSpacing": "0.8px"}),
                                *([ref_sample_badge] if ref_sample_badge else []),
                            ], justify="space-between", align="center"),
                            dmc.Group([
                                render_player_portrait(ref_player["Player_Unique"], size=44, radius=6),
                                dmc.Box([
                                    dmc.Title(ref_player["Player"], order=3, c="var(--scout-text-primary)", style={"fontSize": "18px"}),
                                    dmc.Group(
                                        [
                                            dmc.Badge(ref_player["Pos"], color=ref_pos_color, variant="filled", size="xs"),
                                            dmc.Badge(ref_player.get("SubRole", "Specialist"), color="cyan", variant="light", size="xs"),
                                            dmc.Text(f"{ref_player.get('Nation_Display', ref_player['Nation_Clean'])} • {ref_player['Squad']} • {ref_player.get('Comp_Clean', 'Big 5')}", size="xs", c="dimmed"),
                                            dmc.Text(f"Min: {ref_player['Min']:,}m", size="xs", c="dimmed", style={"fontVariantNumeric": "tabular-nums"}),
                                        ],
                                        gap="xs",
                                        mt=4,
                                        wrap="wrap",
                                    ),
                                ]),
                            ], gap="sm", align="center", mt=6),
                            dmc.Text(f"Tactical Style: {ref_player.get('PlayingStyle_Name', 'Specialist')}", size="xs", style={"color": ACCENT}, mt=6),
                        ],
                        style={
                            "backgroundColor": "var(--scout-surface-secondary)",
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
                                dmc.Group([
                                    dmc.Text("#1 STATISTICAL TWIN", size="10px", fw=700, c="dimmed", style={"letterSpacing": "0.8px"}),
                                    *([match_sample_badge] if match_sample_badge else []),
                                ], gap="xs", align="center"),
                                dmc.Badge(f"{best_sim_pct:.1f}% SIMILARITY", color="emerald", variant="filled", size="sm"),
                            ], justify="space-between"),
                            dmc.Group([
                                render_player_portrait(best_match["Player_Unique"], size=44, radius=6),
                                dmc.Box([
                                    dmc.Title(best_match["Player"], order=3, c="var(--scout-text-primary)", style={"fontSize": "18px"}),
                                    dmc.Group(
                                        [
                                            dmc.Badge(best_match["Pos"], color=match_pos_color, variant="filled", size="xs"),
                                            dmc.Badge(best_match.get("SubRole", "Specialist"), color="cyan", variant="light", size="xs"),
                                            dmc.Badge(sim_explanation.get("positional_compat_level", "Direct"), color="teal" if sim_explanation.get("positional_compat_level") == "Direct" else "orange", variant="outline", size="xs"),
                                            dmc.Text(f"{best_match.get('Nation_Display', best_match['Nation_Clean'])} • {best_match['Squad']} • {best_match.get('Comp_Clean', 'Big 5')}", size="xs", c="dimmed"),
                                            dmc.Text(f"Min: {best_match['Min']:,}m", size="xs", c="dimmed", style={"fontVariantNumeric": "tabular-nums"}),
                                        ],
                                        gap="xs",
                                        mt=4,
                                        wrap="wrap",
                                    ),
                                ]),
                            ], gap="sm", align="center", mt=6),
                            dmc.Text(f"Succession Horizon: {sim_explanation.get('succession_note', '')}", size="xs", c="cyan", mt=6),
                        ],
                        style={
                            "backgroundColor": "var(--scout-surface-secondary)",
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
        sim_explanation = {}

    # 2. Radar Chart (Reference vs Top Match)
    if not sim_results.empty:
        compare_players = [ref_player, sim_results.iloc[0]]
        radar_fig = build_radar_chart(players=compare_players, height=370, theme=theme)
    else:
        radar_fig = build_radar_chart(players=[ref_player], height=370, theme=theme)

    # 3. Methodology & Explainable Drivers of Similarity
    shared_items = [
        html.Li(dmc.Text(s, size="xs", c="var(--scout-text-secondary)", style={"lineHeight": 1.4}), style={"marginBottom": "3px"})
        for s in sim_explanation.get("shared_strengths", [])
    ]
    diff_items = [
        html.Li(dmc.Text(d, size="xs", c="var(--scout-text-secondary)", style={"lineHeight": 1.4}), style={"marginBottom": "3px"})
        for d in sim_explanation.get("key_differences", [])
    ]

    methodology_children = [
        # Prominent Tactical Disclaimer
        dmc.Alert(
            "NOTICE: Statistical similarity models numerical volume across match events, not tactical interchangeability. Video scouting and physical screening required prior to recruitment decisions.",
            color="teal",
            variant="light",
            radius="sm",
            style={"fontSize": "11px", "padding": "8px 12px", "marginBottom": "12px"},
        ),

        dmc.Text("THE 3 DRIVERS OF SIMILARITY (#1 CANDIDATE)", size="10px", fw=800, c="teal", style={"letterSpacing": "0.8px"}, mb=6),

        # Driver 1: Shared Core Strengths
        dmc.Text("Strongest Shared Tactical Attributes:", size="10.5px", fw=700, c="#10B981", mt=4),
        html.Ul(shared_items, style={"paddingLeft": "16px", "margin": "4px 0"}),

        # Driver 2: Key Differences
        dmc.Text("Key Tactical Differences & Variance:", size="10.5px", fw=700, c="#F59E0B", mt=6),
        html.Ul(diff_items, style={"paddingLeft": "16px", "margin": "4px 0"}),

        # Driver 3: Succession & Role Suitability
        dmc.Text("Succession & Positional Compatibility:", size="10.5px", fw=700, c="#38BDF8", mt=6),
        dmc.Text(
            f"Role Relationship: {sim_explanation.get('positional_compatibility', 'N/A')}. {sim_explanation.get('succession_note', '')}",
            size="xs",
            c="var(--scout-text-secondary)",
            mt=2,
        ),
    ]

    if scout_analyst_mode == "analyst":
        methodology_children.extend([
            dmc.Divider(my="xs", color=BORDER),
            dmc.Text("ANALYST METHODOLOGY & MATHEMATICAL FORMULATION", size="10px", fw=700, c="dimmed", style={"letterSpacing": "0.6px"}, mb=4),
            dmc.Text(
                "Cosine similarity calculated over 7 position-standardized Z-score vectors (Finishing, Creativity, Passing, Progression, Defending pAdj, Ball Security, Aerial). "
                "Feature scaling applies StandardScaler(with_mean=True, with_std=True) within position cohorts.",
                size="10px",
                c="var(--scout-text-muted)",
                style={"lineHeight": 1.45},
            ),
        ])

    methodology = html.Div(methodology_children)

    # 4. Similar Players Table
    if sim_results.empty:
        table_container = dmc.Alert(
            "No candidates satisfied the filter constraints.",
            color="yellow",
            variant="light",
            radius="sm",
        )
        return banner, radar_fig, methodology, table_container

    if scout_analyst_mode == "scout":
        thead = dmc.TableThead(
            dmc.TableTr([
                dmc.TableTh("RANK", style={"color": TEXT, "width": "50px", "fontSize": "10px", "letterSpacing": "0.6px"}),
                dmc.TableTh("CANDIDATE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
                dmc.TableTh("SQUAD / LEAGUE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
                dmc.TableTh("ROLE DNA", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
                dmc.TableTh("SIMILARITY", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
                dmc.TableTh("MATCH TIER", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
                dmc.TableTh("ACTION", style={"color": TEXT, "textAlign": "center", "fontSize": "10px", "letterSpacing": "0.6px"}),
            ])
        )
    else:
        thead = dmc.TableThead(
            dmc.TableTr([
                dmc.TableTh("RANK", style={"color": TEXT, "width": "50px", "fontSize": "10px", "letterSpacing": "0.6px"}),
                dmc.TableTh("CANDIDATE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
                dmc.TableTh("SQUAD / LEAGUE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
                dmc.TableTh("ROLE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
                dmc.TableTh("NAT", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
                dmc.TableTh("SIMILARITY", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
                dmc.TableTh("MATCH TIER", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
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
        mins = float(r.get("Min", 0))

        if rank == 1:
            rank_badge = dmc.Badge(f"#{rank}", color="yellow", variant="filled", size="xs")
        elif rank == 2:
            rank_badge = dmc.Badge(f"#{rank}", color="gray", variant="light", size="xs")
        elif rank == 3:
            rank_badge = dmc.Badge(f"#{rank}", color="orange", variant="light", size="xs")
        else:
            rank_badge = dmc.Text(f"#{rank}", size="xs", c="dimmed", style={"fontVariantNumeric": "tabular-nums"})

        # Match Tier
        if sim_pct >= 95.0:
            tier_badge = dmc.Badge("Direct Twin", color="emerald", variant="light", size="xs")
        elif sim_pct >= 88.0:
            tier_badge = dmc.Badge("Strong Match", color="cyan", variant="light", size="xs")
        else:
            tier_badge = dmc.Badge("Partial Match", color="orange", variant="light", size="xs")

        profile_url = f"/player-profile?player={r['Player_Unique']}"

        sample_pill = dmc.Badge(f"{int(mins)}m (Low)", color="orange", variant="outline", size="xs", style={"fontSize": "8.5px", "height": "14px", "padding": "0 3px", "marginLeft": "4px"}) if mins < SAMPLE_SIZE_THRESHOLD else None

        if scout_analyst_mode == "scout":
            row_cells = [
                dmc.TableTd(rank_badge),
                dmc.TableTd([
                    dmc.Group([
                        render_player_portrait(r["Player_Unique"], size=32, radius=4),
                        dmc.Box([
                            dmc.Group([
                                dmc.Text(r["Player"], size="xs", fw=600, c="var(--scout-text-primary)"),
                                *([sample_pill] if sample_pill else []),
                            ], gap=4, align="center"),
                            dmc.Text(f"{r.get('Nation_Display', r['Nation_Clean'])} • Age {r.get('Age', '-')} • {int(mins):,} mins", size="10px", c="dimmed"),
                        ]),
                    ], gap="xs", align="center", wrap="nowrap"),
                ]),
                dmc.TableTd([
                    dmc.Text(r["Squad"], size="xs", fw=500, c="var(--scout-text-primary)"),
                    dmc.Text(r.get("Comp_Clean", ""), size="10px", c="dimmed"),
                ]),
                dmc.TableTd([
                    dmc.Badge(r["Pos"], color=pos_badge_color, variant="light", size="xs"),
                    dmc.Text(r.get("SubRole", ""), size="10px", c="dimmed", mt=2),
                ]),
                dmc.TableTd(
                    dmc.Badge(
                        f"{sim_pct:.1f}%",
                        size="xs",
                        variant="light",
                        color="emerald" if sim_pct >= 95 else "cyan" if sim_pct >= 88 else "orange",
                    )
                ),
                dmc.TableTd(tier_badge),
                dmc.TableTd(
                    dcc.Link(
                        dmc.Button("Dossier →", size="xs", variant="subtle", color="emerald"),
                        href=profile_url,
                        style={"textDecoration": "none"},
                    ),
                    style={"textAlign": "center"},
                ),
            ]
        else:
            row_cells = [
                dmc.TableTd(rank_badge),
                dmc.TableTd([
                    dmc.Group([
                        render_player_portrait(r["Player_Unique"], size=32, radius=4),
                        dmc.Box([
                            dmc.Group([
                                dmc.Text(r["Player"], size="xs", fw=600, c="var(--scout-text-primary)"),
                                *([sample_pill] if sample_pill else []),
                            ], gap=4, align="center"),
                            dmc.Text(f"{r.get('Nation_Display', r['Nation_Clean'])} • Age {r.get('Age', '-')} • {int(mins):,} mins", size="10px", c="dimmed"),
                        ]),
                    ], gap="xs", align="center", wrap="nowrap"),
                ]),
                dmc.TableTd([
                    dmc.Text(r["Squad"], size="xs", fw=500, c="var(--scout-text-primary)"),
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
                        color="emerald" if sim_pct >= 95 else "cyan" if sim_pct >= 88 else "orange",
                    )
                ),
                dmc.TableTd(tier_badge),
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
            ]

        rows.append(dmc.TableTr(row_cells))

    tbody = dmc.TableTbody(rows)
    table = dmc.Table(
        [thead, tbody],
        striped=True,
        highlightOnHover=True,
        withTableBorder=True,
        style={"backgroundColor": PANEL, "fontSize": "12px", "borderColor": BORDER},
    )

    return banner, radar_fig, methodology, table
