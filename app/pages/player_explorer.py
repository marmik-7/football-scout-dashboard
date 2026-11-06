import dash
from dash import html, dcc, Input, Output, State, callback
import dash_mantine_components as dmc
import pandas as pd
import numpy as np

from app.utils.data_loader import load_data, get_unique_squads, get_unique_nations
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
)

dash.register_page(__name__, path="/player-explorer", name="Player Explorer", order=2)

df = load_data()
unique_squads = get_unique_squads()
unique_nations = get_unique_nations()

PAGE_SIZE = 15

# --------------------------------------------------
# PAGE LAYOUT
# --------------------------------------------------

layout = dmc.Container(
    [
        create_page_header(
            title="Player Explorer",
            subtitle="Search, filter, and discover players across Europe's top leagues with comprehensive percentile evaluations.",
            badge_text="DATABASE: 1,692 PLAYERS",
        ),

        # FILTER CONTROLS PANEL
        create_section_card(
            [
                dmc.Grid(
                    [
                        dmc.GridCol(
                            dmc.TextInput(
                                id="explorer-search",
                                label="Search Player",
                                placeholder="Type player name...",
                                leftSection="🔍",
                                debounce=300,
                            ),
                            span={"base": 12, "sm": 6, "md": 3},
                        ),
                        dmc.GridCol(
                            dmc.Select(
                                id="explorer-pos",
                                label="Position Group",
                                data=[
                                    {"label": "All Positions", "value": "ALL"},
                                    {"label": "Defenders (DF)", "value": "DF"},
                                    {"label": "Midfielders (MF)", "value": "MF"},
                                    {"label": "Forwards (FW)", "value": "FW"},
                                ],
                                value="ALL",
                                allowDeselect=False,
                            ),
                            span={"base": 12, "sm": 6, "md": 3},
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
                            span={"base": 12, "sm": 6, "md": 3},
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
                            span={"base": 12, "sm": 6, "md": 3},
                        ),
                    ],
                    gap="md",
                ),

                dmc.Space(h=15),

                dmc.Grid(
                    [
                        dmc.GridCol(
                            dmc.Select(
                                id="explorer-sort-attr",
                                label="Rank / Sort By",
                                data=[
                                    {"label": name, "value": col}
                                    for name, col in ATTRIBUTE_COLUMNS.items()
                                ] + [
                                    {"label": "Minutes Played", "value": "Min"},
                                    {"label": "Goals", "value": "Gls"},
                                    {"label": "Assists", "value": "Ast"},
                                    {"label": "Expected Goals (xG)", "value": "xG"},
                                    {"label": "Age", "value": "Age"},
                                ],
                                value="Finishing_Score",
                                allowDeselect=False,
                            ),
                            span={"base": 12, "sm": 6, "md": 3},
                        ),
                        dmc.GridCol(
                            dmc.Select(
                                id="explorer-sort-order",
                                label="Order",
                                data=[
                                    {"label": "Highest to Lowest (Desc)", "value": "desc"},
                                    {"label": "Lowest to Highest (Asc)", "value": "asc"},
                                ],
                                value="desc",
                                allowDeselect=False,
                            ),
                            span={"base": 12, "sm": 6, "md": 3},
                        ),
                        dmc.GridCol(
                            dmc.Box([
                                dmc.Text("Minimum Minutes", size="xs", fw=500, c="dimmed", mb=4),
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
                                    color="lime",
                                ),
                            ]),
                            span={"base": 12, "sm": 6, "md": 3},
                        ),
                        dmc.GridCol(
                            dmc.Box([
                                dmc.Text("Min Score for Sorted Attribute", size="xs", fw=500, c="dimmed", mb=4),
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
                                    color="lime",
                                ),
                            ]),
                            span={"base": 12, "sm": 6, "md": 3},
                        ),
                    ],
                    gap="md",
                ),
            ],
            title="Database Filters & Search",
            subtitle="Combine text search with positional, club, and attribute thresholds",
        ),

        dmc.Space(h=20),

        # RESULTS STATS & TABLE
        create_section_card(
            [
                dmc.Group(
                    [
                        dmc.Text(id="explorer-count-label", size="sm", fw=600, c="lime"),
                        dmc.Pagination(
                            id="explorer-pagination",
                            total=1,
                            value=1,
                            color="lime",
                            size="sm",
                        ),
                    ],
                    justify="space-between",
                    align="center",
                    mb="md",
                ),

                html.Div(
                    id="explorer-table-container",
                    style={"overflowX": "auto"},
                ),

                dmc.Space(h=15),

                dmc.Group(
                    [
                        dmc.Text("Click any player's 'View Profile' button to open their analytical profile card.", size="xs", c="dimmed"),
                        dmc.Pagination(
                            id="explorer-pagination-bottom",
                            total=1,
                            value=1,
                            color="lime",
                            size="sm",
                        ),
                    ],
                    justify="space-between",
                    align="center",
                ),
            ],
            title="Player Roster",
            subtitle="Detailed player records with 7 core percentile scores and match statistics",
        ),
    ],
    fluid=True,
    p=0,
)


# --------------------------------------------------
# CALLBACKS
# --------------------------------------------------

# Sync top and bottom paginations
@callback(
    Output("explorer-pagination-bottom", "value"),
    Output("explorer-pagination-bottom", "total"),
    Input("explorer-pagination", "value"),
    Input("explorer-pagination", "total"),
)
def sync_bottom_pagination(val, total):
    return val, total


