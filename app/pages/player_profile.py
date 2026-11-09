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
    get_recruitment_suitability_assessment,
)
from app.utils.metric_definitions import (
    get_metric_label,
    get_metric_tooltip,
    get_metric_info,
    get_role_metrics,
    get_sample_size_badge,
    SAMPLE_SIZE_THRESHOLD,
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
                                        "Bookmark Target",
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
                    dmc.Text("Add Candidate to Recruitment Pipeline", size="sm", fw=700, style={"color": TEXT}),
                ], gap="xs"),
                opened=False,
                centered=True,
                radius="sm",
                styles={"content": {"backgroundColor": PANEL, "borderColor": BORDER}},
                children=[
                    dmc.Box([
                        dmc.Text(id="profile-modal-player-title", fw=600, size="sm", style={"color": TEXT}, mb="xs"),
                        dmc.Select(
                            id="profile-modal-tier",
                            label="Recruitment Priority Tier",
                            data=[
                                {"label": "A-List Target (Priority 1)", "value": "A-List Target"},
                                {"label": "Primary Alternative (Priority 2)", "value": "Primary Alternative"},
                                {"label": "Monitor / Development (Priority 3)", "value": "Monitor / Development"},
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

            # LAYER 1: FIRST SCREEN HERO — 12-SLICE PIZZA + EXECUTIVE SCOUTING SYNTHESIS
            dmc.Grid(
                [
                    # LEFT: 12-SLICE PERCENTILE PIZZA (PRIMARY VISUAL FOOTPRINT)
                    dmc.GridCol(
                        create_section_card(
                            [
                                dcc.Graph(
                                    id="profile-radar-chart",
                                    config={"displayModeBar": False},
                                    responsive=True,
                                    style={"height": "400px", "width": "100%"},
                                ),
                                dmc.Space(h=6),
                                html.Div(
                                    id="profile-chart-note",
                                    style={"textAlign": "center"},
                                ),
                            ],
                            title="Visual Performance Footprint",
                            subtitle="12-Slice Percentile Pizza benchmarked against positional cohort",
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
                        span={"base": 12, "lg": 5},
                    ),

                    # RIGHT: EXECUTIVE SCOUTING DOSSIER & RECRUITMENT SYNTHESIS
                    dmc.GridCol(
                        create_section_card(
                            html.Div(id="profile-scouting-summary"),
                            title="Executive Scouting Dossier",
                            subtitle="Core assets, data-backed watch-outs, and evidence-based recruitment suitability",
                        ),
                        span={"base": 12, "lg": 7},
                    ),
                ],
                gap="md",
            ),

            dmc.Space(h=16),

            # LAYER 2 & LAYER 3: PROGRESSIVE DISCLOSURE ACCORDIONS
            dmc.Accordion(
                multiple=True,
                value=["production"],
                styles={
                    "item": {
                        "backgroundColor": "var(--scout-surface-primary)",
                        "border": "1px solid var(--scout-border)",
                        "borderRadius": "6px",
                        "marginBottom": "12px",
                    },
                    "control": {
                        "color": "var(--scout-text-primary)",
                        "padding": "12px 18px",
                    },
                    "panel": {
                        "padding": "0px 18px 18px 18px",
                    },
                },
                children=[
                    # ACCORDION 1: SEASON PRODUCTION STATISTICS
                    dmc.AccordionItem(
                        [
                            dmc.AccordionControl(
                                dmc.Group([
                                    dmc.Text("Season Match Production Statistics", fw=700, size="sm", c="var(--scout-text-primary)"),
                                    dmc.Badge("PRODUCTION MATRIX", color="teal", variant="light", size="xs"),
                                    dmc.Text("Key volume, rates, and role-tailored indicators (2024–25)", size="xs", c="dimmed"),
                                ], gap="xs")
                            ),
                            dmc.AccordionPanel(
                                dmc.Box([
                                    dmc.Group([
                                        dmc.Text("Select statistical metric rate:", size="11px", c="dimmed"),
                                        dmc.SegmentedControl(
                                            id="profile-metric-mode",
                                            data=[
                                                {"label": "Standard Per-90 Rates", "value": "per90"},
                                                {"label": "Season Total Counts", "value": "total"},
                                            ],
                                            value="per90",
                                            size="xs",
                                            color="emerald",
                                        ),
                                    ], justify="space-between", align="center", mb="sm"),
                                    html.Div(id="profile-stats-grid"),
                                ])
                            ),
                        ],
                        value="production",
                    ),

                    # ACCORDION 2: ATTRIBUTE PERCENTILE SPECTRUM & BENCHMARK DEVIATION
                    dmc.AccordionItem(
                        [
                            dmc.AccordionControl(
                                dmc.Group([
                                    dmc.Text("Positional Percentile Spectrum & Benchmarks", fw=700, size="sm", c="var(--scout-text-primary)"),
                                    dmc.Badge("7-DIMENSIONAL SPECTRUM", color="blue", variant="light", size="xs"),
                                    dmc.Text("Detailed trait scores and +/- deviation against position cohort average", size="xs", c="dimmed"),
                                ], gap="xs")
                            ),
                            dmc.AccordionPanel(
                                html.Div(id="profile-attributes-breakdown", style={"paddingTop": "8px"})
                            ),
                        ],
                        value="attributes",
                    ),

                    # ACCORDION 3: DATA QUALITY & PROVENANCE VERIFICATION (LAYER 4)
                    dmc.AccordionItem(
                        [
                            dmc.AccordionControl(
                                dmc.Group([
                                    dmc.Text("Data Quality & Provenance Verification", fw=700, size="sm", c="var(--scout-text-primary)"),
                                    dmc.Badge("DATA AUDIT & PROVENANCE", color="teal", variant="light", size="xs"),
                                    dmc.Text("Sample size validation, Opta event coverage, and analytical confidence", size="xs", c="dimmed"),
                                ], gap="xs")
                            ),
                            dmc.AccordionPanel(
                                dmc.Grid(
                                    [
                                        dmc.GridCol(
                                            dmc.Box([
                                                dmc.Text("SAMPLE SIZE INTEGRITY", size="10px", fw=700, c="var(--scout-text-muted)"),
                                                dmc.Text("Standard Threshold Validation", size="xs", fw=600, c="var(--scout-text-primary)", mt=2),
                                                dmc.Text("Rate metrics qualified against the 900-minute benchmark for statistical reliability.", size="10px", c="var(--scout-text-secondary)", mt=2),
                                            ], style={"padding": "10px 12px", "backgroundColor": "var(--scout-surface-secondary)", "borderRadius": "4px", "border": "1px solid var(--scout-border)"}),
                                            span={"base": 12, "sm": 4},
                                        ),
                                        dmc.GridCol(
                                            dmc.Box([
                                                dmc.Text("DATA PROVENANCE & LEAGUE COVERAGE", size="10px", fw=700, c="var(--scout-text-muted)"),
                                                dmc.Text("Opta / FBref 2024–25 Event Stream", size="xs", fw=600, c="var(--scout-text-primary)", mt=2),
                                                dmc.Text("European Big 5 league match events with possession adjustment (pAdj).", size="10px", c="var(--scout-text-secondary)", mt=2),
                                            ], style={"padding": "10px 12px", "backgroundColor": "var(--scout-surface-secondary)", "borderRadius": "4px", "border": "1px solid var(--scout-border)"}),
                                            span={"base": 12, "sm": 4},
                                        ),
                                        dmc.GridCol(
                                            dmc.Box([
                                                dmc.Text("ANALYTICAL CONFIDENCE", size="10px", fw=700, c="var(--scout-text-muted)"),
                                                dmc.Text("Peer Cohort Benchmarking", size="xs", fw=600, c="#10B981", mt=2),
                                                dmc.Text("Standardized percentile ranks computed strictly within positional peer groups.", size="10px", c="var(--scout-text-secondary)", mt=2),
                                            ], style={"padding": "10px 12px", "backgroundColor": "var(--scout-surface-secondary)", "borderRadius": "4px", "border": "1px solid var(--scout-border)"}),
                                            span={"base": 12, "sm": 4},
                                        ),
                                    ],
                                    gap="sm",
                                )
                            ),
                        ],
                        value="data_quality",
                    ),
                ],
            ),

            dmc.Space(h=16),
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
    Input("scout-analyst-mode", "data"),
    Input("theme-store", "data"),
)
def update_player_profile(selected_name, metric_mode="per90", chart_type="pizza", scout_analyst_mode="scout", theme="dark"):
    scout_analyst_mode = scout_analyst_mode or "scout"
    theme = theme or "dark"
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
    minutes = float(player.get("Min", 0))
    style_name = player.get("PlayingStyle_Name", "Tactical Specialist")

    pos_badge_color = "blue" if pos == "DF" else "emerald" if pos == "MF" else "orange"
    sample_badge = get_sample_size_badge(minutes)

    # 1. Dossier Header Banner (Pitch Black / High Hierarchy)
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
                                dmc.Title(name, order=2, c="var(--scout-text-primary)", style={"fontSize": "22px", "fontWeight": 700}),
                                dmc.Badge(pos_name, color=pos_badge_color, variant="filled", size="sm"),
                                dmc.Badge(subrole, color="cyan", variant="light", size="sm"),
                                *([sample_badge] if sample_badge else []),
                            ],
                            gap="xs",
                            wrap="wrap",
                            align="center",
                        ),
                        dmc.Group(
                            [
                                dmc.Text(club, size="xs", fw=600, c="var(--scout-text-primary)"),
                                dmc.Text("•", c="dimmed"),
                                dmc.Text(nation, size="xs", c="dimmed"),
                                dmc.Text("•", c="dimmed"),
                                dmc.Text(f"Age {age} ({born})", size="xs", c="dimmed"),
                                dmc.Text("•", c="dimmed"),
                                dmc.Text(f"{int(minutes):,} mins ({minutes/90:.1f} 90s)", size="xs", c="dimmed", style={"fontVariantNumeric": "tabular-nums"}),
                            ],
                            gap="xs",
                            mt=6,
                            wrap="wrap",
                        ),
                    ]),
                    dmc.Box(
                        [
                            dmc.Badge(style_name, color="emerald", variant="light", size="sm"),
                            dmc.Text("PLAYING STYLE DNA", size="10px", fw=700, c="dimmed", style={"letterSpacing": "0.8px"}, mt=4),
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
            height=400,
            theme=theme,
        )
        chart_note = dmc.Text(
            "7-Dimensional Scouting Radar: Dashed line represents position cohort baseline (50.0).",
            size="xs",
            c="dimmed",
            mt=4,
        )
    else:
        chart_fig = build_pizza_chart(player, height=400, theme=theme)
        if scout_analyst_mode == "scout":
            chart_note = dmc.Text(
                "12-Slice Percentile Pizza: Radial wedge length indicates percentile rank (0–100) vs positional cohort.",
                size="xs",
                c="dimmed",
                mt=4,
            )
        else:
            chart_note = dmc.Text(
                "12-Slice Percentile Pizza: Normalized angular distribution across Attacking, Possession, and Defending vectors.",
                size="xs",
                c="dimmed",
                mt=4,
            )

    # 3. Attribute Breakdown Progress Bars (Layer 3 Progressive Disclosure)
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
                                dmc.Text(attr, size="xs", fw=600, c="var(--scout-text-primary)"),
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

    # 4. Tactical Assessment, Standout Strengths & Evidence-Based Recruitment Suitability
    strengths, weaknesses = get_player_strengths_and_weaknesses(player)
    report_text = generate_scouting_report(player)
    recruitment_assessment = get_recruitment_suitability_assessment(player)

    # Format Strengths UI: STRICT LIMIT OF MAX 3 PRIMARY STRENGTHS
    primary_strengths = strengths[:3]
    strength_badges = []
    for s in primary_strengths:
        level_color = "emerald" if s["level"] in ["Elite", "Outperformer", "High Efficiency"] else "teal"
        badge_text = f"{s['attribute']}"
        if s.get("score") and s["score"] <= 100:
            badge_text += f" ({s['score']:.1f})"
        if s.get("is_limited_sample"):
            badge_text += " [Low Min]"
        strength_badges.append(
            dmc.Tooltip(
                label=s.get("scout_note", ""),
                multiline=True,
                w=260,
                children=dmc.Badge(
                    badge_text,
                    color=level_color,
                    variant="light",
                    size="xs",
                    style={"cursor": "help", "fontWeight": 600},
                ),
            )
        )

    # Format Weaknesses / Monitoring UI: STRICT LIMIT OF MAX 2 PRIMARY CONCERNS
    primary_weaknesses = weaknesses[:2]
    weakness_badges = []
    for w in primary_weaknesses:
        w_color = "red" if "Priority" in w["level"] else "orange"
        badge_text = f"{w['attribute']}"
        if w.get("score"):
            badge_text += f" ({w['score']:.1f})"
        if w.get("is_limited_sample"):
            badge_text += " [Low Min]"
        weakness_badges.append(
            dmc.Tooltip(
                label=w.get("scout_note", ""),
                multiline=True,
                w=260,
                children=dmc.Badge(
                    badge_text,
                    color=w_color,
                    variant="light",
                    size="xs",
                    style={"cursor": "help", "fontWeight": 600},
                ),
            )
        )

    # Recruitment Suitability UI Elements (Concise 2–3 items)
    attractions_list = [
        html.Li(
            dmc.Text(att, size="xs", c="#CBD5E1", style={"lineHeight": 1.45}),
            style={"marginBottom": "3px"}
        )
        for att in recruitment_assessment.get("attractions", [])[:3]
    ]
    concerns_list = [
        html.Li(
            dmc.Text(con, size="xs", c="#CBD5E1", style={"lineHeight": 1.45}),
            style={"marginBottom": "3px"}
        )
        for con in recruitment_assessment.get("concerns", [])[:2]
    ]
    actions_list = [
        html.Li(
            dmc.Text(act, size="xs", c="#CBD5E1", style={"lineHeight": 1.45}),
            style={"marginBottom": "3px"}
        )
        for act in recruitment_assessment.get("scouting_actions", [])[:2]
    ]

    scouting_summary = html.Div([
        dmc.Text(report_text, size="xs", c="#E2E8F0", style={"lineHeight": 1.6, "marginBottom": "10px"}),

        dmc.Grid([
            dmc.GridCol([
                dmc.Text("TOP 3 STANDOUT CHARACTERISTICS", size="10px", fw=700, c="teal", style={"letterSpacing": "0.6px"}, mb=6),
                dmc.Group(strength_badges if strength_badges else [dmc.Badge("Balanced Profile", color="gray", variant="light", size="xs")], gap="xs", wrap="wrap"),
            ], span={"base": 12, "sm": 7}),
            dmc.GridCol([
                dmc.Text("TACTICAL WATCH-OUTS (MAX 2)", size="10px", fw=700, c="orange", style={"letterSpacing": "0.6px"}, mb=6),
                dmc.Group(
                    weakness_badges if weakness_badges else [dmc.Badge("Balanced Profile (No Critical Deficits)", color="gray", variant="light", size="xs")],
                    gap="xs",
                    wrap="wrap",
                ),
            ], span={"base": 12, "sm": 5}),
        ], gap="sm", mb="xs"),

        dmc.Divider(my="xs", color=BORDER),

        # EVIDENCE-BASED RECRUITMENT ASSESSMENT
        dmc.Box(
            [
                dmc.Group([
                    dmc.Text("RECRUITMENT SUITABILITY ASSESSMENT", size="10px", fw=800, c="teal", style={"letterSpacing": "0.8px"}),
                    dmc.Badge(
                        recruitment_assessment.get("sample_size_status", "Qualified"),
                        color="teal" if "Qualified" in recruitment_assessment.get("sample_size_status", "") else "orange",
                        variant="light",
                        size="xs",
                    ),
                ], justify="space-between", align="center", mb=4),

                dmc.Text("Statistical Attractions:", size="10px", fw=700, c="#10B981", mt=4),
                html.Ul(attractions_list, style={"paddingLeft": "16px", "margin": "3px 0"}),

                dmc.Text("Recruitment Watch-Outs / Flags:", size="10px", fw=700, c="#F59E0B", mt=4),
                html.Ul(concerns_list, style={"paddingLeft": "16px", "margin": "3px 0"}),

                dmc.Text("Recommended Next Scouting Steps:", size="10px", fw=700, c="#38BDF8", mt=4),
                html.Ul(actions_list, style={"paddingLeft": "16px", "margin": "3px 0"}),

                dmc.Text(
                    recruitment_assessment.get("disclaimer", ""),
                    size="9px",
                    c="#64748B",
                    style={"fontStyle": "italic", "lineHeight": 1.35},
                    mt=6,
                ),
            ],
            style={
                "backgroundColor": "var(--scout-surface-secondary)",
                "border": "1px solid var(--scout-accent-border)",
                "borderRadius": "5px",
                "padding": "10px 14px",
                "marginTop": "6px",
            },
        ),
    ])

    # 5. Season Production Statistics Grid (Layer 2 Progressive Disclosure)
    cmp_pct = float(player.get("Cmp%", 0.0))
    won_pct = float(player.get("Won%", 0.0))
    padj_factor = float(player.get("pAdj_Factor", 1.0))
    g_xg = float(player.get("G-xG", 0.0))
    npxg_sh = float(player.get("npxG/Sh", 0.0))

    if scout_analyst_mode == "scout":
        # Role-tailored 6-metric focus
        role_metric_keys = get_role_metrics(subrole, pos)
        stat_items = []
        for mk in role_metric_keys:
            info = get_metric_info(mk)
            label = info["scout_name"]
            desc = info["description"]

            # Compute value based on per90 or total
            if mk == "Gls_per90":
                val = f"{player.get('Gls_per90', 0.0):.2f}" if metric_mode == "per90" else str(int(player.get('Gls', 0)))
            elif mk == "xG_per90":
                val = f"{player.get('xG_per90', 0.0):.2f}" if metric_mode == "per90" else f"{player.get('xG', 0.0):.2f}"
            elif mk == "G-xG":
                val = f"{g_xg:+.2f}"
            elif mk == "npxG/Sh":
                val = f"{npxg_sh:.2f}"
            elif mk == "Ast_per90":
                val = f"{player.get('Ast_per90', 0.0):.2f}" if metric_mode == "per90" else str(int(player.get('Ast', 0)))
            elif mk == "xA_per90":
                val = f"{player.get('xA_per90', 0.0):.2f}" if metric_mode == "per90" else f"{player.get('xA', 0.0):.2f}"
            elif mk == "KP_per90":
                val = f"{player.get('KP_per90', 0.0):.2f}" if metric_mode == "per90" else str(int(player.get('KP', 0)))
            elif mk == "SCA_per90":
                val = f"{player.get('SCA_per90', 0.0):.2f}" if metric_mode == "per90" else str(int(player.get('SCA', 0)))
            elif mk == "PrgP_per90":
                val = f"{player.get('PrgP_per90', 0.0):.1f}" if metric_mode == "per90" else str(int(player.get('PrgP', 0)))
            elif mk == "PrgC_per90":
                val = f"{player.get('PrgC_per90', 0.0):.1f}" if metric_mode == "per90" else str(int(player.get('PrgC', 0)))
            elif mk == "Cmp%":
                val = f"{cmp_pct:.1f}%"
            elif mk == "Won%":
                val = f"{won_pct:.1f}%"
            elif mk == "Tkl_pAdj_per90":
                val = f"{player.get('Tkl_pAdj_per90', 0.0):.2f}" if metric_mode == "per90" else str(int(player.get('Tkl_pAdj', 0)))
            elif mk == "Int_pAdj_per90":
                val = f"{player.get('Int_pAdj_per90', 0.0):.2f}" if metric_mode == "per90" else str(int(player.get('Int_pAdj', 0)))
            elif mk == "Clr_pAdj_per90":
                val = f"{player.get('Clr_pAdj_per90', 0.0):.2f}" if metric_mode == "per90" else str(int(player.get('Clr_pAdj', 0)))
            else:
                raw_val = player.get(mk, 0.0)
                val = f"{float(raw_val):.2f}" if isinstance(raw_val, (int, float)) else str(raw_val)

            stat_items.append((label, val, desc))

        stat_cols = [
            dmc.GridCol(
                dmc.Box(
                    [
                        dmc.Text(label.upper(), size="10px", fw=700, c="dimmed", style={"letterSpacing": "0.5px"}),
                        dmc.Text(str(val), size="sm", fw=700, c="var(--scout-text-primary)", mt=2, style={"fontVariantNumeric": "tabular-nums"}),
                        dmc.Text(desc, size="10px", c="dimmed", mt=1, lineClamp=1),
                    ],
                    style={
                        "backgroundColor": "var(--scout-surface-secondary)",
                        "border": "1px solid var(--scout-border)",
                        "borderRadius": "4px",
                        "padding": "10px 12px",
                    },
                ),
                span={"base": 6, "sm": 4},
            )
            for label, val, desc in stat_items
        ]

        stats_grid = dmc.Box([
            dmc.Grid(stat_cols, gap="xs"),
            dmc.Group([
                dmc.Badge("ROLE-TAILORED METRICS", color="teal", variant="outline", size="xs"),
                dmc.Text(
                    f"Showing 6 primary production indicators prioritized for {subrole}. Switch to Analyst View in the header for all 15 advanced metrics and pAdj distributions.",
                    size="10.5px",
                    c="#64748B",
                ),
            ], gap="xs", align="center", mt="md"),
        ])

    else:
        # Analyst View: Comprehensive 15-item matrix with mathematical adjustments
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
                        dmc.Text(str(val), size="sm", fw=700, c="var(--scout-text-primary)", mt=2, style={"fontVariantNumeric": "tabular-nums"}),
                        dmc.Text(desc, size="10px", c="dimmed", mt=1),
                    ],
                    style={
                        "backgroundColor": "var(--scout-surface-secondary)",
                        "border": "1px solid var(--scout-border)",
                        "borderRadius": "4px",
                        "padding": "8px 10px",
                    },
                ),
                span={"base": 6, "sm": 4},
            )
            for label, val, desc in stat_items
        ]

        stats_grid = dmc.Box([
            dmc.Grid(stat_cols, gap="xs"),
            dmc.Group([
                dmc.Badge("ANALYST VIEW ACTIVE", color="indigo", variant="outline", size="xs"),
                dmc.Text(
                    f"Showing complete 15-attribute analytical matrix with possession-adjusted (pAdj) defending factors ({padj_factor:.2f}x), shot quality, and finishing differentials.",
                    size="10.5px",
                    c="#818CF8",
                ),
            ], gap="xs", align="center", mt="md"),
        ])

    compare_href = f"/player-comparison?player1={player['Player_Unique']}"
    similar_href = f"/similar-players?player={player['Player_Unique']}"

    return (
        header,
        chart_fig,
        chart_note,
        attributes_breakdown,
        scouting_summary,
        stats_grid,
        compare_href,
        similar_href,
    )


