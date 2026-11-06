import dash
from dash import html, dcc, Input, Output, State, callback
import dash_mantine_components as dmc
import plotly.graph_objects as go
import pandas as pd

from app.utils.data_loader import (
    load_data,
    get_player_by_name,
    get_all_player_names,
    get_position_averages,
)
from app.utils.styling import (
    PANEL,
    BORDER,
    TEXT,
    MUTED,
    ACCENT,
    POSITION_COLORS,
    POSITION_NAMES,
    ATTRIBUTE_COLUMNS,
    create_page_header,
    create_section_card,
    position_percentile_warning,
    get_percentile_tier,
)
from app.utils.charts import build_radar_chart, build_pizza_chart
from app.utils.player_analysis import (
    get_player_strengths_and_weaknesses,
    generate_scouting_report,
    get_player_attribute_comparison,
)

dash.register_page(__name__, path="/player-profile", name="Player Profile", order=3)

df = load_data()
all_player_names = get_all_player_names()

DEFAULT_PLAYER = "Erling Haaland" if "Erling Haaland" in all_player_names else all_player_names[0]


def layout(player=None, **kwargs):
    initial_player = player if player and get_player_by_name(player) is not None else DEFAULT_PLAYER

    return dmc.Container(
        [
            create_page_header(
                title="Player Dossier",
                subtitle="Deep technical evaluation, 12-slice percentile pizza, positional benchmarking, and tactical DNA.",
                badge_text="RECRUITMENT INTELLIGENCE",
            ),

            # COMMAND BAR: PLAYER SELECT & QUICK ACTIONS
            create_section_card(
                dmc.Grid(
                    [
                        dmc.GridCol(
                            dmc.Select(
                                id="profile-player-select",
                                label="Target Candidate Lookup",
                                placeholder="Search by player name...",
                                data=[{"label": name, "value": name} for name in all_player_names],
                                value=initial_player,
                                searchable=True,
                                allowDeselect=False,
                            ),
                            span={"base": 12, "md": 5},
                        ),
                        dmc.GridCol(
                            dmc.Group(
                                [
                                    dmc.Button(
                                        "★ Bookmark Target",
                                        id="profile-open-shortlist-btn",
                                        variant="filled",
                                        color="emerald",
                                        size="xs",
                                        style={"fontWeight": 600},
                                    ),
                                    dmc.Anchor(
                                        dmc.Button(
                                            "Direct Comparison →",
                                            variant="outline",
                                            color="gray",
                                            size="xs",
                                            style={"color": "#E2E8F0", "borderColor": BORDER},
                                        ),
                                        id="profile-compare-btn",
                                        href="/player-comparison",
                                    ),
                                    dmc.Anchor(
                                        dmc.Button(
                                            "Find Statistical Twins →",
                                            variant="light",
                                            color="emerald",
                                            size="xs",
                                        ),
                                        id="profile-similar-btn",
                                        href="/similar-players",
                                    ),
                                ],
                                gap="xs",
                                mt={"base": 0, "md": 24},
                            ),
                            span={"base": 12, "md": 7},
                        ),
                    ],
                    align="center",
                    gap="md",
                ),
                style={"marginBottom": "16px"},
            ),

            # BOOKMARK TO SHORTLIST MODAL
            dmc.Modal(
                id="profile-shortlist-modal",
                title=dmc.Group([
                    dmc.Badge("SHORTLIST", color="emerald", variant="filled", size="xs"),
                    dmc.Text("Add Candidate to Recruitment Pipeline", size="sm", fw=700, c="white"),
                ], gap="xs"),
                opened=False,
                centered=True,
                radius="sm",
                styles={"content": {"backgroundColor": PANEL, "borderColor": BORDER}},
                children=[
                    dmc.Box([
                        dmc.Text(id="profile-modal-player-title", fw=600, size="sm", c="white", mb="xs"),
                        dmc.Select(
                            id="profile-modal-tier",
                            label="Recruitment Priority Tier",
                            data=[
                                {"label": "★ A-List Target (Priority 1)", "value": "A-List Target"},
                                {"label": "◆ Primary Alternative (Priority 2)", "value": "Primary Alternative"},
                                {"label": "● Monitor / Development (Priority 3)", "value": "Monitor / Development"},
                            ],
                            value="A-List Target",
                            allowDeselect=False,
                            mb="sm",
                        ),
                        dmc.Textarea(
                            id="profile-modal-notes",
                            label="Scout Intelligence Notes",
                            placeholder="Add tactical observations, recruitment context, estimated valuation, or contract situation...",
                            minRows=3,
                            autosize=True,
                            mb="md",
                        ),
                        html.Div(id="profile-shortlist-feedback"),
                        dmc.Group([
                            dmc.Button("Cancel", id="profile-modal-cancel", variant="subtle", color="gray", size="xs"),
                            dmc.Button("Save Target", id="profile-modal-submit", variant="filled", color="emerald", size="xs"),
                        ], justify="flex-end"),
                    ]),
                ],
            ),

            # DYNAMIC PLAYER DOSSIER HEADER
            html.Div(id="profile-header-banner"),

            dmc.Space(h=16),

            # MAIN VISUAL PROFILE: 12-SLICE PIZZA / RADAR + ATTRIBUTE BREAKDOWN
            dmc.Grid(
                [
                    # LEFT: PIZZA / RADAR
                    dmc.GridCol(
                        create_section_card(
                            [
                                dcc.Graph(
                                    id="profile-radar-chart",
                                    config={"displayModeBar": False},
                                    responsive=True,
                                ),
                                dmc.Space(h=8),
                                html.Div(
                                    id="profile-chart-note",
                                    style={"textAlign": "center"},
                                ),
                            ],
                            title="Visual Scouting Footprint",
                            subtitle="Multidimensional footprint benchmarked against positional cohort",
                            extra_header=dmc.SegmentedControl(
                                id="profile-chart-type-toggle",
                                data=[
                                    {"label": "Percentile Pizza (12-Slice)", "value": "pizza"},
                                    {"label": "Radar Footprint (7D)", "value": "radar"},
                                ],
                                value="pizza",
                                size="xs",
                                color="emerald",
                            ),
                        ),
                        span={"base": 12, "lg": 6},
                    ),

                    # RIGHT: ATTRIBUTE PERCENTILE SPECTRUM
                    dmc.GridCol(
                        create_section_card(
                            html.Div(id="profile-attributes-breakdown"),
                            title="Attribute Percentile Spectrum",
                            subtitle="Engineered score cards and deviation from positional benchmark",
                        ),
                        span={"base": 12, "lg": 6},
                    ),
                ],
                gap="md",
            ),

            dmc.Space(h=16),

            # SCOUTING REPORT & MATCH PRODUCTION
            dmc.Grid(
                [
                    dmc.GridCol(
                        create_section_card(
                            html.Div(id="profile-scouting-summary"),
                            title="Tactical Assessment & Scouting Synthesis",
                            subtitle="Algorithmic strengths, developmental priorities, and recruitment summary",
                        ),
                        span={"base": 12, "md": 5},
                    ),
                    dmc.GridCol(
                        create_section_card(
                            html.Div(id="profile-stats-grid"),
                            title="Season Production Statistics",
                            subtitle="Key volume and efficiency metrics (2024–25 European Season)",
                            extra_header=dmc.SegmentedControl(
                                id="profile-metric-mode",
                                data=[
                                    {"label": "Standard Per-90 Rates", "value": "per90"},
                                    {"label": "Season Total Counts", "value": "total"},
                                ],
                                value="per90",
                                size="xs",
                                color="emerald",
                            ),
                        ),
                        span={"base": 12, "md": 7},
                    ),
                ],
                gap="md",
            ),

            dmc.Space(h=20),
            position_percentile_warning(),
        ],
        fluid=True,
        p=0,
    )


