import dash
from dash import html, dcc, Input, Output, State, callback
import dash_mantine_components as dmc
import plotly.graph_objects as go
import pandas as pd

from app.utils.data_loader import load_data, get_player_by_name, get_all_player_names
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
from app.utils.charts import build_radar_chart, build_comparison_bars, PLAYER_COMPARE_COLORS
from app.utils.player_analysis import get_player_strengths_and_weaknesses
from app.utils.metric_definitions import (
    get_metric_label,
    get_metric_tooltip,
    get_sample_size_badge,
    SAMPLE_SIZE_THRESHOLD,
)

dash.register_page(__name__, path="/player-comparison", name="Player Comparison", order=4)

df = load_data()
all_player_names = get_all_player_names()

DEFAULT_PLAYERS = ["Erling Haaland", "Kylian Mbappé"]
if not all(p in all_player_names for p in DEFAULT_PLAYERS):
    DEFAULT_PLAYERS = all_player_names[:2]


def layout(player1=None, player2=None, **kwargs):
    initial_values = []
    if player1 and get_player_by_name(player1) is not None:
        initial_values.append(player1)
    if player2 and get_player_by_name(player2) is not None:
        initial_values.append(player2)

    if len(initial_values) < 2:
        for p in DEFAULT_PLAYERS:
            if p not in initial_values:
                initial_values.append(p)
            if len(initial_values) == 2:
                break

    return dmc.Container(
        [
            create_page_header(
                title="Comparison Matrix",
                subtitle="Head-to-head multi-dimensional evaluation. Benchmark 2 to 4 candidates simultaneously across percentile attributes and match volume.",
                badge_text="COMPARATIVE EVALUATION",
            ),

            # CANDIDATE SELECTION PANEL
            create_section_card(
                dmc.Box([
                    dmc.MultiSelect(
                        id="compare-players-select",
                        label="Selected Evaluation Cohort (2 to 4 Players)",
                        placeholder="Search and add up to 4 candidates...",
                        data=[{"label": name, "value": name} for name in all_player_names],
                        value=initial_values,
                        searchable=True,
                        maxValues=4,
                        clearable=False,
                    ),
                    dmc.Text("First player acts as the baseline starter. Subsequent candidates display relative +/- differentials.", size="10px", c="dimmed", mt=6),
                ]),
                title="Candidate Selection",
                subtitle="Configure the head-to-head evaluation cohort across clubs and leagues",
            ),

            dmc.Space(h=14),

            # CROSS POSITION NOTIFICATION
            html.Div(id="compare-position-warning"),

            dmc.Space(h=14),

            # HERO DECISION LAYER: RADAR FOOTPRINT + SIDE-BY-SIDE TACTICAL PROFILES
            dmc.Grid(
                [
                    dmc.GridCol(
                        create_section_card(
                            dmc.Tabs(
                                value="radar",
                                children=[
                                    dmc.TabsList([
                                        dmc.TabsTab("Radar Overlay (7D)", value="radar"),
                                        dmc.TabsTab("Attribute Breakdown (Bars)", value="bars"),
                                    ]),
                                    dmc.TabsPanel(
                                        dcc.Graph(
                                            id="compare-radar-chart",
                                            config={"displayModeBar": False},
                                            responsive=True,
                                            style={"height": "380px", "width": "100%"},
                                        ),
                                        value="radar",
                                    ),
                                    dmc.TabsPanel(
                                        dcc.Graph(
                                            id="compare-bar-chart",
                                            config={"displayModeBar": False},
                                            responsive=True,
                                            style={"height": "380px", "width": "100%"},
                                        ),
                                        value="bars",
                                    ),
                                ],
                            ),
                            title="Multi-Player Visual Footprint",
                            subtitle="Direct 7-dimensional footprint comparison across candidates",
                        ),
                        span={"base": 12, "lg": 6},
                    ),
                    dmc.GridCol(
                        create_section_card(
                            html.Div(id="compare-profiles-container"),
                            title="Tactical Candidate Profiles",
                            subtitle="Automated analytical strengths, watch-outs, and role context for each candidate",
                        ),
                        span={"base": 12, "lg": 6},
                    ),
                ],
                gap="md",
            ),

            dmc.Space(h=16),

            # EXECUTIVE VERDICT & COLLAPSIBLE STATISTICAL MATRIX TABLE
            create_section_card(
                html.Div(id="compare-stats-table-container", style={"overflowX": "auto"}),
                title="Head-to-Head Comparison Matrix & Verdict",
                subtitle="Executive decision trade-offs, live +/- deltas, and deep statistical breakdown",
                extra_header=dmc.Group([
                    dmc.Switch(
                        id="compare-delta-toggle",
                        label="Show Deltas (Δ vs Baseline)",
                        checked=True,
                        size="xs",
                        color="emerald",
                    ),
                    dmc.SegmentedControl(
                        id="compare-metric-mode",
                        data=[
                            {"label": "Standard Per-90 Rates", "value": "per90"},
                            {"label": "Season Total Counts", "value": "total"},
                        ],
                        value="per90",
                        size="xs",
                        color="emerald",
                    ),
                    dmc.Button(
                        "Export Matrix (CSV)",
                        id="compare-export-btn",
                        size="xs",
                        variant="light",
                        color="emerald",
                    ),
                    dcc.Download(id="compare-download-csv"),
                ], gap="xs", align="center", wrap="wrap"),
            ),
        ],
        fluid=True,
        p=0,
    )


