import dash
from dash import html, dcc, Input, Output, State, ALL, callback
import dash_mantine_components as dmc
import pandas as pd

from app.utils.data_loader import (
    load_data,
    get_player_by_name,
    get_all_player_names,
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
    create_metric_card,
    create_section_card,
    get_percentile_tier,
)

dash.register_page(__name__, path="/shortlists", name="Shortlists", order=8)

df = load_data()
all_player_names = get_all_player_names()
unique_subroles = get_unique_subroles()

PRIORITY_TIERS = [
    {"label": "★ A-List Target (Priority 1)", "value": "A-List Target", "color": "red"},
    {"label": "◆ Primary Alternative (Priority 2)", "value": "Primary Alternative", "color": "blue"},
    {"label": "● Monitor / Development (Priority 3)", "value": "Monitor / Development", "color": "orange"},
]

TIER_COLORS = {
    "A-List Target": "red",
    "Primary Alternative": "blue",
    "Monitor / Development": "orange",
}


def layout():
    return dmc.Container(
        [
            create_page_header(
                title="Recruitment Shortlists & Dossiers",
                subtitle="Manage recruitment target pipelines, priority tier assignments, scout intelligence notes, and executive dossier exports.",
                badge_text="RECRUITMENT INTELLIGENCE",
            ),

            # QUICK ADD TARGET MODAL
            dmc.Modal(
                id="shortlist-add-modal",
                title=dmc.Group([
                    dmc.Text("⭐", size="md"),
                    dmc.Title("Bookmark Target to Recruitment Pipeline", order=4, c="white"),
                ], gap="xs"),
                opened=False,
                centered=True,
                radius="md",
                styles={"content": {"backgroundColor": PANEL, "borderColor": BORDER}},
                children=[
                    dmc.Box([
                        dmc.Select(
                            id="shortlist-modal-player",
                            label="Target Candidate",
                            placeholder="Search and select candidate...",
                            data=[{"label": name, "value": name} for name in all_player_names],
                            value=all_player_names[0] if all_player_names else None,
                            searchable=True,
                            allowDeselect=False,
                            mb="sm",
                        ),
                        dmc.Select(
                            id="shortlist-modal-tier",
                            label="Recruitment Priority Tier",
                            data=[
                                {"label": t["label"], "value": t["value"]} for t in PRIORITY_TIERS
                            ],
                            value="A-List Target",
                            allowDeselect=False,
                            mb="sm",
                        ),
                        dmc.Textarea(
                            id="shortlist-modal-notes",
                            label="Scout Intelligence Notes",
                            placeholder="Enter tactical observations, scouting context, estimated valuation, or developmental timeline...",
                            minRows=3,
                            autosize=True,
                            mb="md",
                        ),
                        dmc.Group([
                            dmc.Button("Cancel", id="shortlist-modal-cancel", variant="subtle", color="gray"),
                            dmc.Button("Save to Pipeline", id="shortlist-modal-submit", variant="filled", color="lime"),
                        ], justify="flex-end"),
                    ]),
                ],
            ),

            # SUMMARY METRIC CARDS
            html.Div(id="shortlist-metrics-container"),

            dmc.Space(h=20),

            # CONTROLS PANEL
            create_section_card(
                dmc.Box([
                    dmc.Grid(
                        [
                            dmc.GridCol(
                                dmc.TextInput(
                                    id="shortlist-search",
                                    placeholder="Search saved candidates...",
                                    leftSection="🔍",
                                    size="xs",
                                    debounce=200,
                                ),
                                span={"base": 12, "sm": 6, "md": 3},
                            ),
                            dmc.GridCol(
                                dmc.Select(
                                    id="shortlist-filter-tier",
                                    placeholder="Filter by Priority Tier",
                                    data=[{"label": "All Priority Tiers", "value": "ALL"}] + [
                                        {"label": t["label"], "value": t["value"]} for t in PRIORITY_TIERS
                                    ],
                                    value="ALL",
                                    size="xs",
                                    allowDeselect=False,
                                ),
                                span={"base": 12, "sm": 6, "md": 3},
                            ),
                            dmc.GridCol(
                                dmc.Select(
                                    id="shortlist-filter-pos",
                                    placeholder="Filter by Position",
                                    data=[
                                        {"label": "All Positions", "value": "ALL"},
                                        {"label": "Defenders (DF)", "value": "DF"},
                                        {"label": "Midfielders (MF)", "value": "MF"},
                                        {"label": "Forwards (FW)", "value": "FW"},
                                    ],
                                    value="ALL",
                                    size="xs",
                                    allowDeselect=False,
                                ),
                                span={"base": 12, "sm": 6, "md": 2},
                            ),
                            dmc.GridCol(
                                dmc.Select(
                                    id="shortlist-filter-subrole",
                                    placeholder="Filter by Sub-Role",
                                    data=[{"label": "All Sub-Roles", "value": "ALL"}] + [
                                        {"label": s, "value": s} for s in unique_subroles
                                    ],
                                    value="ALL",
                                    size="xs",
                                    allowDeselect=False,
                                ),
                                span={"base": 12, "sm": 6, "md": 2},
                            ),
                            dmc.GridCol(
                                dmc.Group([
                                    dmc.Button(
                                        "➕ Add Target",
                                        id="shortlist-open-add-btn",
                                        size="xs",
                                        variant="filled",
                                        color="lime",
                                    ),
                                    dmc.Button(
                                        "📥 Export Dossier",
                                        id="shortlist-export-btn",
                                        size="xs",
                                        variant="light",
                                        color="cyan",
                                    ),
                                    dcc.Download(id="shortlist-download-csv"),
                                ], gap="xs"),
                                span={"base": 12, "sm": 12, "md": 2},
                            ),
                        ],
                        gap="sm",
                        align="center",
                    ),
                ]),
                title="Pipeline Management Controls",
                subtitle="Filter bookmarked targets, add new recruitment candidates, and export dossiers",
            ),

            dmc.Space(h=20),

            # SHORTLIST CANDIDATES TABLE
            create_section_card(
                html.Div(id="shortlist-table-container", style={"overflowX": "auto"}),
                title="Target Candidates & Scout Intelligence",
                subtitle="Persistent recruitment watchlists with priority tags, notes, and 7-dimensional attributes",
            ),
        ],
        fluid=True,
        p=0,
    )


