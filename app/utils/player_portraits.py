import json
from pathlib import Path
from dash import html
import dash_mantine_components as dmc

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


def _resolve_player_record(player_identifier, metadata):
    """
    Resolves player record from metadata.
    Prioritizes exact identifier (including club suffixes).
    Never silently assigns a portrait if club disambiguation conflicts exist.
    """
    if not player_identifier:
        return None

    clean_id = str(player_identifier).strip()

    # 1. Exact match (including full name with club disambiguation suffix, e.g. "Nicolás González (Juventus)")
    record = metadata.get(clean_id)
    if record:
        return record

    # 2. Base name match only if no club-specific disambiguation collisions exist in metadata
    if "(" in clean_id:
        base_name = clean_id.split("(")[0].strip()
        # Identity disambiguation guard: if metadata contains club-disambiguated entries
        # for this base name (e.g. "Nicolás González (Juventus)"), never silently assign
        # another club's or unverified portrait to this player.
        has_club_collision = any(
            k != clean_id and k.startswith(f"{base_name} (")
            for k in metadata.keys()
        )
        if not has_club_collision:
            record = metadata.get(base_name)

    return record


def get_player_portrait_url(player_identifier):
    """
    Returns the URL path to a player's cached portrait image,
    or the fallback placeholder if not available.
    """
    if not player_identifier:
        return PLACEHOLDER_URL

    metadata = _load_metadata()
    record = _resolve_player_record(player_identifier, metadata)

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
    return _resolve_player_record(player_identifier, metadata)


def render_player_portrait(player_identifier, size=36, radius=6, style=None):
    """
    Renders a player portrait component with consistent dimensions, object-fit cropping,
    and safe client-side fallback handling.
    """
    url = get_player_portrait_url(player_identifier)
    meta = get_player_image_metadata(player_identifier)

    title_tooltip = str(player_identifier) if player_identifier else "Player Portrait"
    if meta and meta.get("attribution"):
        title_tooltip = f"{player_identifier} (Photo: {meta.get('attribution')} • {meta.get('license', 'CC')})"

    is_hero = size >= 80
    base_style = {
        "width": f"{size}px",
        "height": f"{size}px",
        "minWidth": f"{size}px",
        "minHeight": f"{size}px",
        "borderRadius": f"{radius}px",
        "objectFit": "cover",
        "objectPosition": "center 20%",
        "backgroundColor": "var(--scout-surface-secondary, #1E293B)",
        "border": "1px solid var(--scout-border, rgba(255, 255, 255, 0.08))" if not is_hero else "2px solid var(--scout-border, rgba(255, 255, 255, 0.12))",
        "boxShadow": "0 1px 3px rgba(0, 0, 0, 0.18)" if not is_hero else "0 4px 14px rgba(0, 0, 0, 0.28)",
        "display": "block",
    }
    if style:
        base_style.update(style)

    return dmc.Image(
        src=url,
        fallbackSrc=PLACEHOLDER_URL,
        alt=str(player_identifier) if player_identifier else "Player Portrait",
        className="scout-portrait-hero" if is_hero else "scout-portrait",
        w=size,
        h=size,
        radius=radius,
        fit="cover",
        attributes={"title": title_tooltip},
        style=base_style,
    )
