import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import dash
from dash import Dash, html, dcc, Input, Output, State, callback, _dash_renderer
import dash_mantine_components as dmc

from app.utils.styling import BG, PANEL, BORDER, TEXT, MUTED, ACCENT
from app.utils.data_loader import get_all_player_names

# Configure React 19 BEFORE creating Dash app
_dash_renderer._set_react_version("19.2.4")

PAGES_FOLDER = str(Path(__file__).resolve().parent / "pages")

app = Dash(
    __name__,
    use_pages=True,
    pages_folder=PAGES_FOLDER,
    suppress_callback_exceptions=True,
)

all_players = get_all_player_names()

NAV_ITEMS = [
    {"label": "Executive Overview", "path": "/", "id": "nav-overview"},
    {"label": "Player Explorer", "path": "/player-explorer", "id": "nav-explorer"},
    {"label": "Player Profile", "path": "/player-profile", "id": "nav-profile"},
    {"label": "Comparison Matrix", "path": "/player-comparison", "id": "nav-comparison"},
    {"label": "Similar Players", "path": "/similar-players", "id": "nav-similar"},
    {"label": "Tactical Styles", "path": "/playing-styles", "id": "nav-styles"},
    {"label": "Leaderboards", "path": "/player-rankings", "id": "nav-rankings"},
    {"label": "Recruitment Shortlists", "path": "/shortlists", "id": "nav-shortlists"},
]

app.layout = dmc.MantineProvider(
    forceColorScheme="dark",
    theme={
        "primaryColor": "teal",
        "fontFamily": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
        "defaultRadius": "sm",
    },
    children=[
        dcc.Location(id="url", refresh="callback-nav"),
        dcc.Store(
            id="scout-shortlists",
            storage_type="local",
            data=[
                {
                    "player": "Florian Wirtz",
                    "tier": "A-List Target",
                    "notes": "Primary succession candidate for elite attacking midfield creator. 95th percentile creativity.",
                    "added_at": "2024-25 Season",
                },
                {
                    "player": "Moisés Caicedo",
                    "tier": "Primary Alternative",
                    "notes": "Elite ball-winning defensive pivot with top recovery and tackling volumes.",
                    "added_at": "2024-25 Season",
                },
            ],
        ),
        dmc.AppShell(
            id="app-shell",
            children=[
                # HEADER WITH MOBILE BURGER & SEARCH COMMAND
                dmc.AppShellHeader(
                    dmc.Group(
                        [
                            dmc.Group(
                                [
                                    dmc.Burger(
                                        id="mobile-burger",
                                        opened=False,
                                        hiddenFrom="sm",
                                        size="sm",
                                        color="white",
                                    ),
                                    dmc.Text("SCOUT", fw=800, size="sm", c="white", style={"letterSpacing": "1.2px"}),
                                    dmc.Badge(
                                        "PRO",
                                        color="teal",
                                        variant="light",
                                        size="xs",
                                        style={"fontSize": "9px", "height": "16px", "padding": "0 5px", "borderRadius": "3px"}
                                    ),
                                    dmc.Text("|", c="#334155", visibleFrom="sm"),
                                    dmc.Text(
                                        "RECRUITMENT INTELLIGENCE",
                                        fw=600,
                                        size="10px",
                                        c=MUTED,
                                        visibleFrom="md",
                                        style={"letterSpacing": "0.5px"}
                                    ),
                                ],
                                gap="xs",
                                align="center",
                            ),

                            # GLOBAL COMMAND SEARCH
                            dmc.Select(
                                id="header-global-search",
                                placeholder="Search candidate dossier (e.g. Saliba, Haaland)...",
                                data=[{"label": name, "value": name} for name in all_players],
                                searchable=True,
                                w={"base": 200, "sm": 300, "md": 380},
                                size="xs",
                                clearable=True,
                                leftSection=html.Span("🔍", style={"fontSize": "11px", "opacity": 0.5}),
                            ),

                            dmc.Group(
                                [
                                    dcc.Link(
                                        dmc.Badge(
                                            id="header-shortlist-badge",
                                            children="Pipeline: 2",
                                            color="teal",
                                            variant="light",
                                            size="sm",
                                            style={"cursor": "pointer", "fontSize": "10.5px", "fontWeight": 600}
                                        ),
                                        href="/shortlists",
                                        style={"textDecoration": "none"},
                                    ),
                                    dmc.Badge("Big 5 Leagues", color="gray", variant="outline", size="xs", visibleFrom="md", style={"borderColor": "rgba(255, 255, 255, 0.12)", "color": "#94A3B8"}),
                                    dmc.Badge("2024–25 Season", color="gray", variant="outline", size="xs", style={"borderColor": "rgba(255, 255, 255, 0.12)", "color": "#94A3B8"}),
                                ],
                                gap="xs",
                            ),
                        ],
                        justify="space-between",
                        px="lg",
                        h="100%",
                    )
                ),

                # SIDEBAR NAVIGATION
                dmc.AppShellNavbar(
                    [
                        dmc.Group([
                            dmc.Box(
                                style={
                                    "width": "28px",
                                    "height": "28px",
                                    "borderRadius": "6px",
                                    "backgroundColor": "#10B981",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                    "fontWeight": 900,
                                    "color": "#090D14",
                                    "fontSize": "14px",
                                },
                                children="S",
                            ),
                            dmc.Box([
                                dmc.Group([
                                    dmc.Text("SCOUT", fw=800, size="sm", c="white", style={"letterSpacing": "1px"}),
                                    dmc.Badge("ELITE", color="teal", variant="light", size="xs", style={"fontSize": "8px", "height": "16px", "padding": "0 4px"}),
                                ], gap=6, align="center"),
                                dmc.Text("Recruitment Analytics", size="10px", c="#64748B"),
                            ]),
                        ], gap="sm", align="center", mb="md", px=4),

                        dmc.Divider(my="xs", color="rgba(255, 255, 255, 0.06)"),

                        html.Div(
                            [
                                dcc.Link(
                                    dmc.NavLink(
                                        id=item["id"],
                                        label=item["label"],
                                        style={"marginBottom": "2px", "borderRadius": "5px"},
                                    ),
                                    href=item["path"],
                                    style={"textDecoration": "none"},
                                )
                                for item in NAV_ITEMS
                            ],
                            style={"marginTop": "6px"},
                        ),

                        dmc.Divider(my="md", color="rgba(255, 255, 255, 0.06)"),

                        # FOOTER STATUS NOTE
                        dmc.Box(
                            [
                                dmc.Group([
                                    html.Span(className="scout-live-dot"),
                                    dmc.Text("Live Intelligence Cohort", size="11px", fw=600, c="#F8FAFC"),
                                ], gap=8, align="center"),
                                dmc.Text("1,692 qualified players (≥600m)", size="10px", c="#64748B", mt=3),
                                dmc.Text("Engine: pAdj • 7 Sub-Roles • K-Means", size="9px", c="#64748B", mt=1),
                            ],
                            style={
                                "marginTop": "auto",
                                "padding": "10px",
                                "backgroundColor": "#090D14",
                                "borderRadius": "6px",
                                "border": "1px solid rgba(255, 255, 255, 0.05)",
                            },
                        ),
                    ],
                    p="md",
                ),

                # MAIN CONTENT CONTAINER
                dmc.AppShellMain(
                    dmc.Container(
                        dash.page_container,
                        fluid=True,
                        p="xl",
                    )
                ),
            ],
            navbar={
                "width": 240,
                "breakpoint": "sm",
                "collapsed": {"mobile": True},
            },
            header={"height": 56},
            padding="md",
            styles={
                "main": {
                    "backgroundColor": "#090D14",
                    "color": "#F8FAFC",
                    "minHeight": "100vh",
                },
                "navbar": {
                    "backgroundColor": "#0D131F",
                    "borderRight": "1px solid rgba(255, 255, 255, 0.08)",
                },
                "header": {
                    "backgroundColor": "#0D131F",
                    "borderBottom": "1px solid rgba(255, 255, 255, 0.08)",
                    "color": "#F8FAFC",
                },
            },
        ),
    ],
)


