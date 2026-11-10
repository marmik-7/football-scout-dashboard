import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import dash
from dash import Dash, html, dcc, Input, Output, State, callback, _dash_renderer
import dash_mantine_components as dmc

from app.utils.styling import BG, PANEL, BORDER, TEXT, MUTED, ACCENT, SUBTLE
from app.utils.data_loader import get_all_player_names

# Configure React 19 BEFORE creating Dash app
_dash_renderer._set_react_version("19.2.4")

PAGES_FOLDER = str(Path(__file__).resolve().parent / "pages")

app = Dash(
    __name__,
    use_pages=True,
    pages_folder=PAGES_FOLDER,
    suppress_callback_exceptions=True,
    title="SCOUT — Recruitment Intelligence",
    update_title=None,
)

app.index_string = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        <link rel="icon" type="image/svg+xml" href="/assets/logo.svg">
        <link rel="alternate icon" type="image/x-icon" href="/assets/favicon.ico">
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""

all_players = get_all_player_names()

# Categorized navigation items conforming to Phase 9.5 Information Architecture
NAV_CATEGORIES = [
    {
        "category": "WORKSPACE",
        "items": [
            {"label": "Overview", "path": "/", "id": "nav-overview"},
            {"label": "Player Explorer", "path": "/player-explorer", "id": "nav-explorer"},
            {"label": "Player Dossiers", "path": "/player-profile", "id": "nav-profile"},
            {"label": "Comparison", "path": "/player-comparison", "id": "nav-comparison"},
            {"label": "Similar Players", "path": "/similar-players", "id": "nav-similar"},
        ],
    },
    {
        "category": "ANALYTICS",
        "items": [
            {"label": "Playing Styles", "path": "/playing-styles", "id": "nav-styles"},
            {"label": "Rankings", "path": "/player-rankings", "id": "nav-rankings"},
        ],
    },
    {
        "category": "RECRUITMENT",
        "items": [
            {"label": "Shortlists", "path": "/shortlists", "id": "nav-shortlists"},
        ],
    },
]

# Flat list for active state callbacks (maintaining backward compatibility)
NAV_ITEMS = [item for cat in NAV_CATEGORIES for item in cat["items"]]

