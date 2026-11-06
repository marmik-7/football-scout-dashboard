import dash
from dash import html, dcc, Input, Output, callback
import dash_mantine_components as dmc
import plotly.graph_objects as go
import pandas as pd

from app.utils.data_loader import (
    load_data,
    get_unique_squads,
    get_unique_nations,
    get_unique_competitions,
    get_unique_subroles,
)
from app.utils.styling import (
    PANEL,
    BORDER,
    TEXT,
    MUTED,
    SUBTLE,
    ACCENT,
    POSITION_COLORS,
    POSITION_NAMES,
    ATTRIBUTE_COLUMNS,
    create_page_header,
    create_section_card,
    style_figure,
    get_percentile_tier,
)
from app.utils.metric_definitions import get_sample_size_badge, SAMPLE_SIZE_THRESHOLD

dash.register_page(__name__, path="/player-rankings", name="Rankings", order=7)

df = load_data()
unique_squads = get_unique_squads()
unique_nations = get_unique_nations()
unique_competitions = get_unique_competitions()
unique_subroles = get_unique_subroles()


# --------------------------------------------------
# PAGE LAYOUT
# --------------------------------------------------

layout = dmc.Container(
    [
        create_page_header(
            title="Player Leaderboards",
            subtitle="Benchmark top-ranked candidates across scouting dimensions, position groups, and tactical archetypes.",
            badge_text="GLOBAL RANKINGS",
        ),

        # FILTER AND RANKING CONTROLS
        dmc.Card(
            [
                # Row 1: Positional & Geographic Scope
                dmc.Grid(
                    [
                        dmc.GridCol(
                            dmc.Select(
                                id="rankings-pos",
                                label="Position Scope",
                                data=[
                                    {"label": "Forwards (FW) — Default", "value": "FW"},
                                    {"label": "Midfielders (MF)", "value": "MF"},
                                    {"label": "Defenders (DF)", "value": "DF"},
                                    {"label": "All Positions (Cross-Position)", "value": "ALL"},
                                ],
                                value="FW",
                                allowDeselect=False,
                            ),
                            span={"base": 12, "sm": 6, "md": 2},
                        ),
                        dmc.GridCol(
                            dmc.Select(
                                id="rankings-subrole",
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
                                id="rankings-attr",
                                label="Scouting Dimension",
                                data=[
                                    {"label": f"{name} (Percentile)", "value": name}
                                    for name in ATTRIBUTE_COLUMNS
                                ],
                                value="Finishing",
                                allowDeselect=False,
                            ),
                            span={"base": 12, "sm": 6, "md": 2.5},
                        ),
                        dmc.GridCol(
                            dmc.Select(
                                id="rankings-comp",
                                label="Competition / League",
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
                                id="rankings-age-group",
                                label="Age Bracket",
                                data=[
                                    {"label": "All Ages", "value": "ALL"},
                                    {"label": "U-21 Prospects (≤21)", "value": "U21"},
                                    {"label": "U-23 Emerging (≤23)", "value": "U23"},
                                    {"label": "Peak Prime (24–29)", "value": "PRIME"},
                                    {"label": "Experienced (30+)", "value": "30PLUS"},
                                ],
                                value="ALL",
                                allowDeselect=False,
                            ),
                            span={"base": 12, "sm": 6, "md": 2.5},
                        ),
                    ],
                    gap="sm",
                ),

                dmc.Divider(my="sm", color="rgba(255, 255, 255, 0.06)"),

                # Row 2: Club & Output Depth
                dmc.Grid(
                    [
                        dmc.GridCol(
                            dmc.Select(
                                id="rankings-squad",
                                label="Club / Squad",
                                data=[{"label": "All Clubs", "value": "ALL"}] + [
                                    {"label": s, "value": s} for s in unique_squads
                                ],
                                value="ALL",
                                searchable=True,
                                allowDeselect=False,
                            ),
                            span={"base": 12, "sm": 6, "md": 4},
                        ),
                        dmc.GridCol(
                            dmc.Select(
                                id="rankings-depth",
                                label="Leaderboard Depth",
                                data=[
                                    {"label": "Top 10 Leaders", "value": 10},
                                    {"label": "Top 25 Leaders", "value": 25},
                                    {"label": "Top 50 Leaders", "value": 50},
                                    {"label": "Top 100 Leaders", "value": 100},
                                ],
                                value=10,
                                allowDeselect=False,
                            ),
                            span={"base": 12, "sm": 6, "md": 4},
                        ),
                        dmc.GridCol(
                            dmc.Select(
                                id="rankings-order",
                                label="Ranking Order",
                                data=[
                                    {"label": "Highest to Lowest (Desc)", "value": "desc"},
                                    {"label": "Lowest to Highest (Asc)", "value": "asc"},
                                ],
                                value="desc",
                                allowDeselect=False,
                            ),
                            span={"base": 12, "sm": 6, "md": 4},
                        ),
                    ],
                    gap="sm",
                ),
            ],
            withBorder=True,
            radius="md",
            p="md",
            style={"backgroundColor": "#0F172A", "borderColor": "rgba(255, 255, 255, 0.08)"},
        ),

        dmc.Space(h=15),

        # WARNING / ANALYTICAL NOTICE CONTAINER
        html.Div(id="rankings-notice-container"),

        dmc.Space(h=15),

        # RANKED BAR CHART
        create_section_card(
            dcc.Graph(
                id="rankings-bar-chart",
                config={"displayModeBar": False},
                responsive=True,
            ),
            title="Visual Leaderboard",
            subtitle="Percentile score distribution of top-ranked candidates",
        ),

        dmc.Space(h=20),

        # LEADERBOARD TABLE
        create_section_card(
            html.Div(id="rankings-table-container", style={"overflowX": "auto"}),
            title="Statistical Leaderboard Matrix",
            subtitle="Candidate records, empirical scores, and multidimensional profile",
        ),
    ],
    fluid=True,
    p=0,
)