# Callback to toggle navbar on mobile
@app.callback(
    Output("app-shell", "navbar"),
    Output("mobile-burger", "opened"),
    Input("mobile-burger", "opened"),
    State("app-shell", "navbar"),
    prevent_initial_call=True,
)
def toggle_mobile_navbar(opened, navbar):
    new_opened = not opened
    navbar = navbar or {"width": 240, "breakpoint": "sm", "collapsed": {}}
    navbar["collapsed"] = {"mobile": not new_opened}
    return navbar, new_opened


# Callback to highlight active sidebar link
@app.callback(
    [Output(item["id"], "active") for item in NAV_ITEMS],
    Input("url", "pathname"),
)
def update_active_nav(pathname):
    if not pathname or pathname == "":
        pathname = "/"

    active_flags = []
    for item in NAV_ITEMS:
        if item["path"] == "/":
            active_flags.append(pathname == "/" or pathname == "")
        else:
            active_flags.append(pathname.startswith(item["path"]))

    if not any(active_flags):
        active_flags[0] = True

    return active_flags


# Callback on global header search to jump to Player Profile
@app.callback(
    Output("url", "href"),
    Input("header-global-search", "value"),
    prevent_initial_call=True,
)
def jump_to_player_profile(selected_name):
    if selected_name and str(selected_name).strip():
        return f"/player-profile?player={selected_name}"
    return dash.no_update


# Callback to update header shortlist counter badge
@app.callback(
    Output("header-shortlist-badge", "children"),
    Input("scout-shortlists", "data"),
)
def update_header_shortlist_badge(shortlist_data):
    count = len(shortlist_data) if isinstance(shortlist_data, list) else 0
    return f"Pipeline: {count}"


if __name__ == "__main__":
    app.run(debug=True)
