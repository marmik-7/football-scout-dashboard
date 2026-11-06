import dash
from dash import html, dcc, Input, Output, callback
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

dash.register_page(__name__, path="/player-comparison", name="Player Comparison", order=4)

df = load_data()
all_player_names = get_all_player_names()

DEFAULT_PLAYERS = ["Erling Haaland", "Kylian Mbappé"]
# Fallback if names differ slightly
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
                title="Player Comparison",
                subtitle="Head-to-head multi-dimensional evaluation. Benchmark 2 to 4 players simultaneously across percentile attributes and volume statistics.",
                badge_text="HEAD-TO-HEAD MATRIX",
            ),

            # CONTROLS PANEL
            create_section_card(
                dmc.Box([
                    dmc.MultiSelect(
                        id="compare-players-select",
                        label="Select Players to Compare (2 to 4)",
                        placeholder="Search and add up to 4 players...",
                        data=[{"label": name, "value": name} for name in all_player_names],
                        value=initial_values,
                        searchable=True,
                        maxValues=4,
                        clearable=False,
                    ),
                    dmc.Text("Select between 2 and 4 players from any club or position.", size="xs", c="dimmed", mt=6),
                ]),
                title="Comparison Candidates",
                subtitle="Add or remove players to compare their statistical profiles",
            ),

            dmc.Space(h=15),

            # CROSS POSITION WARNING CONTAINER
            html.Div(id="compare-position-warning"),

            dmc.Space(h=15),

            # RADAR & GROUPED BARS
            dmc.Grid(
                [
                    dmc.GridCol(
                        create_section_card(
                            dcc.Graph(
                                id="compare-radar-chart",
                                config={"displayModeBar": False},
                                responsive=True,
                            ),
                            title="Multi-Player Radar Overlay",
                            subtitle="Direct 7-dimensional footprint comparison",
                        ),
                        span={"base": 12, "lg": 6},
                    ),
                    dmc.GridCol(
                        create_section_card(
                            dcc.Graph(
                                id="compare-bar-chart",
                                config={"displayModeBar": False},
                                responsive=True,
                            ),
                            title="Attribute-by-Attribute Breakdown",
                            subtitle="Grouped comparison across the 7 scouting dimensions",
                        ),
                        span={"base": 12, "lg": 6},
                    ),
                ],
                gap="lg",
            ),

            dmc.Space(h=25),

            # SIDE-BY-SIDE STATISTICAL MATRIX TABLE
            create_section_card(
                html.Div(id="compare-stats-table-container", style={"overflowX": "auto"}),
                title="Statistical Comparison Matrix",
                subtitle="Direct side-by-side benchmarking of percentiles, production volume, and playing styles",
            ),

            dmc.Space(h=25),

            # TACTICAL PROFILES AND STRENGTHS
            create_section_card(
                html.Div(id="compare-profiles-container"),
                title="Tactical Strengths & Developmental Priorities",
                subtitle="Automated scouting observations for each evaluated candidate",
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
)
def update_comparison_views(selected_names):
    if not selected_names or len(selected_names) < 2:
        warning_msg = dmc.Alert(
            "Please select at least 2 players (up to 4) to generate the comparison matrix.",
            title="Selection Needed",
            color="yellow",
            variant="light",
        )
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="Select 2 to 4 players to view comparison charts.",
            showarrow=False,
            font=dict(color=MUTED, size=14),
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

    # 1. Cross-Position Warning
    positions = set(p["Pos"] for p in players)
    if len(positions) > 1:
        pos_list = ", ".join(positions)
        cross_pos_warning = dmc.Alert(
            f"Analytical Notice: You are comparing players from multiple position groups ({pos_list}). "
            "Percentile scores (0–100) are engineered strictly relative to peers in each player's own position group "
            "(e.g., Defender finishing is benchmarked against other defenders). Direct numerical equivalence across positions should be interpreted with caution.",
            title="Cross-Position Percentile Comparison Detected",
            color="yellow",
            variant="light",
            radius="md",
            p="sm",
            style={
                "backgroundColor": "rgba(245, 158, 11, 0.08)",
                "borderColor": "rgba(245, 158, 11, 0.25)",
                "color": "#F8FAFC",
            },
        )
    else:
        pos = list(positions)[0]
        pos_name = {"DF": "Defenders", "MF": "Midfielders", "FW": "Forwards"}.get(pos, pos)
        cross_pos_warning = dmc.Text(
            f"All selected candidates are {pos_name}. Scores are directly comparable on the same position-relative percentile scale.",
            size="xs",
            c="dimmed",
        )

    # 2. Charts
    radar_fig = build_radar_chart(players=players, height=380)
    bar_fig = build_comparison_bars(players=players, height=380)

    # 3. Statistical Comparison Table
    table_headers = [dmc.TableTh("Metric / Dimension", style={"color": TEXT, "width": "220px"})]
    for i, p in enumerate(players):
        color = PLAYER_COMPARE_COLORS[i % len(PLAYER_COMPARE_COLORS)]
        table_headers.append(
            dmc.TableTh(
                dmc.Group([
                    dmc.Badge("●", color=color, variant="transparent", size="xs", p=0),
                    dmc.Text(p["Player"], fw=700, c="white"),
                ], gap="xs"),
                style={"color": TEXT},
            )
        )
    thead = dmc.TableThead(dmc.TableTr(table_headers))

    # Metric Rows Definition
    def make_row(label, values_fn, is_header=False, is_percentile=False):
        cells = [dmc.TableTd(dmc.Text(label, fw=700 if is_header else 500, c="dimmed" if not is_header else "lime"))]
        for p in players:
            val = values_fn(p)
            if is_percentile:
                num = float(val)
                tier_info = get_percentile_tier(num)
                cells.append(dmc.TableTd(dmc.Text(f"{num:.1f}", fw=700, style={"color": tier_info["color"], "fontVariantNumeric": "tabular-nums"})))
            else:
                cells.append(dmc.TableTd(dmc.Text(str(val), fw=600 if is_header else 400, c="white", style={"fontVariantNumeric": "tabular-nums"})))
        return dmc.TableTr(cells)

    rows = [
        # Metadata
        make_row("Club / Squad", lambda p: p["Squad"]),
        make_row("Position Group", lambda p: p["Pos"]),
        make_row("Nationality", lambda p: p.get("Nation_Display", p["Nation_Clean"])),
        make_row("Age (Born)", lambda p: f"{p['Age']} ({p['Born']})"),
        make_row("Minutes Played", lambda p: f"{p['Min']:,}m"),
        make_row("Tactical Playing Style", lambda p: p.get("PlayingStyle_Name", "N/A"), is_header=True),

        # Percentile Attributes
        make_row("Finishing Score", lambda p: p["Finishing_Score"], is_percentile=True),
        make_row("Creativity Score", lambda p: p["Creativity_Score"], is_percentile=True),
        make_row("Passing Score", lambda p: p["Passing_Score"], is_percentile=True),
        make_row("Progression Score", lambda p: p["Progression_Score"], is_percentile=True),
        make_row("Defending Score", lambda p: p["Defending_Score"], is_percentile=True),
        make_row("Ball Security Score", lambda p: p["BallSecurity_Score"], is_percentile=True),
        make_row("Aerial Score", lambda p: p["Aerial_Score"], is_percentile=True),

        # Volume Metrics
        make_row("Goals + Assists (G+A)", lambda p: int(p.get("Gls", 0) + p.get("Ast", 0))),
        make_row("Expected Goals (xG)", lambda p: f"{p.get('xG', 0.0):.2f}"),
        make_row("Expected Assists (xA)", lambda p: f"{p.get('xA', 0.0):.2f}"),
        make_row("Pass Completion %", lambda p: f"{p.get('Cmp%', 0.0):.1f}%"),
        make_row("Progressive Passes", lambda p: int(p.get("PrgP", 0))),
        make_row("Progressive Carries", lambda p: int(p.get("PrgC", 0))),
        make_row("Tackles + Interceptions", lambda p: int(p.get("Tkl", 0) + p.get("Int", 0))),
    ]

    tbody = dmc.TableTbody(rows)
    stats_table = dmc.Table(
        [thead, tbody],
        striped=True,
        highlightOnHover=True,
        withTableBorder=True,
        style={"backgroundColor": PANEL, "fontSize": "13px", "borderColor": BORDER},
    )

    # 4. Tactical Profiles Cards Grid
    profile_cards = []
    for i, p in enumerate(players):
        color = PLAYER_COMPARE_COLORS[i % len(PLAYER_COMPARE_COLORS)]
        strengths, weaknesses = get_player_strengths_and_weaknesses(p)

        card = dmc.GridCol(
            dmc.Card(
                [
                    dmc.Group([
                        dmc.Badge("●", color=color, variant="transparent", size="sm", p=0),
                        dmc.Title(p["Player"], order=4, c="white"),
                    ], gap="xs"),
                    dmc.Text(f"{p['Squad']} • {p['Pos']} • Style: {p.get('PlayingStyle_Name', 'Specialist')}", size="xs", c="dimmed", mt=2),
                    dmc.Divider(my="sm"),

                    dmc.Text("KEY STRENGTHS", size="xs", fw=700, c="lime", mb=4),
                    dmc.Group([
                        dmc.Badge(f"{s['attribute']} ({s['score']:.1f})", color="lime", variant="light", size="xs")
                        for s in strengths
                    ], gap="xs", mb="sm", wrap="wrap"),

                    dmc.Text("VULNERABILITIES / LOWEST VOLUMES", size="xs", fw=700, c="orange", mb=4),
                    dmc.Group([
                        dmc.Badge(f"{w['attribute']} ({w['score']:.1f})", color="orange", variant="light", size="xs")
                        for w in weaknesses
                    ], gap="xs", wrap="wrap"),
                ],
                withBorder=True,
                radius="md",
                p="md",
                style={"backgroundColor": "#131E30", "borderColor": BORDER, "borderTop": f"3px solid {color}"},
            ),
            span={"base": 12, "sm": 6, "lg": 12 // len(players)},
        )
        profile_cards.append(card)

    profiles_container = dmc.Grid(profile_cards, gap="md")

    return cross_pos_warning, radar_fig, bar_fig, stats_table, profiles_container