# --------------------------------------------------
# SHORTLIST BOOKMARKING CALLBACKS
# --------------------------------------------------

@callback(
    Output("profile-shortlist-modal", "opened"),
    Output("profile-modal-player-title", "children"),
    Input("profile-open-shortlist-btn", "n_clicks"),
    Input("profile-modal-cancel", "n_clicks"),
    State("profile-player-select", "value"),
    prevent_initial_call=True,
)
def toggle_profile_shortlist_modal(open_clicks, cancel_clicks, selected_name):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, ""
    button_id = ctx.triggered_id
    if button_id == "profile-open-shortlist-btn":
        player = get_player_by_name(selected_name)
        title = f"Candidate: {player['Player']} ({player['Squad']} • {player.get('SubRole', player['Pos'])})" if player is not None else ""
        return True, title
    return False, ""


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
def save_profile_to_shortlist(n_clicks=None, player_name=None, tier=None, notes=None, current_data=None, submit_clicks=None):
    clicks = n_clicks or submit_clicks
    if not clicks or not player_name:
        return dash.no_update, dash.no_update

    current_data = current_data or []
    updated = save_candidate_to_store(current_data, player_name, tier, notes)
    feedback = dmc.Alert(
        f"Successfully bookmarked {player_name} to {tier}.",
        color="emerald",
        variant="light",
        radius="sm",
        p="xs",
        mb="sm",
    )
    return updated, feedback


def save_candidate_to_store(current_data, player_name, tier, notes):
    updated = []
    found = False
    for item in current_data:
        if item.get("player") == player_name:
            updated.append({
                "player": player_name,
                "tier": tier or "A-List Target",
                "notes": notes or item.get("notes", ""),
                "added_at": item.get("added_at", "2024-25 Season"),
            })
            found = True
        else:
            updated.append(item)

    if not found:
        updated.append({
            "player": player_name,
            "tier": tier or "A-List Target",
            "notes": notes or "Target bookmarked for recruitment evaluation.",
            "added_at": "2024-25 Season",
        })

    return updated
