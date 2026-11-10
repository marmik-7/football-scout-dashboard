import dash
from dash import html, dcc, Input, Output, State, callback
import dash_mantine_components as dmc
import pandas as pd
import numpy as np

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
    ATTRIBUTE_COLUMNS,
    create_page_header,
    create_section_card,
    get_percentile_tier,
)
from app.utils.metric_definitions import get_sample_size_badge, SAMPLE_SIZE_THRESHOLD
from app.utils.player_portraits import render_player_portrait

dash.register_page(__name__, path="/player-explorer", name="Player Explorer", order=2)

df = load_data()
unique_squads = get_unique_squads()
unique_nations = get_unique_nations()
unique_competitions = get_unique_competitions()
unique_subroles = get_unique_subroles()

PAGE_SIZE = 15

# --------------------------------------------------
# PAGE LAYOUT
# --------------------------------------------------

layout = dmc.Container(
    [
        create_page_header(
            title="Player Explorer",
            subtitle="Search, filter, and screen 1,692 qualified players across Europe's top 5 leagues with high-dimensional percentile metrics.",
            badge_text="DATABASE COHORT",
        ),

        # COMMAND FILTER TOOLBAR
        create_section_card(
            dmc.Box([
                # Primary Command Row
                dmc.Grid(
                    [
                        dmc.GridCol(
                            dmc.TextInput(
                                id="explorer-search",
                                label="Search Player",
                                placeholder="Filter candidate by name (e.g. Saka, Saliba, Wirtz)...",
                                debounce=300,
                                leftSection=html.Img(
                                    src="/assets/search.svg",
                                    alt="Search",
                                    style={"width": "14px", "height": "14px", "display": "block", "opacity": 0.85},
                                ),
                                leftSectionPointerEvents="none",
                                className="scout-search-input",
                            ),
                            span={"base": 12, "sm": 6, "md": 3.5},
                        ),
                        dmc.GridCol(
                            dmc.Select(
                                id="explorer-pos",
                                label="Position Scope",
                                data=[
                                    {"label": "All Positions", "value": "ALL"},
                                    {"label": "Defenders (DF)", "value": "DF"},
                                    {"label": "Midfielders (MF)", "value": "MF"},
                                    {"label": "Forwards (FW)", "value": "FW"},
                                ],
                                value="ALL",
                                allowDeselect=False,
                            ),
                            span={"base": 12, "sm": 6, "md": 2},
                        ),
                        dmc.GridCol(
                            dmc.Select(
                                id="explorer-subrole",
                                label="Tactical Sub-Role",
                                data=[{"label": "All Sub-Roles", "value": "ALL"}] + [
                                    {"label": s, "value": s} for s in unique_subroles
                                ],
                                value="ALL",
                                searchable=True,
                                allowDeselect=False,
                            ),
                            span={"base": 12, "sm": 6, "md": 2.5},
                        ),
                        dmc.GridCol(
                            dmc.Select(
                                id="explorer-comp",
                                label="Competition / League",
                                data=[{"label": "All 5 Leagues", "value": "ALL"}] + [
                                    {"label": c, "value": c} for c in unique_competitions
                                ],
                                value="ALL",
                                searchable=True,
                                allowDeselect=False,
                            ),
                            span={"base": 12, "sm": 6, "md": 2},
                        ),
                        dmc.GridCol(
                            dmc.Select(
                                id="explorer-age-preset",
                                label="Age Bracket",
                                data=[
                                    {"label": "All Ages", "value": "ALL"},
                                    {"label": "U-21 Prospects (≤21)", "value": "U21"},
                                    {"label": "U-23 Emerging (≤23)", "value": "U23"},
                                    {"label": "Prime Peak (24–29)", "value": "PRIME"},
                                    {"label": "Experienced (30+)", "value": "30PLUS"},
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

                # Progressive Disclosure: Secondary & Compound Filters Accordion (Layer 2)
                dmc.Accordion(
                    value="advanced",
                    children=[
                        dmc.AccordionItem(
                            [
                                dmc.AccordionControl(
                                    dmc.Group(
                                        [
                                            dmc.Group(
                                                [
                                                    dmc.Text("ADVANCED SCREENING & DUAL THRESHOLDS", size="11px", fw=700, c="var(--scout-text-primary)", style={"letterSpacing": "0.6px"}),
                                                    dmc.Badge("8 PARAMETERS", size="xs", variant="light", color="teal"),
                                                ],
                                                gap="xs",
                                            ),
                                            dmc.Text("Club, Nationality, Sort Metric, Min Minutes & Compound Dual-Threshold Filters", size="xs", c="var(--scout-text-muted)"),
                                        ],
                                        justify="space-between",
                                        w="100%",
                                    )
                                ),
                                dmc.AccordionPanel(
                                    dmc.Box([
                                        dmc.Divider(my="xs", color="var(--scout-border-subtle)"),
                                        # Secondary Sorting & Screening Row
                                        dmc.Grid(
                                            [
                                                dmc.GridCol(
                                                    dmc.Select(
                                                        id="explorer-sort-attr",
                                                        label="Sort Metric",
                                                        data=[
                                                            {"label": f"{name} (Percentile)", "value": col}
                                                            for name, col in ATTRIBUTE_COLUMNS.items()
                                                        ] + [
                                                            {"label": "Finishing Diff (G - xG)", "value": "G-xG"},
                                                            {"label": "Shot Quality (npxG/Sh)", "value": "npxG/Sh"},
                                                            {"label": "Minutes Played", "value": "Min"},
                                                            {"label": "Goals", "value": "Gls"},
                                                            {"label": "Assists", "value": "Ast"},
                                                            {"label": "Expected Goals (xG)", "value": "xG"},
                                                            {"label": "pAdj Defending Actions", "value": "Tkl_pAdj_per90"},
                                                            {"label": "Age", "value": "Age"},
                                                        ],
                                                        value="Finishing_Score",
                                                        searchable=True,
                                                        allowDeselect=False,
                                                    ),
                                                    span={"base": 12, "sm": 6, "md": 3},
                                                ),
                                                dmc.GridCol(
                                                    dmc.Select(
                                                        id="explorer-sort-order",
                                                        label="Order",
                                                        data=[
                                                            {"label": "Highest First (Desc)", "value": "desc"},
                                                            {"label": "Lowest First (Asc)", "value": "asc"},
                                                        ],
                                                        value="desc",
                                                        allowDeselect=False,
                                                    ),
                                                    span={"base": 12, "sm": 6, "md": 2},
                                                ),
                                                dmc.GridCol(
                                                    dmc.Select(
                                                        id="explorer-squad",
                                                        label="Club / Squad",
                                                        data=[{"label": "All Clubs", "value": "ALL"}] + [
                                                            {"label": s, "value": s} for s in unique_squads
                                                        ],
                                                        value="ALL",
                                                        searchable=True,
                                                        allowDeselect=False,
                                                    ),
                                                    span={"base": 12, "sm": 6, "md": 3.5},
                                                ),
                                                dmc.GridCol(
                                                    dmc.Select(
                                                        id="explorer-nation",
                                                        label="Nationality",
                                                        data=[{"label": "All Nationalities", "value": "ALL"}] + [
                                                            {"label": n, "value": n} for n in unique_nations
                                                        ],
                                                        value="ALL",
                                                        searchable=True,
                                                        allowDeselect=False,
                                                    ),
                                                    span={"base": 12, "sm": 6, "md": 3.5},
                                                ),
                                            ],
                                            gap="sm",
                                        ),

                                        dmc.Space(h=12),

                                        # Tertiary Threshold Pods: Perfectly Balanced 6 + 6 Symmetry
                                        dmc.Grid(
                                            [
                                                # Pod 1: Sample Volume & Primary Score Benchmark
                                                dmc.GridCol(
                                                    dmc.Box(
                                                        [
                                                            dmc.Group([
                                                                dmc.Text("SAMPLE VOLUME & PRIMARY BENCHMARK", size="10.5px", fw=700, c="var(--scout-text-secondary)", style={"letterSpacing": "0.5px"}),
                                                                dmc.Badge("VOLUME", size="xs", variant="outline", color="teal"),
                                                            ], justify="space-between", mb="xs"),
                                                            dmc.Grid([
                                                                dmc.GridCol(
                                                                    dmc.Box([
                                                                        dmc.Text("MINIMUM MINUTES", size="10px", fw=600, c="var(--scout-text-muted)", style={"letterSpacing": "0.5px"}, mb=4),
                                                                        dmc.Slider(
                                                                            id="explorer-min-minutes",
                                                                            min=600,
                                                                            max=3000,
                                                                            step=100,
                                                                            value=600,
                                                                            marks=[
                                                                                {"value": 600, "label": "600m"},
                                                                                {"value": 1500, "label": "1500m"},
                                                                                {"value": 2500, "label": "2500m"},
                                                                            ],
                                                                            color="teal",
                                                                            size="xs",
                                                                        ),
                                                                    ]),
                                                                    span={"base": 12, "sm": 6},
                                                                ),
                                                                dmc.GridCol(
                                                                    dmc.Box([
                                                                        dmc.Text("MIN PRIMARY SCORE", size="10px", fw=600, c="var(--scout-text-muted)", style={"letterSpacing": "0.5px"}, mb=4),
                                                                        dmc.Slider(
                                                                            id="explorer-min-score",
                                                                            min=0,
                                                                            max=90,
                                                                            step=5,
                                                                            value=0,
                                                                            marks=[
                                                                                {"value": 0, "label": "0"},
                                                                                {"value": 50, "label": "50"},
                                                                                {"value": 80, "label": "80"},
                                                                            ],
                                                                            color="teal",
                                                                            size="xs",
                                                                        ),
                                                                    ]),
                                                                    span={"base": 12, "sm": 6},
                                                                ),
                                                            ], gap="sm"),
                                                        ],
                                                        style={
                                                            "backgroundColor": "var(--scout-surface-secondary)",
                                                            "border": "1px solid var(--scout-border)",
                                                            "borderRadius": "6px",
                                                            "padding": "12px 14px",
                                                        },
                                                    ),
                                                    span={"base": 12, "md": 6},
                                                ),

                                                # Pod 2: Compound Secondary Attribute & Score Benchmark
                                                dmc.GridCol(
                                                    dmc.Box(
                                                        [
                                                            dmc.Group([
                                                                dmc.Text("COMPOUND SECONDARY ATTRIBUTE", size="10.5px", fw=700, c="var(--scout-text-secondary)", style={"letterSpacing": "0.5px"}),
                                                                dmc.Badge("DUAL SCREEN", size="xs", variant="outline", color="cyan"),
                                                            ], justify="space-between", mb="xs"),
                                                            dmc.Grid([
                                                                dmc.GridCol(
                                                                    dmc.Select(
                                                                        id="explorer-sec-attr",
                                                                        label="Secondary Attribute",
                                                                        data=[{"label": "None (No Secondary Filter)", "value": "NONE"}] + [
                                                                            {"label": name, "value": col}
                                                                            for name, col in ATTRIBUTE_COLUMNS.items()
                                                                        ],
                                                                        value="NONE",
                                                                        searchable=True,
                                                                        allowDeselect=False,
                                                                    ),
                                                                    span={"base": 12, "sm": 6},
                                                                ),
                                                                dmc.GridCol(
                                                                    dmc.Box([
                                                                        dmc.Text("MIN SECONDARY SCORE", size="10px", fw=600, c="var(--scout-text-muted)", style={"letterSpacing": "0.5px"}, mb=4),
                                                                        dmc.Slider(
                                                                            id="explorer-sec-score",
                                                                            min=0,
                                                                            max=90,
                                                                            step=5,
                                                                            value=0,
                                                                            marks=[
                                                                                {"value": 0, "label": "0"},
                                                                                {"value": 50, "label": "50"},
                                                                                {"value": 80, "label": "80"},
                                                                            ],
                                                                            color="teal",
                                                                            size="xs",
                                                                        ),
                                                                    ]),
                                                                    span={"base": 12, "sm": 6},
                                                                ),
                                                            ], gap="sm", align="flex-end"),
                                                        ],
                                                        style={
                                                            "backgroundColor": "var(--scout-surface-secondary)",
                                                            "border": "1px solid var(--scout-border)",
                                                            "borderRadius": "6px",
                                                            "padding": "12px 14px",
                                                        },
                                                    ),
                                                    span={"base": 12, "md": 6},
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
            title="Recruitment Cohort Screening",
            subtitle="Filter and screen 1,692 qualified candidates across tactical sub-roles, leagues, and compound statistical thresholds",
            extra_header=dmc.Badge("COHORT SCREENING", color="teal", variant="light", size="xs"),
        ),

        dmc.Space(h=15),

        # RESULTS STATS & DATA GRID
        dmc.Card(
            [
                dmc.Group(
                    [
                        dmc.Group([
                            dmc.Text(id="explorer-count-label", size="xs", fw=600, c="var(--scout-text-primary)"),
                        ], gap=6, align="center"),
                        dmc.Group([
                            dmc.SegmentedControl(
                                id="explorer-view-mode",
                                data=[
                                    {"label": "Recruitment (6 Col)", "value": "scout"},
                                    {"label": "7D Attribute Matrix (14 Col)", "value": "analyst"},
                                ],
                                value="scout",
                                size="xs",
                                color="teal",
                                persistence=True,
                                persistence_type="local",
                                style={"fontWeight": 600},
                            ),
                            dmc.Pagination(
                                id="explorer-pagination",
                                total=1,
                                value=1,
                                color="teal",
                                size="xs",
                            ),
                        ], gap="sm", align="center"),
                    ],
                    justify="space-between",
                    align="center",
                    mb="sm",
                ),

                html.Div(
                    id="explorer-table-container",
                    style={"overflowX": "auto"},
                ),

                dmc.Space(h=15),

                # Bottom Pagination
                dmc.Group(
                    [
                        dmc.Text("Showing 15 candidate profiles per page", size="11px", c="var(--scout-text-muted)"),
                        dmc.Pagination(
                            id="explorer-pagination-bottom",
                            total=1,
                            value=1,
                            color="teal",
                            size="xs",
                        ),
                    ],
                    justify="space-between",
                    align="center",
                ),
            ],
            withBorder=True,
            radius="md",
            p="md",
            style={"backgroundColor": "var(--scout-surface-primary)", "borderColor": "var(--scout-border)"},
        ),
    ],
    fluid=True,
    p=0,
)


# --------------------------------------------------
# CALLBACKS
# --------------------------------------------------

# Sync top and bottom paginations bidirectionally
@callback(
    Output("explorer-pagination-bottom", "value"),
    Output("explorer-pagination-bottom", "total"),
    Input("explorer-pagination", "value"),
    Input("explorer-pagination", "total"),
)
def sync_bottom_pagination(val, total):
    return val or 1, total or 1


@callback(
    Output("explorer-pagination", "value", allow_duplicate=True),
    Input("explorer-pagination-bottom", "value"),
    prevent_initial_call=True,
)
def sync_from_bottom(bottom_val):
    if bottom_val is not None:
        return bottom_val
    return dash.no_update


@callback(
    Output("explorer-table-container", "children"),
    Output("explorer-count-label", "children"),
    Output("explorer-pagination", "total"),
    Input("explorer-search", "value"),
    Input("explorer-pos", "value"),
    Input("explorer-subrole", "value"),
    Input("explorer-comp", "value"),
    Input("explorer-squad", "value"),
    Input("explorer-nation", "value"),
    Input("explorer-age-preset", "value"),
    Input("explorer-sort-attr", "value"),
    Input("explorer-sort-order", "value"),
    Input("explorer-min-minutes", "value"),
    Input("explorer-min-score", "value"),
    Input("explorer-sec-attr", "value"),
    Input("explorer-sec-score", "value"),
    Input("explorer-pagination", "value"),
    Input("explorer-view-mode", "value"),
)
def update_explorer_table(search, pos, subrole, comp, squad, nation, age_preset, sort_attr, sort_order, min_min, min_score, sec_attr, sec_score, page, local_view_mode="scout", **kwargs):
    effective_mode = "analyst" if (local_view_mode == "analyst" or kwargs.get("scout_analyst_mode") == "analyst") else "scout"
    filtered = df.copy()

    # Search filter
    if search and str(search).strip():
        query = str(search).strip().lower()
        filtered = filtered[filtered["Player"].str.lower().str.contains(query, na=False)]

    # Position filter
    if pos and pos != "ALL":
        filtered = filtered[filtered["Pos"] == pos]

    # Tactical Sub-Role filter
    if subrole and subrole != "ALL" and "SubRole" in filtered.columns:
        filtered = filtered[filtered["SubRole"] == subrole]

    # Competition / League filter
    if comp and comp != "ALL":
        filtered = filtered[filtered["Comp_Clean"].apply(lambda c: comp in [x.strip() for x in str(c).split(",")])]

    # Squad filter
    if squad and squad != "ALL":
        filtered = filtered[filtered["Squad"].apply(lambda s: squad in [c.strip() for c in str(s).split(",")])]

    # Nation filter
    if nation and nation != "ALL":
        filtered = filtered[filtered["Nation_Clean"] == nation]

    # Age Bracket filter
    if age_preset and age_preset != "ALL":
        if age_preset == "U21":
            filtered = filtered[(filtered["Age"] > 0) & (filtered["Age"] <= 21)]
        elif age_preset == "U23":
            filtered = filtered[(filtered["Age"] > 0) & (filtered["Age"] <= 23)]
        elif age_preset == "PRIME":
            filtered = filtered[(filtered["Age"] >= 24) & (filtered["Age"] <= 29)]
        elif age_preset == "30PLUS":
            filtered = filtered[filtered["Age"] >= 30]

    # Minutes filter
    if min_min and min_min > 600:
        filtered = filtered[filtered["Min"] >= min_min]

    # Minimum attribute score filter
    if min_score and min_score > 0 and sort_attr in filtered.columns:
        filtered = filtered[filtered[sort_attr] >= min_score]

    # Secondary attribute screening filter
    if sec_attr and sec_attr != "NONE" and sec_score and sec_score > 0 and sec_attr in filtered.columns:
        filtered = filtered[filtered[sec_attr] >= sec_score]

    # Sort
    ascending = (sort_order == "asc")
    if sort_attr and sort_attr in filtered.columns:
        filtered = filtered.sort_values(sort_attr, ascending=ascending)

    total_matching = len(filtered)
    total_pages = max(1, int(np.ceil(total_matching / PAGE_SIZE)))

    if page is None or page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    start_idx = (page - 1) * PAGE_SIZE
    end_idx = min(start_idx + PAGE_SIZE, total_matching)

    page_df = filtered.iloc[start_idx:end_idx]

    if total_matching == 0:
        count_text = "No candidates match the selected criteria."
    else:
        count_text = f"Showing {start_idx + 1}–{end_idx} of {total_matching} matching players"

    sort_arrow = " ▲" if ascending else " ▼"

    def col_header(label, col_key, align="left"):
        is_active = (sort_attr == col_key)
        th_label = f"{label}{sort_arrow}" if is_active else label
        th_style = {
            "color": "#10B981" if is_active else TEXT,
            "fontSize": "10px",
            "letterSpacing": "0.6px",
            "fontWeight": "700" if is_active else "600",
        }
        if align != "left":
            th_style["textAlign"] = align
        return dmc.TableTh(th_label, style=th_style)

    # SCOUT VIEW: Streamlined, high-signal recruitment table
    if effective_mode == "scout":
        mins_label = f"MINUTES{sort_arrow}" if sort_attr == "Min" else "MINUTES"
        ga_label = f"G+A{sort_arrow}" if sort_attr in ["Gls", "Ast", "G-xG"] else "G+A"
        asset_label = f"PRIMARY SCOUTING ASSET{sort_arrow}" if "Score" in str(sort_attr) else "PRIMARY SCOUTING ASSET"
        thead = dmc.TableThead(
            dmc.TableTr([
                dmc.TableTh("CANDIDATE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
                dmc.TableTh("SQUAD / LEAGUE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
                dmc.TableTh("ROLE & STYLE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
                dmc.TableTh(mins_label, style={"color": "#10B981" if sort_attr == "Min" else TEXT, "fontWeight": "700" if sort_attr == "Min" else "600", "fontSize": "10px", "letterSpacing": "0.6px"}),
                dmc.TableTh(ga_label, style={"color": "#10B981" if sort_attr in ["Gls", "Ast", "G-xG"] else TEXT, "fontWeight": "700" if sort_attr in ["Gls", "Ast", "G-xG"] else "600", "fontSize": "10px", "letterSpacing": "0.6px", "textAlign": "center"}),
                dmc.TableTh(asset_label, style={"color": "#10B981" if "Score" in str(sort_attr) else TEXT, "fontWeight": "700" if "Score" in str(sort_attr) else "600", "fontSize": "10px", "letterSpacing": "0.6px"}),
            ])
        )
        rows = []
        for idx, r in page_df.iterrows():
            pos_badge_color = "blue" if r["Pos"] == "DF" else "teal" if r["Pos"] == "MF" else "orange"
            nat_display = r.get("Nation_Display", r.get("Nation_Clean", "N/A"))
            age_str = str(int(r["Age"])) if r["Age"] > 0 else "—"
            mins = float(r.get("Min", 0))

            gls = int(r.get("Gls", 0)) if pd.notna(r.get("Gls")) else 0
            ast = int(r.get("Ast", 0)) if pd.notna(r.get("Ast")) else 0
            ga = gls + ast
            profile_url = f"/player-profile?player={r['Player_Unique']}"

            sample_pill = dmc.Badge(f"{int(mins)}m (Low)", color="orange", variant="outline", size="xs", style={"fontSize": "8.5px", "height": "14px", "padding": "0 3px"}) if mins < SAMPLE_SIZE_THRESHOLD else None

            scores = {attr: float(r[c]) for attr, c in ATTRIBUTE_COLUMNS.items()}
            top_attr, top_score = max(scores.items(), key=lambda x: x[1])
            tier_info = get_percentile_tier(top_score)

            rows.append(
                dmc.TableTr([
                    dmc.TableTd([
                        dcc.Link(
                            dmc.Group([
                                render_player_portrait(r["Player_Unique"], size=32, radius=4),
                                dmc.Box([
                                    dmc.Group([
                                        dmc.Text(r["Player"], size="xs", fw=700, c="var(--scout-text-primary)", className="scout-candidate-name"),
                                        *([sample_pill] if sample_pill else []),
                                    ], gap=4, align="center"),
                                    dmc.Text(f"{nat_display} • Age {age_str}", size="10px", c="var(--scout-text-muted)"),
                                ]),
                            ], gap="xs", align="center", wrap="nowrap"),
                            href=profile_url,
                            style={"textDecoration": "none", "color": "inherit"},
                            className="scout-player-link",
                        ),
                    ]),
                    dmc.TableTd([
                        dmc.Text(r["Squad"], size="xs", fw=500, c="var(--scout-text-primary)"),
                        dmc.Text(r.get("Comp_Clean", ""), size="10px", c="var(--scout-text-muted)"),
                    ]),
                    dmc.TableTd([
                        dmc.Badge(r.get("SubRole", r["Pos"]), color=pos_badge_color, variant="light", size="xs"),
                        dmc.Text(r.get("PlayingStyle_Name", "Specialist"), size="10px", c="var(--scout-text-secondary)", mt=2),
                    ]),
                    dmc.TableTd(dmc.Text(f"{int(mins):,}m", size="xs", c="var(--scout-text-muted)", style={"fontVariantNumeric": "tabular-nums"})),
                    dmc.TableTd(dmc.Text(str(ga), size="xs", fw=600, c="var(--scout-text-primary)", style={"fontVariantNumeric": "tabular-nums", "textAlign": "center"})),
                    dmc.TableTd(
                        dmc.Badge(
                            f"{top_attr} ({top_score:.1f}th pct)",
                            color=tier_info["badge_color"],
                            variant="light",
                            size="xs",
                        )
                    ),
                ])
            )
        if total_matching == 0:
            rows = [
                dmc.TableTr([
                    dmc.TableTd(
                        dmc.Box([
                            dmc.Text("No candidates matched your exact screening criteria.", size="xs", fw=600, c="var(--scout-text-primary)"),
                            dmc.Text("Try lowering the minimum minutes threshold or adjusting score sliders.", size="11px", c="var(--scout-text-muted)", mt=2),
                        ], style={"textAlign": "center", "padding": "28px 12px"}),
                        colSpan=6,
                    )
                ])
            ]
        tbody = dmc.TableTbody(rows)
        table = dmc.Table(
            [thead, tbody],
            striped=False,
            highlightOnHover=True,
            withTableBorder=False,
            withColumnBorders=False,
            style={"fontSize": "12.5px"},
        )
        return table, count_text, total_pages

    # ANALYST VIEW: Full 14-column multi-attribute grid
    thead = dmc.TableThead(
        dmc.TableTr([
            dmc.TableTh("CANDIDATE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh("SQUAD / LEAGUE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh("ROLE", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            dmc.TableTh("NAT", style={"color": TEXT, "fontSize": "10px", "letterSpacing": "0.6px"}),
            col_header("AGE", "Age"),
            col_header("MINUTES", "Min"),
            col_header("G+A", sort_attr if sort_attr in ["Gls", "Ast", "G-xG"] else "G+A"),
            col_header("FIN", "Finishing_Score", align="right"),
            col_header("CRE", "Creativity_Score", align="right"),
            col_header("PAS", "Passing_Score", align="right"),
            col_header("PRG", "Progression_Score", align="right"),
            col_header("DEF", "Defending_Score", align="right"),
            col_header("SEC", "BallSecurity_Score", align="right"),
            col_header("AER", "Aerial_Score", align="right"),
        ])
    )

    rows = []
    for idx, r in page_df.iterrows():
        pos_badge_color = "blue" if r["Pos"] == "DF" else "teal" if r["Pos"] == "MF" else "orange"
        nat_display = r.get("Nation_Display", r.get("Nation_Clean", "N/A"))
        age_str = str(int(r["Age"])) if r["Age"] > 0 else "—"
        mins = float(r.get("Min", 0))

        gls = int(r.get("Gls", 0)) if pd.notna(r.get("Gls")) else 0
        ast = int(r.get("Ast", 0)) if pd.notna(r.get("Ast")) else 0
        ga = gls + ast
        profile_url = f"/player-profile?player={r['Player_Unique']}"

        sample_pill = dmc.Badge(f"{int(mins)}m (Low)", color="orange", variant="outline", size="xs", style={"fontSize": "8.5px", "height": "14px", "padding": "0 3px"}) if mins < SAMPLE_SIZE_THRESHOLD else None

        def render_score(score_val):
            tier_info = get_percentile_tier(score_val)
            return dmc.TableTd(
                dmc.Text(
                    f"{score_val:.1f}",
                    size="xs",
                    fw=600,
                    style={"color": tier_info["color"], "fontVariantNumeric": "tabular-nums", "textAlign": "right"},
                )
            )

        rows.append(
            dmc.TableTr([
                dmc.TableTd([
                    dcc.Link(
                        dmc.Group([
                            render_player_portrait(r["Player_Unique"], size=32, radius=4),
                            dmc.Group([
                                dmc.Text(r["Player"], size="xs", fw=700, c="var(--scout-text-primary)", className="scout-candidate-name"),
                                *([sample_pill] if sample_pill else []),
                            ], gap=4, align="center"),
                        ], gap="xs", align="center", wrap="nowrap"),
                        href=profile_url,
                        style={"textDecoration": "none", "color": "inherit"},
                        className="scout-player-link",
                    ),
                ]),
                dmc.TableTd([
                    dmc.Text(r["Squad"], size="xs", fw=500, c="var(--scout-text-primary)"),
                    dmc.Text(r.get("Comp_Clean", ""), size="10px", c="var(--scout-text-muted)"),
                ]),
                dmc.TableTd([
                    dmc.Badge(r["Pos"], color=pos_badge_color, variant="light", size="xs"),
                    dmc.Text(r.get("SubRole", ""), size="10px", c="var(--scout-text-muted)", mt=2),
                ]),
                dmc.TableTd(dmc.Text(nat_display, size="xs", c="var(--scout-text-primary)")),
                dmc.TableTd(dmc.Text(age_str, size="xs", c="var(--scout-text-primary)", style={"fontVariantNumeric": "tabular-nums"})),
                dmc.TableTd(dmc.Text(f"{r['Min']:,}", size="xs", c="var(--scout-text-muted)", style={"fontVariantNumeric": "tabular-nums"})),
                dmc.TableTd(dmc.Text(str(ga), size="xs", fw=600, c="var(--scout-text-primary)", style={"fontVariantNumeric": "tabular-nums"})),

                render_score(r['Finishing_Score']),
                render_score(r['Creativity_Score']),
                render_score(r['Passing_Score']),
                render_score(r['Progression_Score']),
                render_score(r['Defending_Score']),
                render_score(r['BallSecurity_Score']),
                render_score(r['Aerial_Score']),
            ])
        )

    if total_matching == 0:
        rows = [
            dmc.TableTr([
                dmc.TableTd(
                    dmc.Box([
                        dmc.Text("No candidates matched your exact screening criteria.", size="xs", fw=600, c="var(--scout-text-primary)"),
                        dmc.Text("Try lowering the minimum minutes threshold or adjusting score sliders.", size="11px", c="var(--scout-text-muted)", mt=2),
                    ], style={"textAlign": "center", "padding": "28px 12px"}),
                    colSpan=14,
                )
            ])
        ]

    tbody = dmc.TableTbody(rows)

    table = dmc.Table(
        [thead, tbody],
        striped=False,
        highlightOnHover=True,
        withTableBorder=False,
        withColumnBorders=False,
        style={
            "fontSize": "12.5px",
        },
    )

    return table, count_text, total_pages