# --------------------------------------------------
# CALLBACK
# --------------------------------------------------

@callback(
    Output("rankings-notice-container", "children"),
    Output("rankings-bar-chart", "figure"),
    Output("rankings-table-container", "children"),
    Input("rankings-pos", "value"),
    Input("rankings-subrole", "value"),
    Input("rankings-attr", "value"),
    Input("rankings-comp", "value"),
    Input("rankings-age-group", "value"),
    Input("rankings-depth", "value"),
    Input("rankings-order", "value"),
    Input("rankings-squad", "value"),
    Input("scout-analyst-mode", "data"),
)
def update_rankings(pos, subrole, attr, comp, age_group, depth, order, squad, scout_analyst_mode="scout"):
    scout_analyst_mode = scout_analyst_mode or "scout"
    if not attr or attr not in ATTRIBUTE_COLUMNS:
        attr = "Finishing"
    if not pos or pos not in ["FW", "MF", "DF", "ALL"]:
        pos = "FW"

    col = ATTRIBUTE_COLUMNS[attr]
    depth = int(depth) if depth else 10
    ascending = (order == "asc")

    # 1. Analytical Notice
    if pos == "ALL":
        notice = dmc.Alert(
            "Analytical Warning: You have selected 'All Positions'. "
            "Percentile scores are calculated relative to peers within each player's position group. "
            "A Defender with an 85th percentile Finishing score is ranked against other defenders, not forwards. "
            "Direct cross-position comparisons reflect within-position standing rather than absolute capability.",
            title="Cross-Position Percentile Comparison Notice",
            color="yellow",
            variant="light",
            radius="sm",
            p="sm",
            style={
                "backgroundColor": "rgba(245, 158, 11, 0.05)",
                "borderColor": "rgba(245, 158, 11, 0.20)",
                "color": "#F8FAFC",
                "fontSize": "12px",
            },
        )
        pos_display = "Players (All Positions)"
    else:
        pos_display = POSITION_NAMES.get(pos, pos)
        notice = dmc.Group([
            dmc.Badge("●", color="teal", variant="transparent", size="xs", p=0),
            dmc.Text(
                f"Rankings benchmarked strictly among {pos_display.lower()} with ≥600 minutes. Scores span 0 to 100 percentile.",
                size="xs",
                c=MUTED,
            ),
        ], gap=6)

    # 2. Filter dataset
    filtered = df.copy()
    if pos != "ALL":
        filtered = filtered[filtered["Pos"] == pos]

    # Tactical Sub-Role filter
    if subrole and subrole != "ALL" and "SubRole" in filtered.columns:
        filtered = filtered[filtered["SubRole"] == subrole]
        pos_display = f"{subrole}s" if not subrole.endswith("s") else subrole

    # League / Competition filter
    if comp and comp != "ALL":
        filtered = filtered[filtered["Comp_Clean"].apply(lambda c: comp in [x.strip() for x in str(c).split(",")])]

    # Age Bracket filter
    if age_group and age_group != "ALL":
        if age_group == "U21":
            filtered = filtered[(filtered["Age"] > 0) & (filtered["Age"] <= 21)]
        elif age_group == "U23":
            filtered = filtered[(filtered["Age"] > 0) & (filtered["Age"] <= 23)]
        elif age_group == "PRIME":
            filtered = filtered[(filtered["Age"] >= 24) & (filtered["Age"] <= 29)]
        elif age_group == "30PLUS":
            filtered = filtered[filtered["Age"] >= 30]

    if squad and squad != "ALL":
        filtered = filtered[filtered["Squad"].apply(lambda s: squad in [c.strip() for c in str(s).split(",")])]

    if filtered.empty:
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="No players found matching the filter criteria.",
            showarrow=False,
            font=dict(color=MUTED, size=13),
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
        )
        empty_fig = style_figure(empty_fig, 450)
        empty_table = dmc.Alert("No candidates found.", color="yellow", variant="light")
        return notice, empty_fig, empty_table

    # 3. Sort and slice
    filtered = filtered.sort_values(col, ascending=ascending)
    top_candidates = filtered.head(depth).copy()

    # For horizontal bar chart, sort ascending so rank #1 is at the top of the chart
    chart_candidates = top_candidates.sort_values(col, ascending=(not ascending)).copy()

    # 4. Ranked Bar Chart
    chart_height = max(380, min(800, len(chart_candidates) * 26 + 100))
    comp_title = f" ({comp})" if comp and comp != "ALL" else ""
    age_title = f" [{age_group}]" if age_group and age_group != "ALL" else ""
    chart_title = f"Top {len(chart_candidates)} {pos_display}{comp_title}{age_title} — {attr}"

    nat_col = "Nation_Display" if "Nation_Display" in chart_candidates.columns else "Nation_Clean"

    fig = go.Figure(
        go.Bar(
            x=chart_candidates[col],
            y=chart_candidates["Player_Unique"],
            orientation="h",
            marker=dict(
                color="#10B981",
                line=dict(color="#090D14", width=1),
            ),
            text=chart_candidates[col].apply(lambda v: f"{v:.1f}"),
            textposition="outside",
            cliponaxis=False,
            customdata=chart_candidates[["Player", "Squad", "Pos", nat_col, "Min"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Percentile Score: <b>%{x:.1f}</b><br>"
                "Club: %{customdata[1]}<br>"
                "Position: %{customdata[2]}<br>"
                "Nationality: %{customdata[3]}<br>"
                "Minutes: %{customdata[4]:,}m"
                "<extra></extra>"
            ),
        )
    )

    fig = style_figure(fig, height=chart_height)
    fig.update_layout(
        title=dict(text=chart_title, font=dict(color="#FFFFFF", size=14)),
        xaxis=dict(
            title=dict(text="Percentile Score (0–100)", font=dict(color=MUTED, size=11)),
            range=[0, 110],
            gridcolor="rgba(255, 255, 255, 0.05)",
            tickfont=dict(color=MUTED, size=10),
        ),
        yaxis=dict(
            title="",
            gridcolor="rgba(255, 255, 255, 0.05)",
            tickfont=dict(color=TEXT, size=11),
            categoryorder="array",
            categoryarray=chart_candidates["Player_Unique"].tolist(),
            automargin=True,
        ),
        margin=dict(l=160, r=35, t=50, b=35),
    )

    # 5. Leaderboard Table
    if scout_analyst_mode == "scout":
        # Role-tailored and dimension-specific production columns
        if attr == "Finishing":
            extra_headers = [
                dmc.TableTh("GOALS / 90", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
                dmc.TableTh("xG / 90", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
                dmc.TableTh("G - xG", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
                dmc.TableTh("SHOT QUAL.", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            ]
        elif attr in ["Passing", "Progression"]:
            extra_headers = [
                dmc.TableTh("PROG. PASS / 90", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
                dmc.TableTh("PROG. CARRY / 90", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
                dmc.TableTh("PASS ACC. %", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
                dmc.TableTh("KEY PASS / 90", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            ]
        elif attr in ["Defending", "Aerial"]:
            extra_headers = [
                dmc.TableTh("pAdj DEFENDING", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
                dmc.TableTh("RAW TKL+INT", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
                dmc.TableTh("AERIALS WON / 90", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
                dmc.TableTh("AERIAL WIN %", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            ]
        elif attr == "Creativity":
            extra_headers = [
                dmc.TableTh("KEY PASSES / 90", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
                dmc.TableTh("xA / 90", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
                dmc.TableTh("SCA / 90", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
                dmc.TableTh("ASSISTS / 90", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            ]
        else: # Ball Security
            extra_headers = [
                dmc.TableTh("PASS ACC. %", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
                dmc.TableTh("MISCONTROLS / 90", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
                dmc.TableTh("DISPOSSESSED / 90", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
                dmc.TableTh("DRIBBLES / 90", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            ]

        thead = dmc.TableThead(
            dmc.TableTr([
                dmc.TableTh("RANK", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "width": "50px"}),
                dmc.TableTh("CANDIDATE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
                dmc.TableTh("SQUAD / LEAGUE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
                dmc.TableTh("ROLE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
                dmc.TableTh("MINUTES", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
                dmc.TableTh(f"{attr.upper()} SCORE", style={"color": "#10B981", "fontWeight": "700", "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
                *extra_headers,
                dmc.TableTh("ACTION", style={"color": TEXT, "textAlign": "center", "fontSize": "10px", "letterSpacing": "0.6px"}),
            ])
        )

        rows = []
        for rank, (_, r) in enumerate(top_candidates.iterrows(), start=1):
            pos_badge_color = "blue" if r["Pos"] == "DF" else "teal" if r["Pos"] == "MF" else "orange"
            target_score = r[col]
            tier = get_percentile_tier(target_score)
            profile_url = f"/player-profile?player={r['Player_Unique']}"
            mins = float(r.get("Min", 0))

            if rank == 1:
                rank_badge = dmc.Badge(f"#{rank}", color="yellow", variant="filled", size="xs")
            elif rank == 2:
                rank_badge = dmc.Badge(f"#{rank}", color="gray", variant="filled", size="xs")
            elif rank == 3:
                rank_badge = dmc.Badge(f"#{rank}", color="orange", variant="filled", size="xs")
            else:
                rank_badge = dmc.Badge(f"#{rank}", color="gray", variant="light", size="xs")

            sample_pill = dmc.Badge(f"{int(mins)}m (Low)", color="orange", variant="outline", size="xs", style={"fontSize": "8.5px", "height": "14px", "padding": "0 3px"}) if mins < SAMPLE_SIZE_THRESHOLD else None

            # Cells based on attr
            if attr == "Finishing":
                extra_cells = [
                    dmc.TableTd(dmc.Text(f"{r.get('Gls_per90', 0.0):.2f}", size="xs", fw=600, c="white", style={"fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                    dmc.TableTd(dmc.Text(f"{r.get('xG_per90', 0.0):.2f}", size="xs", c="#94A3B8", style={"fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                    dmc.TableTd(dmc.Text(f"{float(r.get('G-xG', 0.0)):+.2f}", size="xs", fw=600, style={"color": ACCENT if float(r.get('G-xG', 0.0)) >= 0 else "#F59E0B", "fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                    dmc.TableTd(dmc.Text(f"{float(r.get('npxG/Sh', 0.0)):.2f}", size="xs", c="#94A3B8", style={"fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                ]
            elif attr in ["Passing", "Progression"]:
                extra_cells = [
                    dmc.TableTd(dmc.Text(f"{r.get('PrgP_per90', 0.0):.1f}", size="xs", fw=600, c="white", style={"fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                    dmc.TableTd(dmc.Text(f"{r.get('PrgC_per90', 0.0):.1f}", size="xs", c="#94A3B8", style={"fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                    dmc.TableTd(dmc.Text(f"{float(r.get('Cmp%', 0.0)):.1f}%", size="xs", fw=600, c="white", style={"fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                    dmc.TableTd(dmc.Text(f"{r.get('KP_per90', 0.0):.2f}", size="xs", c="#94A3B8", style={"fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                ]
            elif attr in ["Defending", "Aerial"]:
                padj_def = float(r.get('Tkl_pAdj_per90', 0.0) + r.get('Int_pAdj_per90', 0.0))
                raw_def = float(r.get('Tkl_per90', 0.0) + r.get('Int_per90', 0.0))
                extra_cells = [
                    dmc.TableTd(dmc.Text(f"{padj_def:.2f}", size="xs", fw=600, c="white", style={"fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                    dmc.TableTd(dmc.Text(f"{raw_def:.2f}", size="xs", c="#94A3B8", style={"fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                    dmc.TableTd(dmc.Text(f"{r.get('Won_per90', 0.0):.2f}", size="xs", c="#94A3B8", style={"fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                    dmc.TableTd(dmc.Text(f"{float(r.get('Won%', 0.0)):.1f}%", size="xs", fw=600, style={"color": ACCENT if float(r.get('Won%', 0.0)) >= 60 else "#94A3B8", "fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                ]
            elif attr == "Creativity":
                extra_cells = [
                    dmc.TableTd(dmc.Text(f"{r.get('KP_per90', 0.0):.2f}", size="xs", fw=600, c="white", style={"fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                    dmc.TableTd(dmc.Text(f"{r.get('xA_per90', 0.0):.2f}", size="xs", c="#94A3B8", style={"fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                    dmc.TableTd(dmc.Text(f"{r.get('SCA_per90', 0.0):.2f}", size="xs", fw=600, c="white", style={"fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                    dmc.TableTd(dmc.Text(f"{r.get('Ast_per90', 0.0):.2f}", size="xs", c="#94A3B8", style={"fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                ]
            else: # Ball Security
                extra_cells = [
                    dmc.TableTd(dmc.Text(f"{float(r.get('Cmp%', 0.0)):.1f}%", size="xs", fw=600, c="white", style={"fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                    dmc.TableTd(dmc.Text(f"{r.get('Mis_per90', 0.0):.2f}", size="xs", c="#F59E0B", style={"fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                    dmc.TableTd(dmc.Text(f"{r.get('Dis_per90', 0.0):.2f}", size="xs", c="#F59E0B", style={"fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                    dmc.TableTd(dmc.Text(f"{r.get('Succ_per90', 0.0):.2f}", size="xs", c="#94A3B8", style={"fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                ]

            rows.append(
                dmc.TableTr([
                    dmc.TableTd(rank_badge),
                    dmc.TableTd([
                        dmc.Group([
                            dmc.Text(r["Player"], fw=700, size="xs", c="white"),
                            *([sample_pill] if sample_pill else []),
                        ], gap=4, align="center"),
                        dmc.Text(f"{r.get('Nation_Display', r['Nation_Clean'])} • Age {r.get('Age', '-')}", size="10px", c="#64748B"),
                    ]),
                    dmc.TableTd([
                        dmc.Text(r["Squad"], size="xs", fw=500, c="white"),
                        dmc.Text(r.get("Comp_Clean", ""), size="10px", c="#64748B"),
                    ]),
                    dmc.TableTd([
                        dmc.Badge(r["Pos"], color=pos_badge_color, variant="light", size="xs"),
                        dmc.Text(r.get("SubRole", ""), size="10px", c="#64748B", mt=2),
                    ]),
                    dmc.TableTd(dmc.Text(f"{int(mins):,}m", size="xs", c="#64748B", style={"fontVariantNumeric": "tabular-nums"})),
                    dmc.TableTd(dmc.Text(f"{target_score:.1f}", size="xs", fw=700, style={"color": tier["color"], "fontVariantNumeric": "tabular-nums", "textAlign": "right"})),
                    *extra_cells,
                    dmc.TableTd(
                        dcc.Link(
                            dmc.Button("Dossier →", size="xs", variant="subtle", color="teal"),
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
            striped=False,
            highlightOnHover=True,
            withTableBorder=False,
            style={"fontSize": "12.5px"},
        )
        return notice, fig, table

    # ANALYST VIEW: Full 7-dimension score matrix
    thead = dmc.TableThead(
        dmc.TableTr([
            dmc.TableTh("RANK", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "width": "50px"}),
            dmc.TableTh("CANDIDATE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh("SQUAD / LEAGUE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh("ROLE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh("NAT", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh("MINUTES", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh(f"{attr.upper()} SCORE", style={"color": "#10B981", "fontWeight": "700", "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("TACTICAL DNA", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh("FIN", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("CRE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("PAS", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("PRG", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("DEF", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "right"}),
            dmc.TableTh("ACTION", style={"color": TEXT, "textAlign": "center", "fontSize": "10px", "letterSpacing": "0.6px"}),
        ])
    )

    rows = []
    for rank, (_, r) in enumerate(top_candidates.iterrows(), start=1):
        pos_badge_color = "blue" if r["Pos"] == "DF" else "teal" if r["Pos"] == "MF" else "orange"
        target_score = r[col]
        tier = get_percentile_tier(target_score)
        profile_url = f"/player-profile?player={r['Player_Unique']}"
        mins = float(r.get("Min", 0))

        # Podium coloring
        if rank == 1:
            rank_badge = dmc.Badge(f"#{rank}", color="yellow", variant="filled", size="xs")
        elif rank == 2:
            rank_badge = dmc.Badge(f"#{rank}", color="gray", variant="filled", size="xs")
        elif rank == 3:
            rank_badge = dmc.Badge(f"#{rank}", color="orange", variant="filled", size="xs")
        else:
            rank_badge = dmc.Badge(f"#{rank}", color="gray", variant="light", size="xs")

        sample_pill = dmc.Badge(f"{int(mins)}m (Low)", color="orange", variant="outline", size="xs", style={"fontSize": "8.5px", "height": "14px", "padding": "0 3px"}) if mins < SAMPLE_SIZE_THRESHOLD else None

        rows.append(
            dmc.TableTr([
                dmc.TableTd(rank_badge),
                dmc.TableTd([
                    dmc.Group([
                        dmc.Text(r["Player"], fw=700, size="xs", c="white"),
                        *([sample_pill] if sample_pill else []),
                    ], gap=4, align="center"),
                    dmc.Text(f"Age {r.get('Age', '-')}", size="10px", c="#64748B"),
                ]),
                dmc.TableTd([
                    dmc.Text(r["Squad"], size="xs", fw=500, c="white"),
                    dmc.Text(r.get("Comp_Clean", ""), size="10px", c="#64748B"),
                ]),
                dmc.TableTd([
                    dmc.Badge(r["Pos"], color=pos_badge_color, variant="light", size="xs"),
                    dmc.Text(r.get("SubRole", ""), size="10px", c="#64748B", mt=2),
                ]),
                dmc.TableTd(dmc.Text(r.get("Nation_Display", r["Nation_Clean"]), size="xs", c="white")),
                dmc.TableTd(dmc.Text(f"{r['Min']:,}m", size="xs", c="#64748B", style={"fontVariantNumeric": "tabular-nums"})),
                dmc.TableTd(dmc.Text(f"{target_score:.1f}", size="xs", fw=700, style={"color": tier["color"], "fontVariantNumeric": "tabular-nums"})),
                dmc.TableTd(dmc.Text(r.get("PlayingStyle_Name", "Specialist"), size="xs", c="#94A3B8")),

                dmc.TableTd(dmc.Text(f"{r['Finishing_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Finishing_Score'])["color"], "fontVariantNumeric": "tabular-nums"})),
                dmc.TableTd(dmc.Text(f"{r['Creativity_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Creativity_Score'])["color"], "fontVariantNumeric": "tabular-nums"})),
                dmc.TableTd(dmc.Text(f"{r['Passing_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Passing_Score'])["color"], "fontVariantNumeric": "tabular-nums"})),
                dmc.TableTd(dmc.Text(f"{r['Progression_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Progression_Score'])["color"], "fontVariantNumeric": "tabular-nums"})),
                dmc.TableTd(dmc.Text(f"{r['Defending_Score']:.1f}", size="xs", fw=600, style={"color": get_percentile_tier(r['Defending_Score'])["color"], "fontVariantNumeric": "tabular-nums"})),

                dmc.TableTd(
                    dcc.Link(
                        dmc.Button("Dossier →", size="xs", variant="subtle", color="teal"),
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
        striped=False,
        highlightOnHover=True,
        withTableBorder=False,
        style={"fontSize": "12.5px"},
    )

    return notice, fig, table