# --------------------------------------------------
# CALLBACKS
# --------------------------------------------------

@callback(
    Output("profile-header-banner", "children"),
    Output("profile-radar-chart", "figure"),
    Output("profile-chart-note", "children"),
    Output("profile-attributes-breakdown", "children"),
    Output("profile-scouting-summary", "children"),
    Output("profile-stats-grid", "children"),
    Output("profile-compare-btn", "href"),
    Output("profile-similar-btn", "href"),
    Input("profile-player-select", "value"),
    Input("profile-metric-mode", "value"),
    Input("profile-chart-type-toggle", "value"),
)
def update_player_profile(selected_name, metric_mode="per90", chart_type="pizza"):
    player = get_player_by_name(selected_name)
    if player is None:
        player = get_player_by_name(DEFAULT_PLAYER)

    name = player["Player"]
    club = player["Squad"]
    comp = player.get("Comp_Clean", "Big 5")
    pos = player["Pos"]
    pos_name = POSITION_NAMES.get(pos, pos)
    subrole = player.get("SubRole", "Tactical Specialist")
    nation = player.get("Nation_Display", player["Nation_Clean"])
    age = player["Age"]
    born = player["Born"]
    minutes = player["Min"]
    style_name = player.get("PlayingStyle_Name", "Tactical Specialist")

    pos_badge_color = "blue" if pos == "DF" else "emerald" if pos == "MF" else "orange"

    # 1. Dossier Header Banner (Linear / Pitch Black aesthetic)
    header = dmc.Box(
        [
            dmc.Group(
                [
                    dmc.Text("SCOUTING DOSSIER", size="10px", fw=700, c="dimmed", style={"letterSpacing": "1px"}),
                    dmc.Text("/", size="xs", c="dimmed"),
                    dmc.Text(comp, size="xs", fw=600, c="dimmed"),
                    dmc.Text("/", size="xs", c="dimmed"),
                    dmc.Text(name, size="xs", fw=700, style={"color": ACCENT}),
                ],
                gap="xs",
                mb="xs",
            ),
            dmc.Group(
                [
                    dmc.Box([
                        dmc.Group(
                            [
                                dmc.Title(name, order=2, c="white", style={"fontSize": "22px", "fontWeight": 700}),
                                dmc.Badge(pos_name, color=pos_badge_color, variant="filled", size="sm"),
                                dmc.Badge(subrole, color="cyan", variant="light", size="sm"),
                            ],
                            gap="xs",
                            wrap="wrap",
                            align="center",
                        ),
                        dmc.Group(
                            [
                                dmc.Text(club, size="xs", fw=600, c="white"),
                                dmc.Text("•", c="dimmed"),
                                dmc.Text(nation, size="xs", c="dimmed"),
                                dmc.Text("•", c="dimmed"),
                                dmc.Text(f"Age {age} ({born})", size="xs", c="dimmed"),
                                dmc.Text("•", c="dimmed"),
                                dmc.Text(f"{minutes:,} mins ({minutes/90:.1f} 90s)", size="xs", c="dimmed", style={"fontVariantNumeric": "tabular-nums"}),
                            ],
                            gap="xs",
                            mt=6,
                            wrap="wrap",
                        ),
                    ]),
                    dmc.Box(
                        [
                            dmc.Text("PLAYING STYLE DNA", size="10px", fw=700, c="dimmed", style={"letterSpacing": "0.8px"}),
                            dmc.Badge(style_name, color="emerald", variant="outline", size="md", mt=4),
                        ],
                        style={"textAlign": "right"},
                    ),
                ],
                justify="space-between",
                align="center",
                wrap="wrap",
            ),
        ],
        style={
            "backgroundColor": PANEL,
            "border": f"1px solid {BORDER}",
            "borderRadius": "6px",
            "padding": "16px 20px",
        },
    )

    # 2. Visual Scouting Footprint (Pizza Chart vs Radar)
    if chart_type == "radar":
        pos_avgs = get_position_averages(pos)
        chart_fig = build_radar_chart(
            players=[player],
            include_position_avg=True,
            position_avg_scores=pos_avgs,
            height=370,
        )
        chart_note = dmc.Text(
            "7-Dimensional Scouting Radar: Dashed grey line represents position peer group average (50.0 baseline).",
            size="xs",
            c="dimmed",
            mt=4,
        )
    else:
        chart_fig = build_pizza_chart(player, height=390)
        chart_note = dmc.Text(
            "12-Slice Percentile Pizza: Uniform angular wedges grouped by Attacking, Possession, and Defending.",
            size="xs",
            c="dimmed",
            mt=4,
        )

    # 3. Attribute Breakdown Progress Bars (Clean Linear-style meters)
    comparisons = get_player_attribute_comparison(player)
    attribute_cards = []

    for item in comparisons:
        attr = item["attribute"]
        score = item["player_score"]
        pos_avg = item["position_avg"]
        diff = item["diff"]

        tier_info = get_percentile_tier(score)
        status = tier_info["tier"]
        bar_color = tier_info["badge_color"]

        diff_str = f"+{diff:.1f}" if diff > 0 else f"{diff:.1f}"
        diff_color = ACCENT if diff >= 0 else "#F59E0B"

        attribute_cards.append(
            dmc.Box(
                [
                    dmc.Group(
                        [
                            dmc.Group([
                                dmc.Text(attr, size="xs", fw=600, c="white"),
                                dmc.Badge(status, color=bar_color, variant="light", size="xs"),
                            ], gap="xs"),
                            dmc.Group(
                                [
                                    dmc.Text(
                                        f"{score:.1f}th pct",
                                        size="xs",
                                        fw=700,
                                        style={"color": tier_info["color"], "fontVariantNumeric": "tabular-nums"},
                                    ),
                                    dmc.Text(
                                        f"({diff_str} vs avg)",
                                        size="10px",
                                        style={"color": diff_color, "fontVariantNumeric": "tabular-nums"},
                                    ),
                                ],
                                gap="xs",
                            ),
                        ],
                        justify="space-between",
                        mb=4,
                    ),
                    dmc.Progress(value=score, color=bar_color, size="xs", radius="sm"),
                ],
                mb="sm",
            )
        )

    attributes_breakdown = html.Div(attribute_cards)

    # 4. Tactical Assessment & Scouting Synthesis
    strengths, weaknesses = get_player_strengths_and_weaknesses(player)
    report_text = generate_scouting_report(player)

    scouting_summary = html.Div([
        dmc.Text(report_text, size="xs", c="#CBD5E1", style={"lineHeight": 1.65}),
        dmc.Divider(my="sm", color=BORDER),
        dmc.Text("PRIMARY TECHNICAL ASSETS", size="10px", fw=700, c="dimmed", style={"letterSpacing": "0.6px"}, mb=6),
        dmc.Group(
            [
                dmc.Badge(
                    f"{s['attribute']} ({s['score']:.1f})",
                    color="emerald",
                    variant="light",
                    size="xs",
                )
                for s in strengths
            ],
            gap="xs",
            mb="md",
            wrap="wrap",
        ),
        dmc.Text("DEVELOPMENTAL & TACTICAL PRIORITIES", size="10px", fw=700, c="dimmed", style={"letterSpacing": "0.6px"}, mb=6),
        dmc.Group(
            [
                dmc.Badge(
                    f"{w['attribute']} ({w['score']:.1f})",
                    color="orange",
                    variant="light",
                    size="xs",
                )
                for w in weaknesses
            ],
            gap="xs",
            wrap="wrap",
        ),
    ])

    # 5. Season Production Statistics Grid (High Density structured matrix)
    cmp_pct = float(player.get("Cmp%", 0.0))
    won_pct = float(player.get("Won%", 0.0))
    padj_factor = float(player.get("pAdj_Factor", 1.0))
    g_xg = float(player.get("G-xG", 0.0))
    npxg_sh = float(player.get("npxG/Sh", 0.0))

    if metric_mode == "per90":
        stat_items = [
            ("Goals / 90", f"{player.get('Gls_per90', 0.0):.2f}", "Scored per 90 min"),
            ("Expected Goals (xG) / 90", f"{player.get('xG_per90', 0.0):.2f}", "Chance quality per 90"),
            ("Finishing Diff (G - xG)", f"{g_xg:+.2f}", "Variance vs expected"),
            ("Shot Quality (npxG/Sh)", f"{npxg_sh:.2f}", "Avg quality per attempt"),
            ("Assists / 90", f"{player.get('Ast_per90', 0.0):.2f}", "Goal assists per 90"),
            ("Expected Assists (xA) / 90", f"{player.get('xA_per90', 0.0):.2f}", "Assisting chance quality"),
            ("Key Passes / 90", f"{player.get('KP_per90', 0.0):.2f}", "Shot-creating passes"),
            ("SCA / 90", f"{player.get('SCA_per90', 0.0):.2f}", "Shot-creating actions"),
            ("Pass Completion %", f"{cmp_pct:.1f}%", "Passing accuracy"),
            ("Prog. Passes / 90", f"{player.get('PrgP_per90', 0.0):.1f}", "Passes ≥10 yds closer"),
            ("Prog. Carries / 90", f"{player.get('PrgC_per90', 0.0):.1f}", "Carries ≥10 yds closer"),
            ("Shots (on Target) / 90", f"{player.get('Sh_per90', 0.0):.2f} ({player.get('SoT_per90', 0.0):.2f})", "Shot volume / 90"),
            ("pAdj Defending / 90", f"{player.get('Tkl_pAdj_per90', 0.0) + player.get('Int_pAdj_per90', 0.0):.2f}", f"Adjusted ({padj_factor:.2f}x)"),
            ("Raw Tackles + Int / 90", f"{player.get('Tkl_per90', 0.0) + player.get('Int_per90', 0.0):.2f}", "Unadjusted match rate"),
            ("Aerials Won / 90", f"{player.get('Won_per90', 0.0):.2f}", f"Win rate: {won_pct:.1f}%"),
        ]
    else:
        gls = int(player.get("Gls", 0))
        ast = int(player.get("Ast", 0))
        xg = float(player.get("xG", 0.0))
        xa = float(player.get("xA", 0.0))
        sh = int(player.get("Sh", 0))
        sot = int(player.get("SoT", 0))
        kp = int(player.get("KP", 0))
        sca = int(player.get("SCA", 0))
        prgp = int(player.get("PrgP", 0))
        prgc = int(player.get("PrgC", 0))
        tkl_int_padj = int(player.get("Tkl_pAdj", 0) + player.get("Int_pAdj", 0))
        tkl_int = int(player.get("Tkl", 0) + player.get("Int", 0))
        won = int(player.get("Won", 0))

        stat_items = [
            ("Goals", str(gls), "Season total goals"),
            ("Expected Goals (xG)", f"{xg:.2f}", "Season total xG"),
            ("Finishing Diff (G - xG)", f"{g_xg:+.2f}", "Total variance vs xG"),
            ("Shot Quality (npxG/Sh)", f"{npxg_sh:.2f}", "Avg quality per shot"),
            ("Assists", str(ast), "Season total assists"),
            ("Expected Assists (xA)", f"{xa:.2f}", "Season total xA"),
            ("Key Passes", str(kp), "Season total key passes"),
            ("Shot-Creating Actions", str(sca), "Season total creation actions"),
            ("Pass Completion %", f"{cmp_pct:.1f}%", "Passing accuracy"),
            ("Progressive Passes", str(prgp), "Season total prog passes"),
            ("Progressive Carries", str(prgc), "Season total prog carries"),
            ("Shots (on Target)", f"{sh} ({sot})", "Season total attempts"),
            ("pAdj Defending Actions", str(tkl_int_padj), f"Adjusted ({padj_factor:.2f}x)"),
            ("Raw Tackles + Int", str(tkl_int), "Unadjusted defensive actions"),
            ("Aerial Duels Won", str(won), f"Won ({won_pct:.1f}% win rate)"),
        ]

    stat_cols = [
        dmc.GridCol(
            dmc.Box(
                [
                    dmc.Text(label.upper(), size="10px", fw=700, c="dimmed", style={"letterSpacing": "0.5px"}),
                    dmc.Text(str(val), size="sm", fw=700, c="white", mt=2, style={"fontVariantNumeric": "tabular-nums"}),
                    dmc.Text(desc, size="10px", c="dimmed", mt=1),
                ],
                style={
                    "backgroundColor": "#0D131F",
                    "border": f"1px solid {BORDER}",
                    "borderRadius": "4px",
                    "padding": "8px 10px",
                },
            ),
            span={"base": 6, "sm": 4},
        )
        for label, val, desc in stat_items
    ]

    stats_grid = dmc.Grid(stat_cols, gap="xs")

    # Links for quick navigation
    compare_url = f"/player-comparison?player1={selected_name}"
    similar_url = f"/similar-players?player={selected_name}"

    return header, chart_fig, chart_note, attributes_breakdown, scouting_summary, stats_grid, compare_url, similar_url


