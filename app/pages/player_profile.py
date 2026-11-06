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
from app.utils.charts import build_radar_chart
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
                title="Player Profile",
                subtitle="In-depth analytical evaluation, 7D percentile radar, tactical archetype, and statistical benchmarking.",
                badge_text="SCOUTING REPORT",
            ),

            # PLAYER SELECTION BAR
            create_section_card(
                dmc.Grid(
                    [
                        dmc.GridCol(
                            dmc.Select(
                                id="profile-player-select",
                                label="Select Player",
                                placeholder="Search player by name...",
                                data=[{"label": name, "value": name} for name in all_player_names],
                                value=initial_player,
                                searchable=True,
                                allowDeselect=False,
                            ),
                            span={"base": 12, "md": 6},
                        ),
                        dmc.GridCol(
                            dmc.Group(
                                [
                                    dmc.Button(
                                        "⭐ Save to Shortlist",
                                        id="profile-open-shortlist-btn",
                                        variant="filled",
                                        color="orange",
                                        size="sm",
                                    ),
                                    dmc.Anchor(
                                        dmc.Button("Compare This Player →", variant="outline", color="lime", size="sm"),
                                        id="profile-compare-btn",
                                        href="/player-comparison",
                                    ),
                                    dmc.Anchor(
                                        dmc.Button("Find Similar Profiles →", variant="light", color="lime", size="sm"),
                                        id="profile-similar-btn",
                                        href="/similar-players",
                                    ),
                                ],
                                gap="sm",
                                mt={"base": 0, "md": 24},
                            ),
                            span={"base": 12, "md": 6},
                        ),
                    ],
                    align="center",
                ),
                style={"marginBottom": "20px"},
            ),

            # BOOKMARK TO SHORTLIST MODAL
            dmc.Modal(
                id="profile-shortlist-modal",
                title=dmc.Group([
                    dmc.Text("⭐", size="md"),
                    dmc.Title("Save Candidate to Recruitment Pipeline", order=4, c="white"),
                ], gap="xs"),
                opened=False,
                centered=True,
                radius="md",
                styles={"content": {"backgroundColor": PANEL, "borderColor": BORDER}},
                children=[
                    dmc.Box([
                        dmc.Text(id="profile-modal-player-title", fw=700, size="sm", c="white", mb="xs"),
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
                            placeholder="Add tactical observations, scouting context, estimated valuation, or contract situation...",
                            minRows=3,
                            autosize=True,
                            mb="md",
                        ),
                        html.Div(id="profile-shortlist-feedback"),
                        dmc.Group([
                            dmc.Button("Cancel", id="profile-modal-cancel", variant="subtle", color="gray"),
                            dmc.Button("Save Target", id="profile-modal-submit", variant="filled", color="lime"),
                        ], justify="flex-end"),
                    ]),
                ],
            ),

            # DYNAMIC PLAYER HEADER BANNER
            html.Div(id="profile-header-banner"),

            dmc.Space(h=20),

            # MAIN PROFILE GRID: RADAR + ATTRIBUTE BREAKDOWN
            dmc.Grid(
                [
                    # LEFT: 7D RADAR CHART
                    dmc.GridCol(
                        create_section_card(
                            [
                                dcc.Graph(
                                    id="profile-radar-chart",
                                    config={"displayModeBar": False},
                                    responsive=True,
                                ),
                                dmc.Space(h=10),
                                dmc.Text(
                                    "Dashed grey line indicates position peer group average (50.0 baseline).",
                                    size="xs",
                                    c="dimmed",
                                    style={"textAlign": "center"},
                                ),
                            ],
                            title="7-Dimensional Scouting Radar",
                            subtitle="Position-relative percentiles benchmarked against positional peers",
                        ),
                        span={"base": 12, "lg": 6},
                    ),

                    # RIGHT: ATTRIBUTE PERCENTILE PROGRESS BARS
                    dmc.GridCol(
                        create_section_card(
                            html.Div(id="profile-attributes-breakdown"),
                            title="Attribute Percentile Breakdown",
                            subtitle="Detailed score cards and deviation from positional benchmark",
                        ),
                        span={"base": 12, "lg": 6},
                    ),
                ],
                gap="lg",
            ),

            dmc.Space(h=25),

            # SCOUTING REPORT & MATCH VOLUME METRICS
            dmc.Grid(
                [
                    dmc.GridCol(
                        create_section_card(
                            html.Div(id="profile-scouting-summary"),
                            title="Automated Scouting Assessment",
                            subtitle="Data-driven tactical overview, strengths, and areas for development",
                        ),
                        span={"base": 12, "md": 5},
                    ),
                    dmc.GridCol(
                        create_section_card(
                            html.Div(id="profile-stats-grid"),
                            title="Season Production Statistics",
                            subtitle="Key volume and efficiency metrics (2024–25 Season)",
                            extra_header=dmc.SegmentedControl(
                                id="profile-metric-mode",
                                data=[
                                    {"label": "Standard Per-90 Rates", "value": "per90"},
                                    {"label": "Season Total Counts", "value": "total"},
                                ],
                                value="per90",
                                size="xs",
                                color="lime",
                            ),
                        ),
                        span={"base": 12, "md": 7},
                    ),
                ],
                gap="lg",
            ),

            dmc.Space(h=25),
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
    Output("profile-attributes-breakdown", "children"),
    Output("profile-scouting-summary", "children"),
    Output("profile-stats-grid", "children"),
    Output("profile-compare-btn", "href"),
    Output("profile-similar-btn", "href"),
    Input("profile-player-select", "value"),
    Input("profile-metric-mode", "value"),
)
def update_player_profile(selected_name, metric_mode="per90"):
    player = get_player_by_name(selected_name)
    if player is None:
        player = get_player_by_name(DEFAULT_PLAYER)

    name = player["Player"]
    club = player["Squad"]
    pos = player["Pos"]
    pos_name = POSITION_NAMES.get(pos, pos)
    subrole = player.get("SubRole", "Tactical Specialist")
    nation = player["Nation_Clean"]
    age = player["Age"]
    born = player["Born"]
    minutes = player["Min"]
    style_name = player.get("PlayingStyle_Name", "Tactical Specialist")

    pos_badge_color = "blue" if pos == "DF" else "lime" if pos == "MF" else "orange"

    # 1. Header Banner
    header = dmc.Card(
        [
            dmc.Breadcrumbs(
                [
                    dmc.Anchor("Scouting Overview", href="/", size="xs", c="dimmed", style={"textDecoration": "none"}),
                    dmc.Anchor("Player Explorer", href="/player-explorer", size="xs", c="dimmed", style={"textDecoration": "none"}),
                    dmc.Text(name, size="xs", fw=600, c="lime"),
                ],
                separator="›",
                mb="sm",
            ),
            dmc.Group(
                [
                    dmc.Box([
                        dmc.Group(
                            [
                                dmc.Title(name, order=2, c="white"),
                                dmc.Badge(pos_name, color=pos_badge_color, variant="filled", size="md"),
                                dmc.Badge(subrole, color="cyan", variant="light", size="md"),
                                dmc.Badge(f"Style: {style_name}", color="lime", variant="outline", size="md"),
                            ],
                            gap="sm",
                            wrap="wrap",
                        ),
                        dmc.Group(
                            [
                                dmc.Text(f"Club: {club} ({player.get('Comp_Clean', 'Big 5')})", size="sm", fw=600, c="dimmed"),
                                dmc.Text("•", c="dimmed"),
                                dmc.Text(f"Nation: {player.get('Nation_Display', nation)}", size="sm", c="dimmed"),
                                dmc.Text("•", c="dimmed"),
                                dmc.Text(f"Age: {age} (Born {born})", size="sm", c="dimmed"),
                                dmc.Text("•", c="dimmed"),
                                dmc.Text(f"Minutes: {minutes:,}m", size="sm", c="dimmed", style={"fontVariantNumeric": "tabular-nums"}),
                            ],
                            gap="xs",
                            mt=8,
                            wrap="wrap",
                        ),
                    ]),
                    dmc.Box([
                        dmc.Text("PLAYING STYLE DNA", size="xs", fw=700, c="dimmed", style={"letterSpacing": "0.5px"}),
                        dmc.Title(style_name, order=3, c="lime", mt=4),
                    ]),
                ],
                justify="space-between",
                align="center",
                wrap="wrap",
            ),
        ],
        withBorder=True,
        radius="md",
        p="lg",
        style={"backgroundColor": PANEL, "borderColor": BORDER, "boxShadow": "0 4px 20px -2px rgba(0,0,0,0.4)"},
    )

    # 2. Radar Chart
    pos_avgs = get_position_averages(pos)
    radar_fig = build_radar_chart(
        players=[player],
        include_position_avg=True,
        position_avg_scores=pos_avgs,
        height=380,
    )

    # 3. Attribute Breakdown Progress Bars
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
        diff_color = "#84CC16" if diff >= 0 else "#F59E0B"

        attribute_cards.append(
            dmc.Box(
                [
                    dmc.Group(
                        [
                            dmc.Text(attr, size="sm", fw=600, c="white"),
                            dmc.Group(
                                [
                                    dmc.Badge(status, color=bar_color, variant="light", size="xs"),
                                    dmc.Text(
                                        f"{score:.1f}th pct",
                                        size="sm",
                                        fw=700,
                                        style={"color": tier_info["color"], "fontVariantNumeric": "tabular-nums"},
                                    ),
                                    dmc.Text(
                                        f"({diff_str} vs avg)",
                                        size="xs",
                                        style={"color": diff_color, "fontVariantNumeric": "tabular-nums"},
                                    ),
                                ],
                                gap="xs",
                            ),
                        ],
                        justify="space-between",
                        mb=4,
                    ),
                    dmc.Progress(value=score, color=bar_color, size="sm", radius="xl"),
                ],
                mb="md",
            )
        )

    attributes_breakdown = html.Div(attribute_cards)

    # 4. Scouting Assessment Narrative
    strengths, weaknesses = get_player_strengths_and_weaknesses(player)
    report_text = generate_scouting_report(player)

    scouting_summary = html.Div([
        dmc.Text(report_text, size="sm", c="white", style={"lineHeight": 1.6}),
        dmc.Divider(my="md"),
        dmc.Text("TOP ANALYTICAL STRENGTHS", size="xs", fw=700, c="lime", mb=6),
        dmc.Group(
            [
                dmc.Badge(
                    f"{s['attribute']} ({s['score']:.1f})",
                    color="lime",
                    variant="filled",
                    size="sm",
                )
                for s in strengths
            ],
            gap="xs",
            mb="md",
            wrap="wrap",
        ),
        dmc.Text("DEVELOPMENTAL PRIORITIES", size="xs", fw=700, c="orange", mb=6),
        dmc.Group(
            [
                dmc.Badge(
                    f"{w['attribute']} ({w['score']:.1f})",
                    color="orange",
                    variant="light",
                    size="sm",
                )
                for w in weaknesses
            ],
            gap="xs",
            wrap="wrap",
        ),
    ])

    # 5. Production Statistics Grid
    cmp_pct = float(player.get("Cmp%", 0.0))
    won_pct = float(player.get("Won%", 0.0))
    padj_factor = float(player.get("pAdj_Factor", 1.0))
    g_xg = float(player.get("G-xG", 0.0))
    npxg_sh = float(player.get("npxG/Sh", 0.0))

    if metric_mode == "per90":
        stat_items = [
            ("Goals / 90", f"{player.get('Gls_per90', 0.0):.2f}", "Goals scored per 90 min"),
            ("Expected Goals (xG) / 90", f"{player.get('xG_per90', 0.0):.2f}", "Shot quality generated / 90"),
            ("Finishing Diff (G - xG)", f"{g_xg:+.2f}", "Over/underperformance vs xG"),
            ("Shot Quality (npxG/Sh)", f"{npxg_sh:.2f}", "Avg chance quality per shot"),
            ("Assists / 90", f"{player.get('Ast_per90', 0.0):.2f}", "Goal assists per 90 min"),
            ("Expected Assists (xA) / 90", f"{player.get('xA_per90', 0.0):.2f}", "Assisting chance quality / 90"),
            ("Key Passes / 90", f"{player.get('KP_per90', 0.0):.2f}", "Shot-creating passes / 90"),
            ("SCA / 90", f"{player.get('SCA_per90', 0.0):.2f}", "Shot-creating actions / 90"),
            ("Pass Completion %", f"{cmp_pct:.1f}%", "Passing accuracy rate"),
            ("Prog. Passes / 90", f"{player.get('PrgP_per90', 0.0):.1f}", "Passes moving ≥10 yds closer"),
            ("Prog. Carries / 90", f"{player.get('PrgC_per90', 0.0):.1f}", "Carries moving ≥10 yds closer"),
            ("Shots (on Target) / 90", f"{player.get('Sh_per90', 0.0):.2f} ({player.get('SoT_per90', 0.0):.2f})", "Shot volume / 90"),
            ("pAdj Defending / 90", f"{player.get('Tkl_pAdj_per90', 0.0) + player.get('Int_pAdj_per90', 0.0):.2f}", f"Possession-adjusted ({padj_factor:.2f}x)"),
            ("Raw Tackles + Int / 90", f"{player.get('Tkl_per90', 0.0) + player.get('Int_per90', 0.0):.2f}", "Unadjusted match rate"),
            ("Aerials Won / 90", f"{player.get('Won_per90', 0.0):.2f}", f"Duel win rate: {won_pct:.1f}%"),
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
            ("Expected Goals (xG)", f"{xg:.2f}", "Season total expected goals"),
            ("Finishing Diff (G - xG)", f"{g_xg:+.2f}", "Total finishing variance vs xG"),
            ("Shot Quality (npxG/Sh)", f"{npxg_sh:.2f}", "Avg chance quality per shot"),
            ("Assists", str(ast), "Season total assists"),
            ("Expected Assists (xA)", f"{xa:.2f}", "Season total expected assists"),
            ("Key Passes", str(kp), "Season total key passes"),
            ("Shot-Creating Actions", str(sca), "Season total creation actions"),
            ("Pass Completion %", f"{cmp_pct:.1f}%", "Passing accuracy rate"),
            ("Progressive Passes", str(prgp), "Season total prog passes"),
            ("Progressive Carries", str(prgc), "Season total prog carries"),
            ("Shots (on Target)", f"{sh} ({sot})", "Season total shooting frequency"),
            ("pAdj Defending Actions", str(tkl_int_padj), f"Possession-adjusted ({padj_factor:.2f}x)"),
            ("Raw Tackles + Int", str(tkl_int), "Unadjusted defensive actions"),
            ("Aerial Duels Won", str(won), f"Season won ({won_pct:.1f}% win rate)"),
        ]

    stat_cols = [
        dmc.GridCol(
            dmc.Card(
                [
                    dmc.Text(label.upper(), size="xs", fw=700, c="dimmed"),
                    dmc.Title(str(val), order=3, c="white", mt=4),
                    dmc.Text(desc, size="xs", c="dimmed", mt=2),
                ],
                withBorder=True,
                radius="sm",
                p="sm",
                style={"backgroundColor": "#131E30", "borderColor": BORDER},
            ),
            span={"base": 6, "sm": 4},
        )
        for label, val, desc in stat_items
    ]

    stats_grid = dmc.Grid(stat_cols, gap="sm")

    # Links for quick navigation
    compare_url = f"/player-comparison?player1={selected_name}"
    similar_url = f"/similar-players?player={selected_name}"

    return header, radar_fig, attributes_breakdown, scouting_summary, stats_grid, compare_url, similar_url


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
    title_text = f"Candidate: {player_name}" if player_name else "Candidate"
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
        f"✓ Successfully bookmarked {player_name} to {tier}!",
        color="lime",
        variant="light",
        p="xs",
        mb="xs",
    )
    return updated, feedback

