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
    {"label": "01   Overview", "path": "/", "id": "nav-overview"},
    {"label": "02   Player Explorer", "path": "/player-explorer", "id": "nav-explorer"},
    {"label": "03   Player Profile", "path": "/player-profile", "id": "nav-profile"},
    {"label": "04   Player Comparison", "path": "/player-comparison", "id": "nav-comparison"},
    {"label": "05   Similar Players", "path": "/similar-players", "id": "nav-similar"},
    {"label": "06   Playing Styles", "path": "/playing-styles", "id": "nav-styles"},
    {"label": "07   Rankings", "path": "/player-rankings", "id": "nav-rankings"},
    {"label": "08   Shortlists", "path": "/shortlists", "id": "nav-shortlists"},
]

app.layout = dmc.MantineProvider(
    forceColorScheme="dark",
    theme={
        "primaryColor": "lime",
        "fontFamily": "Inter, sans-serif",
        "defaultRadius": "md",
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
                # HEADER WITH MOBILE BURGER & QUICK SEARCH
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
                                    dmc.Text("⚽", size="lg"),
                                    dmc.Text("SCOUT", fw=900, size="md", c="lime"),
                                    dmc.Text("|", c="dimmed", visibleFrom="sm"),
                                    dmc.Text("FOOTBALL INTELLIGENCE", fw=600, size="xs", c="white", visibleFrom="md"),
                                ],
                                gap="xs",
                                align="center",
                            ),

                            # GLOBAL QUICK SEARCH
                            dmc.Select(
                                id="header-global-search",
                                placeholder="⚡ Quick Player Search (Jump to Profile)...",
                                data=[{"label": name, "value": name} for name in all_players],
                                searchable=True,
                                w={"base": 190, "sm": 280, "md": 340},
                                size="xs",
                                clearable=True,
                            ),

                            dmc.Group(
                                [
                                    dcc.Link(
                                        dmc.Badge(id="header-shortlist-badge", children="★ Shortlist: 2", color="orange", variant="light", size="sm"),
                                        href="/shortlists",
                                        style={"textDecoration": "none"},
                                    ),
                                    dmc.Badge("1,692 PLAYERS", color="blue", variant="light", size="sm", visibleFrom="md"),
                                    dmc.Badge("2024–25", color="lime", variant="light", size="sm"),
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
                        dmc.Box(
                            [
                                dmc.Title("SCOUT", order=2, c="lime"),
                                dmc.Text("PLAYER SCOUTING & ANALYTICS", size="xs", c="dimmed"),
                            ],
                            mb="md",
                        ),
                        dmc.Divider(my="sm", color=BORDER),

                        html.Div(
                            [
                                dcc.Link(
                                    dmc.NavLink(
                                        id=item["id"],
                                        label=item["label"],
                                        style={"marginBottom": "4px", "borderRadius": "6px"},
                                    ),
                                    href=item["path"],
                                    style={"textDecoration": "none"},
                                )
                                for item in NAV_ITEMS
                            ],
                            style={"marginTop": "8px"},
                        ),

                        dmc.Divider(my="md", color=BORDER),

                        # FOOTER METRIC NOTE
                        dmc.Box(
                            [
                                dmc.Text("ANALYTICAL FRAMEWORK", size="xs", fw=700, c="dimmed", mb=4),
                                dmc.Text("Position-relative percentiles benchmarked for players with ≥600 minutes.", size="xs", c="dimmed", style={"lineHeight": 1.4}),
                            ],
                            style={"marginTop": "auto"},
                            p="xs",
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
                "width": 260,
                "breakpoint": "sm",
                "collapsed": {"mobile": True},
            },
            header={"height": 60},
            padding="md",
            styles={
                "main": {
                    "backgroundColor": BG,
                    "color": TEXT,
                    "minHeight": "100vh",
                },
                "navbar": {
                    "backgroundColor": "#131E30",
                    "borderRight": f"1px solid {BORDER}",
                },
                "header": {
                    "backgroundColor": "#131E30",
                    "borderBottom": f"1px solid {BORDER}",
                    "color": TEXT,
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
    navbar = navbar or {"width": 260, "breakpoint": "sm", "collapsed": {}}
    navbar["collapsed"] = {"mobile": not new_opened}
    return navbar, new_opened


# Callback to highlight active NavLink based on current URL path
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
    return f"★ Shortlist: {count}"


if __name__ == "__main__":
    app.run(debug=True)