# Toggle Profile Shortlist Modal
@callback(
    Output("profile-shortlist-modal", "opened"),
    Output("profile-modal-player-title", "children"),
    Input("profile-open-shortlist-btn", "n_clicks"),
    Input("profile-modal-cancel", "n_clicks"),
    Input("profile-modal-submit", "n_clicks"),
    State("profile-player-select", "value"),
    State("profile-shortlist-modal", "opened"),
    prevent_initial_call=True,
)
def toggle_profile_shortlist_modal(n_open, n_cancel, n_submit, player_name, is_open):
    title_text = f"Target: {player_name}" if player_name else "Candidate"
    return not is_open, title_text


# Save Profile Target to Global Shortlist Store
@callback(
    Output("scout-shortlists", "data", allow_duplicate=True),
    Output("profile-shortlist-feedback", "children"),
    Input("profile-modal-submit", "n_clicks"),
    State("profile-player-select", "value"),
    State("profile-modal-tier", "value"),
    State("profile-modal-notes", "value"),
    State("scout-shortlists", "data"),
    prevent_initial_call=True,
)
def save_profile_to_shortlist(n_clicks, player_name, tier, notes, current_data):
    if not player_name:
        return dash.no_update, dash.no_update
    current_data = current_data or []
    updated = [item for item in current_data if item.get("player") != player_name]
    updated.append({
        "player": player_name,
        "tier": tier or "A-List Target",
        "notes": notes or "Target scouted directly from Player Profile view.",
        "added_at": "2024-25 Season",
    })
    feedback = dmc.Alert(
        f"✓ Successfully bookmarked {player_name} to {tier}",
        color="emerald",
        variant="light",
        p="xs",
        mb="xs",
    )
    return updated, feedback