# --------------------------------------------------
# CALLBACK
# --------------------------------------------------

@callback(
    Output("compare-position-warning", "children"),
    Output("compare-radar-chart", "figure"),
    Output("compare-bar-chart", "figure"),
    Output("compare-stats-table-container", "children"),
    Output("compare-profiles-container", "children"),
    Input("compare-players-select", "value"),
    Input("compare-metric-mode", "value"),
    Input("compare-delta-toggle", "checked"),
    Input("scout-analyst-mode", "data"),
)
def update_comparison_views(selected_names, metric_mode="per90", show_deltas=True, scout_analyst_mode="scout"):
    scout_analyst_mode = scout_analyst_mode or "scout"
    if not selected_names or len(selected_names) < 2:
        warning_msg = dmc.Alert(
            "Please select at least 2 players (up to 4) to generate the comparison matrix.",
            title="Selection Needed",
            color="orange",
            variant="light",
            radius="sm",
        )
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="Select 2 to 4 players to view comparison charts.",
            showarrow=False,
            font=dict(color=MUTED, size=13),
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
        )
        empty_fig.update_layout(paper_bgcolor=PANEL, plot_bgcolor=PANEL)
        return warning_msg, empty_fig, empty_fig, html.Div(), html.Div()

    players = [get_player_by_name(name) for name in selected_names if get_player_by_name(name) is not None]
    if len(players) < 2:
        return html.Div(), go.Figure(), go.Figure(), html.Div(), html.Div()

    # 1. Executive Head-to-Head Recruitment Verdict
    p1 = players[0]
    p2 = players[1]
    p1_edges = []
    p2_edges = []
    for attr, col in ATTRIBUTE_COLUMNS.items():
        v1 = float(p1.get(col, 50.0))
        v2 = float(p2.get(col, 50.0))
        diff = v2 - v1
        if diff >= 6.0:
            p2_edges.append((attr, diff, v2, v1))
        elif diff <= -6.0:
            p1_edges.append((attr, abs(diff), v1, v2))

    p1_edges.sort(key=lambda x: x[1], reverse=True)
    p2_edges.sort(key=lambda x: x[1], reverse=True)

    m1 = float(p1.get("Min", 0))
    m2 = float(p2.get("Min", 0))

    p1_edge_str = ", ".join([f"{e[0]} (+{e[1]:.1f})" for e in p1_edges[:3]]) if p1_edges else "Balanced output across baseline traits"
    p2_edge_str = ", ".join([f"{e[0]} (+{e[1]:.1f})" for e in p2_edges[:3]]) if p2_edges else "Balanced output across candidate traits"

    sample_warning_items = []
    if m1 < SAMPLE_SIZE_THRESHOLD:
        sample_warning_items.append(f"{p1['Player']} has limited minutes ({int(m1)}m < 900m)")
    if m2 < SAMPLE_SIZE_THRESHOLD:
        sample_warning_items.append(f"{p2['Player']} has limited minutes ({int(m2)}m < 900m)")

    sample_badge_ui = dmc.Badge(
        "Limited Sample Notice: " + " • ".join(sample_warning_items),
        color="orange",
        variant="light",
        size="xs",
    ) if sample_warning_items else None

    primary_tradeoff = f"{p1_edges[0][0]} ({p1['Player']})" if p1_edges else "Baseline profile"
    alt_tradeoff = f"{p2_edges[0][0]} ({p2['Player']})" if p2_edges else "Candidate profile"

    executive_verdict = dmc.Box(
        [
            dmc.Group([
                dmc.Group([
                    dmc.Text("EXECUTIVE HEAD-TO-HEAD RECRUITMENT VERDICT", size="10.5px", fw=800, c="teal", style={"letterSpacing": "0.8px"}),
                    dmc.Badge(
                        "👤 SCOUT VIEW" if scout_analyst_mode == "scout" else "🔬 ANALYST VIEW",
                        color="teal" if scout_analyst_mode == "scout" else "indigo",
                        variant="filled",
                        size="xs",
                    ),
                ], gap="xs"),
                *([sample_badge_ui] if sample_badge_ui else []),
            ], justify="space-between", align="center", mb="xs"),

            dmc.Grid([
                dmc.GridCol([
                    dmc.Group([
                        html.Span("●", style={"color": PLAYER_COMPARE_COLORS[0], "fontSize": "13px"}),
                        dmc.Text(f"Baseline Starter Advantage: {p1['Player']}", size="xs", fw=700, c="white"),
                    ], gap="xs"),
                    dmc.Text(f"Superior production in: {p1_edge_str}.", size="11px", c="#CBD5E1", mt=2),
                ], span={"base": 12, "md": 6}),
                dmc.GridCol([
                    dmc.Group([
                        html.Span("●", style={"color": PLAYER_COMPARE_COLORS[1], "fontSize": "13px"}),
                        dmc.Text(f"Target Alternative Advantage: {p2['Player']}", size="xs", fw=700, c="#38BDF8"),
                    ], gap="xs"),
                    dmc.Text(f"Superior production in: {p2_edge_str}.", size="11px", c="#CBD5E1", mt=2),
                ], span={"base": 12, "md": 6}),
            ], gap="sm"),

            dmc.Divider(my="xs", color=BORDER),
            dmc.Text(
                f"Recruitment Trade-off: Selecting {p2['Player']} over {p1['Player']} represents a strategic choice between {alt_tradeoff} vs {primary_tradeoff}. "
                "Review match video to confirm whether the stylistic profile aligns with squad tactical requirements.",
                size="11px",
                c="#94A3B8",
                style={"fontStyle": "italic", "lineHeight": 1.4},
            ),
        ],
        style={
            "backgroundColor": "#090D14",
            "border": f"1px solid {BORDER}",
            "borderLeft": "3px solid #10B981",
            "borderRadius": "5px",
            "padding": "12px 16px",
            "marginBottom": "14px",
        },
    )

    # 1. Cross-Position Warning
    positions = set(p["Pos"] for p in players)
    if len(positions) > 1:
        pos_list = ", ".join(positions)
        cross_pos_warning = dmc.Alert(
            f"Analytical Notice: You are comparing candidates from multiple position groups ({pos_list}). "
            "Percentiles are benchmarked strictly relative to peers within each candidate's own position cohort "
            "(e.g., Defender finishing is benchmarked against fellow defenders). Direct numerical equivalence should be interpreted in tactical context.",
            title="Cross-Cohort Percentile Notice",
            color="yellow",
            variant="light",
            radius="sm",
            p="sm",
            style={
                "backgroundColor": "rgba(245, 158, 11, 0.06)",
                "border": "1px solid rgba(245, 158, 11, 0.2)",
            },
        )
    else:
        pos = list(positions)[0]
        pos_name = {"DF": "Defenders", "MF": "Midfielders", "FW": "Forwards"}.get(pos, pos)
        cross_pos_warning = dmc.Text(
            f"✓ Homogeneous Cohort: All candidates belong to {pos_name}. Scores are directly comparable on identical position-relative percentile scales.",
            size="xs",
            c="dimmed",
        )

    # 2. Charts
    radar_fig = build_radar_chart(players=players, height=370)
    bar_fig = build_comparison_bars(players=players, height=370)

    # 3. Statistical Comparison Table
    table_headers = [dmc.TableTh("METRIC / DIMENSION", style={"color": TEXT, "width": "220px", "fontSize": "10px", "letterSpacing": "0.6px"})]
    for i, p in enumerate(players):
        color = PLAYER_COMPARE_COLORS[i % len(PLAYER_COMPARE_COLORS)]
        role_badge = dmc.Badge("BASELINE", color="emerald", variant="filled", size="xs") if i == 0 else dmc.Badge(f"TARGET #{i}", color="cyan", variant="light", size="xs")
        table_headers.append(
            dmc.TableTh(
                dmc.Box([
                    dmc.Group([
                        html.Span("●", style={"color": color, "fontSize": "14px", "lineHeight": 1}),
                        dmc.Text(p["Player"], fw=700, c="white", size="xs"),
                    ], gap="xs"),
                    dmc.Group([
                        role_badge,
                        dmc.Text(f"{p['Squad']} • {p.get('SubRole', p['Pos'])}", size="10px", c="dimmed"),
                    ], gap="xs", mt=4),
                ]),
                style={"color": TEXT},
            )
        )
    thead = dmc.TableThead(dmc.TableTr(table_headers))

    # Metric Rows Definition with Delta Support
    def make_row(label, values_fn, is_header=False, is_percentile=False, is_numeric=False, precision=1):
        cells = [dmc.TableTd(dmc.Text(label, fw=700 if is_header else 500, c="dimmed" if not is_header else "emerald", size="xs"))]
        baseline_num = None
        for i, p in enumerate(players):
            raw_val = values_fn(p)
            if is_header:
                cells.append(dmc.TableTd(dmc.Text(str(raw_val), fw=600, c="white", size="xs", style={"fontVariantNumeric": "tabular-nums"})))
            elif is_percentile or is_numeric:
                try:
                    num = float(raw_val)
                    delta_badge = None
                    if i == 0:
                        baseline_num = num
                        if show_deltas:
                            delta_badge = dmc.Badge("REF", size="xs", variant="outline", color="gray")
                    else:
                        if baseline_num is not None and show_deltas:
                            delta = num - baseline_num
                            if abs(delta) < 0.001:
                                delta_badge = dmc.Badge("0.0", size="xs", variant="light", color="gray")
                            elif delta > 0:
                                delta_badge = dmc.Badge(f"+{delta:.{precision}f}", size="xs", variant="light", color="emerald")
                            else:
                                delta_badge = dmc.Badge(f"{delta:.{precision}f}", size="xs", variant="light", color="red")

                    if is_percentile:
                        tier_info = get_percentile_tier(num)
                        val_span = dmc.Text(f"{num:.1f}", fw=700, size="xs", style={"color": tier_info["color"], "fontVariantNumeric": "tabular-nums"})
                    else:
                        val_span = dmc.Text(f"{num:.{precision}f}" if precision > 0 else f"{int(round(num))}", fw=600, size="xs", c="white", style={"fontVariantNumeric": "tabular-nums"})

                    content = dmc.Group([val_span, delta_badge] if delta_badge else [val_span], gap="xs", align="center")
                    cells.append(dmc.TableTd(content))
                except (ValueError, TypeError):
                    cells.append(dmc.TableTd(dmc.Text(str(raw_val), fw=400, size="xs", c="white")))
            else:
                cells.append(dmc.TableTd(dmc.Text(str(raw_val), fw=400, size="xs", c="white")))
        return dmc.TableTr(cells)

    rows = [
        # Metadata
        make_row("Club / Squad", lambda p: p["Squad"]),
        make_row("Competition / League", lambda p: p.get("Comp_Clean", "N/A")),
        make_row("Position Group", lambda p: p["Pos"]),
        make_row("Tactical Sub-Role", lambda p: p.get("SubRole", "N/A")),
        make_row("Nationality", lambda p: p.get("Nation_Display", p["Nation_Clean"])),
        make_row("Age (Born)", lambda p: f"{p['Age']} ({p['Born']})"),
        make_row("Minutes Played", lambda p: f"{p['Min']:,}m"),
        make_row("Tactical Playing Style", lambda p: p.get("PlayingStyle_Name", "N/A"), is_header=True),

        # Percentile Attributes
        make_row("Finishing Score", lambda p: p["Finishing_Score"], is_percentile=True),
        make_row("Creativity Score", lambda p: p["Creativity_Score"], is_percentile=True),
        make_row("Passing Score", lambda p: p["Passing_Score"], is_percentile=True),
        make_row("Progression Score", lambda p: p["Progression_Score"], is_percentile=True),
        make_row("Defending Score (pAdj)", lambda p: p["Defending_Score"], is_percentile=True),
        make_row("Ball Security Score", lambda p: p["BallSecurity_Score"], is_percentile=True),
        make_row("Aerial Score", lambda p: p["Aerial_Score"], is_percentile=True),
    ]

    # Production / Match Stats based on Metric Mode
    if metric_mode == "per90":
        rows.extend([
            make_row("Standard Per-90 Rates", lambda p: "---", is_header=True),
            make_row("Goals / 90", lambda p: p.get('Gls_per90', 0.0), is_numeric=True, precision=2),
            make_row("Expected Goals (xG) / 90", lambda p: p.get('xG_per90', 0.0), is_numeric=True, precision=2),
            make_row("Finishing Diff (G - xG)", lambda p: p.get('G-xG', 0.0), is_numeric=True, precision=2),
            make_row("Shot Quality (npxG/Sh)", lambda p: p.get('npxG/Sh', 0.0), is_numeric=True, precision=2),
            make_row("Assists / 90", lambda p: p.get('Ast_per90', 0.0), is_numeric=True, precision=2),
            make_row("Expected Assists (xA) / 90", lambda p: p.get('xA_per90', 0.0), is_numeric=True, precision=2),
            make_row("Shots (on Target) / 90", lambda p: f"{p.get('Sh_per90', 0.0):.2f} ({p.get('SoT_per90', 0.0):.2f})"),
            make_row("Pass Completion %", lambda p: p.get('Cmp%', 0.0), is_numeric=True, precision=1),
            make_row("Prog. Passes / 90", lambda p: p.get('PrgP_per90', 0.0), is_numeric=True, precision=1),
            make_row("Prog. Carries / 90", lambda p: p.get('PrgC_per90', 0.0), is_numeric=True, precision=1),
            make_row("pAdj Defending Actions / 90", lambda p: p.get('Tkl_pAdj_per90', 0.0) + p.get('Int_pAdj_per90', 0.0), is_numeric=True, precision=2),
            make_row("Raw Tackles + Int / 90", lambda p: p.get('Tkl_per90', 0.0) + p.get('Int_per90', 0.0), is_numeric=True, precision=2),
            make_row("Aerials Won / 90", lambda p: p.get('Won_per90', 0.0), is_numeric=True, precision=2),
        ])
    else:
        rows.extend([
            make_row("Season Total Counts", lambda p: "---", is_header=True),
            make_row("Goals (Season Total)", lambda p: p.get('Gls', 0), is_numeric=True, precision=0),
            make_row("Expected Goals (xG)", lambda p: p.get('xG', 0.0), is_numeric=True, precision=2),
            make_row("Finishing Diff (G - xG)", lambda p: p.get('G-xG', 0.0), is_numeric=True, precision=2),
            make_row("Shot Quality (npxG/Sh)", lambda p: p.get('npxG/Sh', 0.0), is_numeric=True, precision=2),
            make_row("Assists (Season Total)", lambda p: p.get('Ast', 0), is_numeric=True, precision=0),
            make_row("Expected Assists (xA)", lambda p: p.get('xA', 0.0), is_numeric=True, precision=2),
            make_row("Shots (on Target)", lambda p: f"{int(p.get('Sh', 0))} ({int(p.get('SoT', 0))})"),
            make_row("Pass Completion %", lambda p: p.get('Cmp%', 0.0), is_numeric=True, precision=1),
            make_row("Progressive Passes", lambda p: p.get('PrgP', 0), is_numeric=True, precision=0),
            make_row("Progressive Carries", lambda p: p.get('PrgC', 0), is_numeric=True, precision=0),
            make_row("pAdj Defending Actions", lambda p: p.get('Tkl_pAdj', 0) + p.get('Int_pAdj', 0), is_numeric=True, precision=0),
            make_row("Raw Tackles + Interceptions", lambda p: p.get('Tkl', 0) + p.get('Int', 0), is_numeric=True, precision=0),
            make_row("Aerial Duels Won", lambda p: p.get('Won', 0), is_numeric=True, precision=0),
        ])

    tbody = dmc.TableTbody(rows)
    stats_table = dmc.Table(
        [thead, tbody],
        striped=True,
        highlightOnHover=True,
        withTableBorder=True,
        style={"backgroundColor": PANEL, "fontSize": "12px", "borderColor": BORDER},
    )
    stats_table_accordion = dmc.Accordion(
        value="matrix" if scout_analyst_mode == "analyst" else None,
        styles={
            "item": {
                "backgroundColor": "#090D14",
                "border": f"1px solid {BORDER}",
                "borderRadius": "4px",
                "marginTop": "10px",
            },
            "control": {
                "color": "white",
                "padding": "10px 14px",
            },
            "panel": {
                "padding": "0 14px 14px 14px",
                "overflowX": "auto",
            },
        },
        children=[
            dmc.AccordionItem(
                [
                    dmc.AccordionControl(
                        dmc.Group([
                            dmc.Text("Comprehensive Statistical Delta Matrix & Volume Breakdown (15 Metrics)", fw=700, size="xs", c="white"),
                            dmc.Badge(
                                "ANALYST MATRIX (OPEN)" if scout_analyst_mode == "analyst" else "PROGRESSIVE DISCLOSURE",
                                color="indigo" if scout_analyst_mode == "analyst" else "teal",
                                variant="light",
                                size="xs",
                            ),
                            dmc.Text("Click to expand side-by-side production and +/- differentials", size="10px", c="dimmed"),
                        ], gap="xs")
                    ),
                    dmc.AccordionPanel(stats_table),
                ],
                value="matrix",
            )
        ],
    )
    stats_matrix_ui = html.Div([executive_verdict, stats_table_accordion])

    # 4. Tactical Profiles Cards Grid
    profile_cards = []
    for i, p in enumerate(players):
        color = PLAYER_COMPARE_COLORS[i % len(PLAYER_COMPARE_COLORS)]
        strengths, weaknesses = get_player_strengths_and_weaknesses(p)

        card = dmc.GridCol(
            dmc.Box(
                [
                    dmc.Group([
                        html.Span("●", style={"color": color, "fontSize": "14px", "lineHeight": 1}),
                        dmc.Text(p["Player"], fw=700, c="white", size="sm"),
                    ], gap="xs"),
                    dmc.Text(f"{p['Squad']} • {p['Pos']} • {p.get('SubRole', '')} • {p.get('PlayingStyle_Name', 'Specialist')}", size="10px", c="dimmed", mt=2),
                    dmc.Divider(my="xs", color=BORDER),

                    dmc.Text("KEY STRENGTHS", size="10px", fw=700, c="dimmed", style={"letterSpacing": "0.5px"}, mb=4),
                    dmc.Group([
                        dmc.Badge(f"{s['attribute']} ({s['score']:.1f})", color="emerald", variant="light", size="xs")
                        for s in strengths
                    ], gap="xs", mb="xs", wrap="wrap"),

                    dmc.Text("DEVELOPMENT PRIORITIES", size="10px", fw=700, c="dimmed", style={"letterSpacing": "0.5px"}, mb=4),
                    dmc.Group([
                        dmc.Badge(f"{w['attribute']} ({w['score']:.1f})", color="orange", variant="light", size="xs")
                        for w in weaknesses
                    ], gap="xs", wrap="wrap"),
                ],
                style={
                    "backgroundColor": "#0D131F",
                    "border": f"1px solid {BORDER}",
                    "borderTop": f"2px solid {color}",
                    "borderRadius": "4px",
                    "padding": "12px 14px",
                },
            ),
            span={"base": 12, "sm": 6, "lg": 12 // len(players)},
        )
        profile_cards.append(card)

    profiles_container = dmc.Grid(profile_cards, gap="md")

    return cross_pos_warning, radar_fig, bar_fig, stats_matrix_ui, profiles_container


# Export Comparison Matrix to CSV
@callback(
    Output("compare-download-csv", "data"),
    Input("compare-export-btn", "n_clicks"),
    State("compare-players-select", "value"),
    State("compare-metric-mode", "value"),
    prevent_initial_call=True,
)
def export_comparison_csv(n_clicks, selected_names, metric_mode):
    if not selected_names or len(selected_names) < 2:
        return dash.no_update
    players = [get_player_by_name(name) for name in selected_names if get_player_by_name(name) is not None]
    if len(players) < 2:
        return dash.no_update

    rows_data = []
    for i, p in enumerate(players):
        role_tag = "BASELINE" if i == 0 else f"TARGET #{i}"
        rows_data.append({
            "Recruitment_Role": role_tag,
            "Player": p["Player"],
            "Squad": p["Squad"],
            "Competition": p.get("Comp_Clean", "Big 5"),
            "Position": p["Pos"],
            "Tactical_SubRole": p.get("SubRole", "N/A"),
            "Age": p["Age"],
            "Minutes": p["Min"],
            "PlayingStyle_DNA": p.get("PlayingStyle_Name", "N/A"),
            "Finishing_Score": round(float(p["Finishing_Score"]), 1),
            "Creativity_Score": round(float(p["Creativity_Score"]), 1),
            "Passing_Score": round(float(p["Passing_Score"]), 1),
            "Progression_Score": round(float(p["Progression_Score"]), 1),
            "Defending_Score_pAdj": round(float(p["Defending_Score"]), 1),
            "BallSecurity_Score": round(float(p["BallSecurity_Score"]), 1),
            "Aerial_Score": round(float(p["Aerial_Score"]), 1),
            "Goals_per90": round(float(p.get("Gls_per90", 0.0)), 2),
            "xG_per90": round(float(p.get("xG_per90", 0.0)), 2),
            "Finishing_Diff_G_minus_xG": round(float(p.get("G-xG", 0.0)), 2),
            "Shot_Quality_npxG_per_Sh": round(float(p.get("npxG/Sh", 0.0)), 2),
            "Assists_per90": round(float(p.get("Ast_per90", 0.0)), 2),
            "xA_per90": round(float(p.get("xA_per90", 0.0)), 2),
            "PrgP_per90": round(float(p.get("PrgP_per90", 0.0)), 1),
            "PrgC_per90": round(float(p.get("PrgC_per90", 0.0)), 1),
            "pAdj_Defending_per90": round(float(p.get("Tkl_pAdj_per90", 0.0) + p.get("Int_pAdj_per90", 0.0)), 2),
        })
    df_exp = pd.DataFrame(rows_data)
    ref_name = players[0]["Player"].replace(" ", "_")
    return dcc.send_data_frame(df_exp.to_csv, f"scout_comparison_{ref_name}_matrix.csv", index=False)
