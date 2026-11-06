import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import dash
from dash import Dash, html, dcc, Input, Output, _dash_renderer
import dash_mantine_components as dmc

from app.utils.styling import BG, PANEL, BORDER, TEXT, MUTED, ACCENT

# Configure React 19 BEFORE creating Dash app
_dash_renderer._set_react_version("19.2.4")

PAGES_FOLDER = str(Path(__file__).resolve().parent / "pages")

app = Dash(
    __name__,
    use_pages=True,
    pages_folder=PAGES_FOLDER,
    suppress_callback_exceptions=True,
)

NAV_ITEMS = [
    {"label": "01   Overview", "path": "/", "id": "nav-overview"},
    {"label": "02   Player Explorer", "path": "/player-explorer", "id": "nav-explorer"},
    {"label": "03   Player Profile", "path": "/player-profile", "id": "nav-profile"},
    {"label": "04   Player Comparison", "path": "/player-comparison", "id": "nav-comparison"},
    {"label": "05   Similar Players", "path": "/similar-players", "id": "nav-similar"},
    {"label": "06   Playing Styles", "path": "/playing-styles", "id": "nav-styles"},
    {"label": "07   Rankings", "path": "/player-rankings", "id": "nav-rankings"},
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
        dmc.AppShell(
            [
                # HEADER
                dmc.AppShellHeader(
                    dmc.Group(
                        [
                            dmc.Group(
                                [
                                    dmc.Text("⚽", size="lg"),
                                    dmc.Text("SCOUT", fw=900, size="md", c="lime"),
                                    dmc.Text("|", c="dimmed"),
                                    dmc.Text("PLAYER SCOUTING & ANALYTICS PLATFORM", fw=600, size="xs", c="white"),
                                ],
                                gap="xs",
                                align="center",
                            ),
                            dmc.Group(
                                [
                                    dmc.Badge("1,692 QUALIFIED PLAYERS", color="blue", variant="light", size="sm"),
                                    dmc.Badge("2024–25 SEASON", color="lime", variant="light", size="sm"),
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
                                dmc.Text("FOOTBALL INTELLIGENCE", size="xs", c="dimmed"),
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

                        # FOOTER INFO IN SIDEBAR
                        dmc.Box(
                            [
                                dmc.Text("METRIC FRAMEWORK", size="xs", fw=700, c="dimmed", mb=4),
                                dmc.Text("Position-relative percentiles benchmarked for players with ≥600 minutes.", size="xs", c="dimmed", style={"lineHeight": 1.4}),
                            ],
                            style={"marginTop": "auto"},
                            p="xs",
                        ),
                    ],
                    p="md",
                ),

                # MAIN CONTENT CONTAINER (PAGES)
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


# Callback to highlight active NavLink based on current URL path
@app.callback(
    [Output(item["id"], "active") for item in NAV_ITEMS],
    Input("url", "pathname"),
)
def update_active_nav(pathname):
    if not pathname or pathname == "":
        pathname = "/"

    # Normalize pathname
    active_flags = []
    for item in NAV_ITEMS:
        if item["path"] == "/":
            active_flags.append(pathname == "/" or pathname == "")
        else:
            active_flags.append(pathname.startswith(item["path"]))

    # If none active (e.g. root redirect), default first to True
    if not any(active_flags):
        active_flags[0] = True

    return active_flags


if __name__ == "__main__":
    app.run(debug=True)
