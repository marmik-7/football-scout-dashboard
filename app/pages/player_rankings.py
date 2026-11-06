import dash
from dash import html, dcc, Input, Output, callback
import dash_mantine_components as dmc
import plotly.graph_objects as go
import pandas as pd

from app.utils.data_loader import (
    load_data,
    get_unique_squads,
    get_unique_nations,
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
    style_figure,
)

dash.register_page(__name__, path="/player-rankings", name="Rankings", order=7)

df = load_data()
unique_squads = get_unique_squads()
unique_nations = get_unique_nations()


# --------------------------------------------------
# PAGE LAYOUT
# --------------------------------------------------

layout = dmc.Container(
    [
        create_page_header(
            title="Player Rankings & Leaderboards",
            subtitle="Explore high-volume percentile rankings and category leaders across all 7 scouting dimensions and position groups.",
            badge_text="GLOBAL LEADERBOARDS",
        ),

        # FILTER AND RANKING CONTROLS
        create_section_card(
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
                        span={"base": 12, "sm": 6, "md": 3},
                    ),
                    dmc.GridCol(
                        dmc.Select(
                            id="rankings-attr",
                            label="Target Scouting Attribute",
                            data=[
                                {"label": name, "value": name}
                                for name in ATTRIBUTE_COLUMNS
                            ],
                            value="Finishing",
                            allowDeselect=False,
                        ),
                        span={"base": 12, "sm": 6, "md": 3},
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
                        span={"base": 12, "sm": 6, "md": 2},
                    ),
                    dmc.GridCol(
                        dmc.Select(
                            id="rankings-order",
                            label="Sort Direction",
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
                            id="rankings-squad",
                            label="Club / Squad",
                            data=[{"label": "All Clubs", "value": "ALL"}] + [
                                {"label": s, "value": s} for s in unique_squads
                            ],
                            value="ALL",
                            searchable=True,
                            allowDeselect=False,
                        ),
                        span={"base": 12, "sm": 6, "md": 2},
                    ),
                ],
                gap="md",
            ),
            title="Leaderboard Filters",
            subtitle="Select the ranking dimension, positional scope, and candidate sample depth",
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
            subtitle="Percentile score distribution of top-ranked players",
        ),

        dmc.Space(h=25),

        # LEADERBOARD TABLE
        create_section_card(
            html.Div(id="rankings-table-container", style={"overflowX": "auto"}),
            title="Complete Leaderboard Matrix",
            subtitle="Official rank numbers, candidate records, and full 7-attribute profile",
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
    Input("rankings-attr", "value"),
    Input("rankings-depth", "value"),
    Input("rankings-order", "value"),
    Input("rankings-squad", "value"),
)
def update_rankings(pos, attr, depth, order, squad):
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
            radius="md",
            p="sm",
            style={
                "backgroundColor": "rgba(245, 158, 11, 0.08)",
                "borderColor": "rgba(245, 158, 11, 0.25)",
                "color": "#F8FAFC",
            },
        )
        pos_display = "Players (All Positions)"
    else:
        pos_display = POSITION_NAMES.get(pos, pos)
        notice = dmc.Text(
            f"Rankings benchmarked strictly among {pos_display.lower()} with ≥600 minutes. Scores span 0 to 100 percentile.",
            size="xs",
            c="dimmed",
        )

    # 2. Filter dataset
    filtered = df.copy()
    if pos != "ALL":
        filtered = filtered[filtered["Pos"] == pos]

    if squad and squad != "ALL":
        filtered = filtered[filtered["Squad"] == squad]

    if filtered.empty:
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="No players found matching the filter criteria.",
            showarrow=False,
            font=dict(color=MUTED, size=14),
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

    # For horizontal bar chart, sort ascending so rank #1 is at the top of the chart!
    chart_candidates = top_candidates.sort_values(col, ascending=(not ascending)).copy()

    # 4. Ranked Bar Chart
    chart_height = max(420, min(850, len(chart_candidates) * 28 + 120))
    chart_title = f"Top {len(chart_candidates)} {pos_display} — {attr}"

    fig = go.Figure(
        go.Bar(
            x=chart_candidates[col],
            y=chart_candidates["Player_Unique"],
            orientation="h",
            marker=dict(color=ACCENT),
            text=chart_candidates[col].apply(lambda v: f"{v:.1f}"),
            textposition="outside",
            cliponaxis=False,
            customdata=chart_candidates[["Player", "Squad", "Pos", "Nation_Clean", "Min"]].values,
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
        title=dict(text=chart_title, font=dict(color=TEXT, size=15)),
        xaxis=dict(
            title=dict(text="Percentile Score", font=dict(color=MUTED, size=12)),
            range=[0, 110],
            gridcolor=BORDER,
            tickfont=dict(color=MUTED),
        ),
        yaxis=dict(
            title="",
            gridcolor=BORDER,
            tickfont=dict(color=TEXT, size=12),
            categoryorder="array",
            categoryarray=chart_candidates["Player_Unique"].tolist(),
            automargin=True,
        ),
        margin=dict(l=160, r=35, t=55, b=40),
    )

    # 5. Leaderboard Table
    thead = dmc.TableThead(
        dmc.TableTr([
            dmc.TableTh("Rank", style={"color": TEXT}),
            dmc.TableTh("Player", style={"color": TEXT}),
            dmc.TableTh("Club", style={"color": TEXT}),
            dmc.TableTh("Pos", style={"color": TEXT}),
            dmc.TableTh("Nat", style={"color": TEXT}),
            dmc.TableTh("Min", style={"color": TEXT}),
            dmc.TableTh(f"{attr} Score", style={"color": ACCENT, "fontWeight": "700"}),
            dmc.TableTh("Style DNA", style={"color": TEXT}),
            dmc.TableTh("Finishing", style={"color": TEXT}),
            dmc.TableTh("Creativity", style={"color": TEXT}),
            dmc.TableTh("Passing", style={"color": TEXT}),
            dmc.TableTh("Progression", style={"color": TEXT}),
            dmc.TableTh("Defending", style={"color": TEXT}),
            dmc.TableTh("Action", style={"color": TEXT, "textAlign": "center"}),
        ])
    )

    rows = []
    for rank, (_, r) in enumerate(top_candidates.iterrows(), start=1):
        pos_badge_color = "blue" if r["Pos"] == "DF" else "lime" if r["Pos"] == "MF" else "orange"
        target_score = r[col]
        profile_url = f"/player-profile?player={r['Player_Unique']}"

        rows.append(
            dmc.TableTr([
                dmc.TableTd(dmc.Badge(f"#{rank}", color="gray", variant="light", size="sm")),
                dmc.TableTd(dmc.Text(r["Player"], fw=600, c="white")),
                dmc.TableTd(dmc.Text(r["Squad"], size="xs", c="dimmed")),
                dmc.TableTd(dmc.Badge(r["Pos"], color=pos_badge_color, variant="light", size="xs")),
                dmc.TableTd(dmc.Text(r["Nation_Clean"], size="xs", c="dimmed")),
                dmc.TableTd(dmc.Text(f"{r['Min']:,}m", size="xs", c="dimmed")),
                dmc.TableTd(dmc.Text(f"{target_score:.1f}", size="sm", fw=700, c="lime")),
                dmc.TableTd(dmc.Text(r.get("PlayingStyle_Name", "Specialist"), size="xs", c="dimmed")),

                dmc.TableTd(dmc.Text(f"{r['Finishing_Score']:.1f}", size="xs", c="white")),
                dmc.TableTd(dmc.Text(f"{r['Creativity_Score']:.1f}", size="xs", c="white")),
                dmc.TableTd(dmc.Text(f"{r['Passing_Score']:.1f}", size="xs", c="white")),
                dmc.TableTd(dmc.Text(f"{r['Progression_Score']:.1f}", size="xs", c="white")),
                dmc.TableTd(dmc.Text(f"{r['Defending_Score']:.1f}", size="xs", c="white")),

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
        style={"backgroundColor": PANEL, "fontSize": "13px", "borderColor": BORDER},
    )

    return notice, fig, table