# --------------------------------------------------
# CALLBACKS
# --------------------------------------------------

# Modal Toggle
@callback(
    Output("shortlist-add-modal", "opened"),
    Input("shortlist-open-add-btn", "n_clicks"),
    Input("shortlist-modal-cancel", "n_clicks"),
    Input("shortlist-modal-submit", "n_clicks"),
    State("shortlist-add-modal", "opened"),
    prevent_initial_call=True,
)
def toggle_shortlist_modal(n_open, n_cancel, n_submit, is_open):
    return not is_open


# Add Player to Shortlist Store
@callback(
    Output("scout-shortlists", "data", allow_duplicate=True),
    Input("shortlist-modal-submit", "n_clicks"),
    State("shortlist-modal-player", "value"),
    State("shortlist-modal-tier", "value"),
    State("shortlist-modal-notes", "value"),
    State("scout-shortlists", "data"),
    prevent_initial_call=True,
)
def add_player_to_shortlist(n_clicks, player_name, tier, notes, current_data):
    if not player_name:
        return dash.no_update

    current_data = current_data or []
    # Check if player already exists; update if so, or append
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
            "notes": notes or "Target identified for recruitment evaluation.",
            "added_at": "2024-25 Season",
        })

    return updated


# Remove Player from Shortlist
@callback(
    Output("scout-shortlists", "data", allow_duplicate=True),
    Input({"type": "shortlist-remove-btn", "index": ALL}, "n_clicks"),
    State("scout-shortlists", "data"),
    prevent_initial_call=True,
)
def remove_player_from_shortlist(n_clicks_list, current_data):
    ctx = dash.callback_context
    if not ctx.triggered or not current_data:
        return dash.no_update

    # Identify which button was clicked
    trig_id = ctx.triggered_id
    if not trig_id or not isinstance(trig_id, dict):
        return dash.no_update

    target_player = trig_id.get("index")
    updated = [item for item in current_data if item.get("player") != target_player]
    return updated