@callback(
    Output("explorer-table-container", "children"),
    Output("explorer-count-label", "children"),
    Output("explorer-pagination", "total"),
    Input("explorer-search", "value"),
    Input("explorer-pos", "value"),
    Input("explorer-squad", "value"),
    Input("explorer-nation", "value"),
    Input("explorer-sort-attr", "value"),
    Input("explorer-sort-order", "value"),
    Input("explorer-min-minutes", "value"),
    Input("explorer-min-score", "value"),
    Input("explorer-pagination", "value"),
)
def update_explorer_table(search, pos, squad, nation, sort_attr, sort_order, min_min, min_score, page):
    filtered = df.copy()

    # Search filter
    if search and str(search).strip():
        query = str(search).strip().lower()
        filtered = filtered[filtered["Player"].str.lower().str.contains(query, na=False)]

    # Position filter
    if pos and pos != "ALL":
        filtered = filtered[filtered["Pos"] == pos]

    # Squad filter
    if squad and squad != "ALL":
        filtered = filtered[filtered["Squad"] == squad]

    # Nation filter
    if nation and nation != "ALL":
        filtered = filtered[filtered["Nation_Clean"] == nation]

    # Minutes filter
    if min_min and min_min > 600:
        filtered = filtered[filtered["Min"] >= min_min]

    # Minimum attribute score filter (if sorting by an engineered score)
    if min_score and min_score > 0 and sort_attr in filtered.columns:
        filtered = filtered[filtered[sort_attr] >= min_score]

    total_matches = len(filtered)
    total_pages = max(1, int(np.ceil(total_matches / PAGE_SIZE)))

    if page is None or page > total_pages:
        page = 1

    # Sorting
    if sort_attr in filtered.columns:
        ascending = (sort_order == "asc")
        filtered = filtered.sort_values(sort_attr, ascending=ascending)

    start_idx = (page - 1) * PAGE_SIZE
    end_idx = min(start_idx + PAGE_SIZE, total_matches)
    page_df = filtered.iloc[start_idx:end_idx]

    count_text = f"Showing {start_idx + 1}–{end_idx} of {total_matches:,} matching players"

    if page_df.empty:
        empty_msg = dmc.Alert(
            "No players match the current filter criteria. Try adjusting your search query or threshold sliders.",
            title="No Results Found",
            color="yellow",
            variant="light",
        )
        return empty_msg, "0 players found", 1

    # Table Header
    thead = dmc.TableThead(
        dmc.TableTr([
            dmc.TableTh("Player", style={"color": TEXT}),
            dmc.TableTh("Club", style={"color": TEXT}),
            dmc.TableTh("Pos", style={"color": TEXT}),
            dmc.TableTh("Nat", style={"color": TEXT}),
            dmc.TableTh("Min", style={"color": TEXT}),
            dmc.TableTh("G+A", style={"color": TEXT}),
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

    # Function to color badge or text by score
    def score_color(val):
        if val >= 80:
            return "#84CC16"  # Lime
        if val >= 60:
            return "#38BDF8"  # Cyan
        if val >= 40:
            return "#94A3B8"  # Muted
        return "#F59E0B"      # Amber

    # Table Rows
    rows = []
    for _, r in page_df.iterrows():
        pos_badge_color = "blue" if r["Pos"] == "DF" else "lime" if r["Pos"] == "MF" else "orange"
        ga = int(r.get("Gls", 0) + r.get("Ast", 0))

        # View profile link passing query parameter
        profile_url = f"/player-profile?player={r['Player_Unique']}"

        rows.append(
            dmc.TableTr([
                dmc.TableTd(
                    dmc.Text(r["Player"], size="sm", fw=600, c="white")
                ),
                dmc.TableTd(dmc.Text(r["Squad"], size="xs", c="dimmed")),
                dmc.TableTd(dmc.Badge(r["Pos"], color=pos_badge_color, variant="light", size="xs")),
                dmc.TableTd(dmc.Text(r["Nation_Clean"], size="xs", c="dimmed")),
                dmc.TableTd(dmc.Text(f"{r['Min']:,}", size="xs", c="dimmed")),
                dmc.TableTd(dmc.Text(str(ga), size="xs", fw=600, c="white")),

                dmc.TableTd(dmc.Text(f"{r['Finishing_Score']:.1f}", size="xs", fw=600, style={"color": score_color(r['Finishing_Score'])})),
                dmc.TableTd(dmc.Text(f"{r['Creativity_Score']:.1f}", size="xs", fw=600, style={"color": score_color(r['Creativity_Score'])})),
                dmc.TableTd(dmc.Text(f"{r['Passing_Score']:.1f}", size="xs", fw=600, style={"color": score_color(r['Passing_Score'])})),
                dmc.TableTd(dmc.Text(f"{r['Progression_Score']:.1f}", size="xs", fw=600, style={"color": score_color(r['Progression_Score'])})),
                dmc.TableTd(dmc.Text(f"{r['Defending_Score']:.1f}", size="xs", fw=600, style={"color": score_color(r['Defending_Score'])})),
                dmc.TableTd(dmc.Text(f"{r['BallSecurity_Score']:.1f}", size="xs", fw=600, style={"color": score_color(r['BallSecurity_Score'])})),
                dmc.TableTd(dmc.Text(f"{r['Aerial_Score']:.1f}", size="xs", fw=600, style={"color": score_color(r['Aerial_Score'])})),

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
        withColumnBorders=False,
        style={
            "backgroundColor": PANEL,
            "fontSize": "13px",
            "borderColor": BORDER,
        },
    )

    return table, count_text, total_pages