app.layout = dmc.MantineProvider(
    id="mantine-provider",
    defaultColorScheme="dark",
    forceColorScheme="dark",
    theme={
        "primaryColor": "teal",
        "fontFamily": '"Twemoji Country Flags", Inter, -apple-system, BlinkMacSystemFont, sans-serif',
        "defaultRadius": "sm",
    },
    children=[
        dcc.Location(id="url", refresh="callback-nav"),
        dcc.Store(
            id="theme-store",
            storage_type="local",
            data="dark",
        ),
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
                                        color="gray",
                                    ),
                                    html.Img(
                                        src="/assets/logo.svg",
                                        alt="SCOUT Logo",
                                        style={"width": "24px", "height": "24px", "display": "block", "borderRadius": "5px"},
                                    ),
                                    dmc.Text("SCOUT", fw=800, size="sm", style={"letterSpacing": "1.2px", "color": "var(--scout-text-primary)"}),
                                    dmc.Badge(
                                        "PRO",
                                        color="teal",
                                        variant="light",
                                        size="xs",
                                        style={"fontSize": "8.5px", "height": "15px", "padding": "0 4px", "borderRadius": "3px"}
                                    ),
                                    dmc.Text("|", c="var(--scout-border-hover)", visibleFrom="sm"),
                                    dmc.Text(
                                        "RECRUITMENT INTELLIGENCE",
                                        fw=600,
                                        size="10px",
                                        c="var(--scout-text-muted)",
                                        visibleFrom="md",
                                        style={"letterSpacing": "0.5px"}
                                    ),
                                ],
                                gap="xs",
                                align="center",
                            ),

                            # GLOBAL COMMAND SEARCH (PROMINENT RECRUITMENT SEARCH)
                            dmc.Select(
                                id="header-global-search",
                                placeholder="Search 1,692 player dossiers (e.g. Saliba, Haaland, Wirtz)...",
                                data=[{"label": name, "value": name} for name in all_players],
                                searchable=True,
                                clearable=True,
                                size="sm",
                                leftSection=html.Img(
                                    src="/assets/search.svg",
                                    alt="Search",
                                    style={"width": "16px", "height": "16px", "display": "block"},
                                ),
                                leftSectionPointerEvents="none",
                                rightSection=dmc.Kbd("/", size="xs"),
                                rightSectionPointerEvents="none",
                                className="scout-header-search",
                                w={"base": 140, "xs": 190, "sm": 320, "md": 460, "lg": 560},
                            ),

                            dmc.Group(
                                [
                                    # Theme Switcher (Dark / Light)
                                    dmc.SegmentedControl(
                                        id="global-theme-toggle",
                                        data=[
                                            {"label": "🌙", "value": "dark"},
                                            {"label": "☀️", "value": "light"},
                                        ],
                                        value="dark",
                                        size="xs",
                                        color="teal",
                                        persistence=True,
                                        persistence_type="local",
                                        style={"fontWeight": 600},
                                    ),
                                    # Pipeline Shortlist Badge Link
                                    dmc.Box(
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
                                        visibleFrom="sm",
                                    ),
                                ],
                                gap="xs",
                                align="center",
                                wrap="nowrap",
                            ),
                        ],
                        justify="space-between",
                        px="md",
                        h="100%",
                    )
                ),

                # SIDEBAR NAVIGATION
                dmc.AppShellNavbar(
                    [
                        # Categorized Nav Items (Linear Style)
                        html.Div(
                            [
                                html.Div(
                                    [
                                        dmc.Text(cat["category"], className="scout-nav-category"),
                                        html.Div(
                                            [
                                                dmc.NavLink(
                                                    id=item["id"],
                                                    label=item["label"],
                                                    href=item["path"],
                                                    style={"marginBottom": "2px", "borderRadius": "5px"},
                                                )
                                                for item in cat["items"]
                                            ]
                                        ),
                                    ],
                                    style={"marginBottom": "8px"},
                                )
                                for cat in NAV_CATEGORIES
                            ],
                            style={"marginTop": "2px", "overflowY": "auto", "flexGrow": 1},
                        ),

                        dmc.Divider(my="xs", color="var(--scout-border-subtle)"),

                        # FOOTER STATUS NOTE
                        dmc.Box(
                            [
                                dmc.Group([
                                    html.Span(className="scout-live-dot"),
                                    dmc.Text("Live Intelligence Cohort", size="11px", fw=600, style={"color": "var(--scout-text-primary)"}),
                                ], gap=8, align="center"),
                                dmc.Text(f"{len(all_players):,} qualified players (≥600m)", size="10px", style={"color": "var(--scout-text-muted)"}, mt=3),
                                dmc.Text("Engine: pAdj • 7 Sub-Roles • K-Means", size="9px", style={"color": "var(--scout-text-muted)"}, mt=1),
                            ],
                            style={
                                "marginTop": "auto",
                                "padding": "10px",
                                "backgroundColor": "var(--scout-surface-secondary)",
                                "borderRadius": "6px",
                                "border": "1px solid var(--scout-border-subtle)",
                            },
                        ),
                    ],
                    p="sm",
                    style={"display": "flex", "flexDirection": "column"},
                ),

                # MAIN CONTENT CONTAINER
                dmc.AppShellMain(
                    dmc.Container(
                        dash.page_container,
                        fluid=True,
                        p="lg",
                    )
                ),
            ],
            navbar={
                "width": 230,
                "breakpoint": "sm",
                "collapsed": {"mobile": True},
            },
            header={"height": 52},
            padding="md",
            styles={
                "main": {
                    "backgroundColor": "var(--scout-bg)",
                    "color": "var(--scout-text-primary)",
                    "minHeight": "100vh",
                },
                "navbar": {
                    "backgroundColor": "var(--scout-bg-sidebar)",
                    "borderRight": "1px solid var(--scout-border)",
                },
                "header": {
                    "backgroundColor": "var(--scout-bg-sidebar)",
                    "borderBottom": "1px solid var(--scout-border)",
                    "color": "var(--scout-text-primary)",
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
    navbar = navbar or {"width": 230, "breakpoint": "sm", "collapsed": {}}
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


# Callback to synchronize global theme (Dark vs Light)
@app.callback(
    Output("mantine-provider", "forceColorScheme"),
    Output("theme-store", "data"),
    Input("global-theme-toggle", "value"),
)
def update_theme_mode(selected_theme):
    theme_val = selected_theme or "dark"
    return theme_val, theme_val


if __name__ == "__main__":
    app.run(debug=True)