# Render Shortlist View & Metrics
@callback(
    Output("shortlist-metrics-container", "children"),
    Output("shortlist-table-container", "children"),
    Input("scout-shortlists", "data"),
    Input("shortlist-search", "value"),
    Input("shortlist-filter-tier", "value"),
    Input("shortlist-filter-pos", "value"),
    Input("shortlist-filter-subrole", "value"),
)
def update_shortlist_view(shortlist_data, search, filter_tier, filter_pos, filter_subrole):
    shortlist_data = shortlist_data or []

    # 1. Compute Metrics
    total_count = len(shortlist_data)
    a_list = sum(1 for x in shortlist_data if x.get("tier") == "A-List Target")
    prim_alt = sum(1 for x in shortlist_data if x.get("tier") == "Primary Alternative")
    monitor = sum(1 for x in shortlist_data if x.get("tier") == "Monitor / Development")

    metrics_grid = dmc.Grid(
        [
            dmc.GridCol(
                create_metric_card("Total Targets", total_count, "Active candidates in recruitment pipeline", color="lime"),
                span={"base": 12, "sm": 6, "lg": 3},
            ),
            dmc.GridCol(
                create_metric_card("★ A-List Targets", a_list, "Priority 1 primary transfer objectives", color="red"),
                span={"base": 12, "sm": 6, "lg": 3},
            ),
            dmc.GridCol(
                create_metric_card("◆ Primary Alternatives", prim_alt, "Priority 2 backup succession options", color="blue"),
                span={"base": 12, "sm": 6, "lg": 3},
            ),
            dmc.GridCol(
                create_metric_card("● Monitor / Development", monitor, "Priority 3 long-term watchlist prospects", color="orange"),
                span={"base": 12, "sm": 6, "lg": 3},
            ),
        ],
        gap="md",
    )

    if not shortlist_data:
        empty_view = dmc.Alert(
            "Your recruitment pipeline is currently empty. Click '➕ Add Target' above, or bookmark candidates from Player Explorer and Player Profile to build your recruitment dossiers.",
            title="No Bookmarked Candidates",
            color="yellow",
            variant="light",
            radius="md",
            p="md",
        )
        return metrics_grid, empty_view

    # 2. Filter Table Candidates
    items = []
    for entry in shortlist_data:
        p_name = entry.get("player")
        p_record = get_player_by_name(p_name)
        if p_record is None:
            continue

        # Filters
        if search and str(search).strip():
            q = str(search).strip().lower()
            if q not in p_record["Player"].lower() and q not in p_record["Squad"].lower():
                continue

        if filter_tier and filter_tier != "ALL":
            if entry.get("tier") != filter_tier:
                continue

        if filter_pos and filter_pos != "ALL":
            if p_record["Pos"] != filter_pos:
                continue

        if filter_subrole and filter_subrole != "ALL":
            if p_record.get("SubRole") != filter_subrole:
                continue

        items.append((entry, p_record))

    if not items:
        empty_filter = dmc.Alert(
            "No candidates in your pipeline matched the selected filters. Try broadening your filter parameters.",
            title="No Filter Matches",
            color="yellow",
            variant="light",
        )
        return metrics_grid, empty_filter

    # 3. Build Shortlist Table
    thead = dmc.TableThead(
        dmc.TableTr([
            dmc.TableTh("Player", style={"color": TEXT}),
            dmc.TableTh("Club / League", style={"color": TEXT}),
            dmc.TableTh("Pos / Role", style={"color": TEXT}),
            dmc.TableTh("Age", style={"color": TEXT}),
            dmc.TableTh("Priority Tier", style={"color": TEXT}),
            dmc.TableTh("Scout Notes", style={"color": TEXT, "width": "220px"}),
            dmc.TableTh("Finishing", style={"color": TEXT}),
            dmc.TableTh("Creativity", style={"color": TEXT}),
            dmc.TableTh("Passing", style={"color": TEXT}),
            dmc.TableTh("Progression", style={"color": TEXT}),
            dmc.TableTh("Defending (pAdj)", style={"color": TEXT}),
            dmc.TableTh("Security", style={"color": TEXT}),
            dmc.TableTh("Aerial", style={"color": TEXT}),
            dmc.TableTh("Actions", style={"color": TEXT, "textAlign": "center"}),
        ])
    )

    def render_tier_score(score_val):
        t = get_percentile_tier(score_val)
        return dmc.TableTd(dmc.Text(f"{score_val:.1f}", fw=700, size="xs", style={"color": t["color"], "fontVariantNumeric": "tabular-nums"}))

    rows = []
    for entry, p in items:
        p_name = p["Player"]
        tier = entry.get("tier", "A-List Target")
        tier_color = TIER_COLORS.get(tier, "lime")
        tier_badge = dmc.Badge(tier, color=tier_color, variant="filled", size="xs")

        pos_badge_color = "blue" if p["Pos"] == "DF" else "lime" if p["Pos"] == "MF" else "orange"
        notes = entry.get("notes", "No notes recorded.")

        profile_url = f"/player-profile?player={p['Player_Unique']}"
        compare_url = f"/player-comparison?player1={p['Player_Unique']}"

        rows.append(
            dmc.TableTr([
                dmc.TableTd([
                    dmc.Text(p_name, fw=700, size="sm", c="white"),
                    dmc.Text(f"Added {entry.get('added_at', '2024-25')}", size="10px", c="dimmed"),
                ]),
                dmc.TableTd([
                    dmc.Text(p["Squad"], size="xs", fw=500, c="white"),
                    dmc.Text(p.get("Comp_Clean", "Big 5"), size="10px", c="dimmed"),
                ]),
                dmc.TableTd([
                    dmc.Badge(p["Pos"], color=pos_badge_color, variant="light", size="xs"),
                    dmc.Text(p.get("SubRole", "Specialist"), size="10px", c="dimmed", mt=2),
                ]),
                dmc.TableTd(dmc.Text(f"{p['Age']} ({p['Min']:,}m)", size="xs", c="white")),
                dmc.TableTd(tier_badge),
                dmc.TableTd(
                    dmc.Text(notes, size="xs", c="dimmed", style={"maxWidth": "220px", "overflow": "hidden", "textOverflow": "ellipsis", "whiteSpace": "nowrap"})
                ),

                render_tier_score(p["Finishing_Score"]),
                render_tier_score(p["Creativity_Score"]),
                render_tier_score(p["Passing_Score"]),
                render_tier_score(p["Progression_Score"]),
                render_tier_score(p["Defending_Score"]),
                render_tier_score(p["BallSecurity_Score"]),
                render_tier_score(p["Aerial_Score"]),

                dmc.TableTd(
                    dmc.Group([
                        dcc.Link(
                            dmc.Button("Profile", size="xs", variant="light", color="lime"),
                            href=profile_url,
                            style={"textDecoration": "none"},
                        ),
                        dcc.Link(
                            dmc.Button("Compare", size="xs", variant="subtle", color="blue"),
                            href=compare_url,
                            style={"textDecoration": "none"},
                        ),
                        dmc.Button(
                            "✕",
                            id={"type": "shortlist-remove-btn", "index": p_name},
                            size="xs",
                            variant="subtle",
                            color="red",
                        ),
                    ], gap=4, justify="center"),
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

    return metrics_grid, table


# Export Shortlist Dossier to CSV
@callback(
    Output("shortlist-download-csv", "data"),
    Input("shortlist-export-btn", "n_clicks"),
    State("scout-shortlists", "data"),
    prevent_initial_call=True,
)
def export_shortlist_dossier(n_clicks, shortlist_data):
    if not shortlist_data:
        return dash.no_update

    records = []
    for entry in shortlist_data:
        p = get_player_by_name(entry.get("player"))
        if p is None:
            continue
        records.append({
            "Player": p["Player"],
            "Squad": p["Squad"],
            "Competition": p.get("Comp_Clean", p["Comp"]),
            "Position": p["Pos"],
            "Tactical_SubRole": p.get("SubRole", "N/A"),
            "Age": p["Age"],
            "Minutes": p["Min"],
            "Recruitment_Tier": entry.get("tier", "A-List Target"),
            "Scout_Notes": entry.get("notes", ""),
            "Finishing_Score": round(float(p["Finishing_Score"]), 1),
            "Creativity_Score": round(float(p["Creativity_Score"]), 1),
            "Passing_Score": round(float(p["Passing_Score"]), 1),
            "Progression_Score": round(float(p["Progression_Score"]), 1),
            "Defending_Score_pAdj": round(float(p["Defending_Score"]), 1),
            "BallSecurity_Score": round(float(p["BallSecurity_Score"]), 1),
            "Aerial_Score": round(float(p["Aerial_Score"]), 1),
            "Goals": int(p.get("Gls", 0)),
            "Assists": int(p.get("Ast", 0)),
            "Expected_Goals_xG": round(float(p.get("xG", 0.0)), 2),
            "Expected_Assists_xA": round(float(p.get("xA", 0.0)), 2),
            "Finishing_Diff_G_minus_xG": round(float(p.get("G-xG", 0.0)), 2),
            "Shot_Quality_npxG_per_Sh": round(float(p.get("npxG/Sh", 0.0)), 2),
            "pAdj_Defending_Factor": round(float(p.get("pAdj_Factor", 1.0)), 2),
        })

    if not records:
        return dash.no_update

    df_export = pd.DataFrame(records)
    return dcc.send_data_frame(df_export.to_csv, "scout_recruitment_dossier_2024_25.csv", index=False)
