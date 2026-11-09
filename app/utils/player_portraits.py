import json
from pathlib import Path
from dash import html

PORTRAITS_DIR = Path(__file__).resolve().parent.parent / "assets" / "players"
METADATA_FILE = PORTRAITS_DIR / "metadata.json"
PLACEHOLDER_URL = "/assets/players/placeholder.svg"

_METADATA_CACHE = None


def _load_metadata():
    global _METADATA_CACHE
    if _METADATA_CACHE is not None:
        return _METADATA_CACHE

    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                _METADATA_CACHE = json.load(f)
        except Exception:
            _METADATA_CACHE = {}
    else:
        _METADATA_CACHE = {}

    return _METADATA_CACHE


def reload_metadata():
    """Forces cache refresh (used after downloading new images)."""
    global _METADATA_CACHE
    _METADATA_CACHE = None
    return _load_metadata()


def get_player_portrait_url(player_identifier):
    """
    Returns the URL path to a player's cached portrait image,
    or the fallback placeholder if not available.
    """
    if not player_identifier:
        return PLACEHOLDER_URL

    metadata = _load_metadata()
    clean_id = str(player_identifier).strip()

    # Look up by exact identifier or stripped name
    record = metadata.get(clean_id)
    if not record and "(" in clean_id:
        base_name = clean_id.split("(")[0].strip()
        record = metadata.get(base_name)

    if record and "filename" in record:
        filename = record["filename"]
        local_file = PORTRAITS_DIR / filename
        if local_file.exists():
            return f"/assets/players/{filename}"

    return PLACEHOLDER_URL


def get_player_image_metadata(player_identifier):
    """
    Returns the metadata dictionary (source, license, attribution, etc.)
    for a player, or None if not found.
    """
    if not player_identifier:
        return None

    metadata = _load_metadata()
    clean_id = str(player_identifier).strip()
    record = metadata.get(clean_id)
    if not record and "(" in clean_id:
        base_name = clean_id.split("(")[0].strip()
        record = metadata.get(base_name)

    return record


def render_player_portrait(player_identifier, size=36, radius=6, style=None):
    """
    Renders an HTML <img> tag with consistent dimensions, object-fit cropping,
    and fallback handling.
    """
    url = get_player_portrait_url(player_identifier)
    meta = get_player_image_metadata(player_identifier)

    title_tooltip = player_identifier
    if meta and meta.get("attribution"):
        title_tooltip = f"{player_identifier} (Photo: {meta.get('attribution')} • {meta.get('license', 'CC')})"

    base_style = {
        "width": f"{size}px",
        "height": f"{size}px",
        "minWidth": f"{size}px",
        "minHeight": f"{size}px",
        "borderRadius": f"{radius}px",
        "objectFit": "cover",
        "backgroundColor": "var(--scout-surface-secondary, #1E293B)",
        "border": "1px solid var(--scout-border, rgba(255, 255, 255, 0.08))",
        "display": "block",
    }
    if style:
        base_style.update(style)

    return html.Img(
        src=url,
        alt=str(player_identifier),
        title=title_tooltip,
        style=base_style,
    )
