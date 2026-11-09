from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "players_clustered.csv"
SUMMARY_PATH = PROJECT_ROOT / "data" / "processed" / "cluster_summary.csv"

# Descriptive playing-style names based on empirical attribute means from cluster_summary.csv
CLUSTER_NAMES = {
    ("DF", 0): "Attacking Full-Back",
    ("DF", 1): "Ball-Playing Centre-Back",
    ("DF", 2): "Wide Transition Defender",
    ("DF", 3): "Stopper / Defensive Anchor",
    ("MF", 0): "Box-to-Box Threat",
    ("MF", 1): "Ball-Winning Anchor",
    ("MF", 2): "Deep-Lying Controller",
    ("MF", 3): "Advanced Playmaker",
    ("FW", 0): "Complete Forward",
    ("FW", 1): "Aerial Target Man",
    ("FW", 2): "High-Pressing Forward",
    ("FW", 3): "Dynamic Inverted Creator",
}

# IOC / FIFA 3-letter country code to Flag emoji mapping
COUNTRY_FLAGS = {
    "ESP": "🇪🇸", "FRA": "🇫🇷", "GER": "🇩🇪", "ENG": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "ITA": "🇮🇹", "BRA": "🇧🇷",
    "ARG": "🇦🇷", "NED": "🇳🇱", "POR": "🇵🇹", "BEL": "🇧🇪", "DEN": "🇩🇰", "MAR": "🇲🇦",
    "CIV": "🇨🇮", "AUT": "🇦🇹", "SEN": "🇸🇳", "CRO": "🇭🇷", "NGA": "🇳🇬", "SWE": "🇸🇪",
    "SUI": "🇨🇭", "ALG": "🇩🇿", "USA": "🇺🇸", "NOR": "🇳🇴", "GHA": "🇬🇭", "MLI": "🇲🇱",
    "URU": "🇺🇾", "SRB": "🇷🇸", "JPN": "🇯🇵", "SCO": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "CMR": "🇨🇲", "COL": "🇨🇴",
    "POL": "🇵🇱", "WAL": "🏴󠁧󠁢󠁷󠁬󠁳󠁿", "IRL": "🇮🇪", "CZE": "🇨🇿", "GRE": "🇬🇷", "HUN": "🇭🇺",
    "TUR": "🇹🇷", "GUI": "🇬🇳", "ALB": "🇦🇱", "CAN": "🇨🇦", "UKR": "🇺🇦", "SVN": "🇸🇮",
    "SVK": "🇸🇰", "TUN": "🇹🇳", "KOR": "🇰🇷", "MEX": "🇲🇽", "CHI": "🇨🇱", "ECU": "🇪🇨",
    "PAR": "🇵🇾", "ROU": "🇷🇴", "BIH": "🇧🇦", "GEO": "🇬🇪", "EGY": "🇪🇬", "BFA": "🇧🇫",
    "COD": "🇨🇩", "GAB": "🇬🇦", "JAM": "🇯🇲", "AUS": "🇦🇺", "VEN": "🇻🇪", "KOS": "🇽🇰",
    "MNE": "🇲🇪", "MKD": "🇲🇰", "NIR": "🇬🇧", "ISL": "🇮🇸", "FIN": "🇫🇮", "ISR": "🇮🇱",
}

# Standard European Top 5 League mappings
COMPETITION_NAMES = {
    "eng Premier League": "Premier League",
    "es La Liga": "La Liga",
    "it Serie A": "Serie A",
    "de Bundesliga": "Bundesliga",
    "fr Ligue 1": "Ligue 1",
}

def clean_competition_name(comp_raw):
    """
    Translates raw competition string into clean league name(s).
    """
    if not comp_raw or pd.isna(comp_raw):
        return "N/A"
    parts = [COMPETITION_NAMES.get(p.strip(), p.strip()) for p in str(comp_raw).split(",")]
    return ", ".join(parts)

def format_nation_flag(nation_code):
    """
    Returns country code with its corresponding national flag emoji.
    """
    if not nation_code or nation_code == "N/A":
        return "N/A"
    flag = COUNTRY_FLAGS.get(str(nation_code).strip(), "🌐")
    return f"{flag} {nation_code}"


_CACHED_DF = None
_CACHED_SUMMARY = None
_PLAYER_LOOKUP_INDEX = {}
_POSITION_AVERAGES_CACHE = {}
_ALL_PLAYER_NAMES_CACHE = None
_UNIQUE_SQUADS_CACHE = None
_UNIQUE_NATIONS_CACHE = None


def load_data():
    """
    Loads and caches the 1,692 player dataset with precomputed
    percentile scores, K-Means clusters, and PCA coordinates.
    Also builds high-speed in-memory hash indexes and benchmark distributions.
    """
    global _CACHED_DF, _PLAYER_LOOKUP_INDEX, _POSITION_AVERAGES_CACHE
    global _ALL_PLAYER_NAMES_CACHE, _UNIQUE_SQUADS_CACHE, _UNIQUE_NATIONS_CACHE

    if _CACHED_DF is not None:
        return _CACHED_DF

    raw_df = pd.read_csv(DATA_PATH)
    df = raw_df.copy()

    # Clean nation values and extract standard 3-letter IOC code
    nation_clean = df["Nation"].fillna("Unknown").apply(
        lambda x: x.split()[-1] if x != "Unknown" and str(x).strip() else "N/A"
    )

    nation_display = nation_clean.apply(format_nation_flag)

    # Disambiguate duplicate player names by appending club in parentheses
    name_counts = df["Player"].value_counts()
    dup_names = set(name_counts[name_counts > 1].index)
    player_unique = df.apply(
        lambda r: f"{r['Player']} ({r['Squad']})" if r["Player"] in dup_names else r["Player"],
        axis=1,
    )

    # Assign descriptive cluster label
    cluster_names = df.apply(
        lambda r: CLUSTER_NAMES.get((r["Pos"], int(r["PlayingStyle_Cluster"])), f"Style {r['PlayingStyle_Cluster']}"),
        axis=1,
    )

    # Clean competition / league names
    comp_clean = df["Comp"].apply(clean_competition_name)

    # Batch assign to avoid DataFrame fragmentation warning
    df = df.assign(
        Comp_Clean=comp_clean,
        Nation_Clean=nation_clean,
        Nation_Display=nation_display,
        Player_Unique=player_unique,
        PlayingStyle_Name=cluster_names,
        Age=pd.to_numeric(df["Age"], errors="coerce").fillna(0).astype(int),
        Born=pd.to_numeric(df["Born"], errors="coerce").fillna(0).astype(int),
        Min=pd.to_numeric(df["Min"], errors="coerce").fillna(0).astype(int),
    )

    # 1. Build O(1) Fast Player Lookup Index
    lookup = {}
    for idx in range(len(df)):
        row = df.iloc[idx]
        u_name = row["Player_Unique"]
        p_name = row["Player"]
        lookup[u_name] = row
        if p_name not in lookup:
            lookup[p_name] = row
    _PLAYER_LOOKUP_INDEX = lookup

    # 2. Precompute Position Attribute Averages
    attr_cols = {
        "Finishing": "Finishing_Score",
        "Creativity": "Creativity_Score",
        "Passing": "Passing_Score",
        "Progression": "Progression_Score",
        "Defending": "Defending_Score",
        "Ball Security": "BallSecurity_Score",
        "Aerial": "Aerial_Score",
    }
    pos_avgs = {}
    for pos_key in ["DF", "MF", "FW", None]:
        sub = df[df["Pos"] == pos_key] if pos_key else df
        pos_avgs[pos_key] = {k: float(sub[v].mean()) for k, v in attr_cols.items()}
    _POSITION_AVERAGES_CACHE = pos_avgs

    # 3. Precompute Lists
    _ALL_PLAYER_NAMES_CACHE = sorted(df["Player_Unique"].tolist())

    squads = set()
    for s in df["Squad"].dropna():
        for club in str(s).split(","):
            clean_club = club.strip()
            if clean_club:
                squads.add(clean_club)
    _UNIQUE_SQUADS_CACHE = sorted(list(squads))

    _UNIQUE_NATIONS_CACHE = sorted([n for n in df["Nation_Clean"].unique() if n != "N/A"])

    _CACHED_DF = df
    return _CACHED_DF


def load_cluster_summary():
    """
    Loads and caches the cluster summary with empirical means.
    """
    global _CACHED_SUMMARY
    if _CACHED_SUMMARY is not None:
        return _CACHED_SUMMARY

    summary = pd.read_csv(SUMMARY_PATH)
    cluster_names = summary.apply(
        lambda r: CLUSTER_NAMES.get((r["Pos"], int(r["PlayingStyle_Cluster"])), f"Cluster {r['PlayingStyle_Cluster']}"),
        axis=1,
    )
    summary = summary.assign(Cluster_Name=cluster_names)
    _CACHED_SUMMARY = summary
    return _CACHED_SUMMARY


def get_player_by_name(player_name):
    """
    High-speed O(1) in-memory lookup of a single player record.
    """
    if not _PLAYER_LOOKUP_INDEX:
        load_data()
    return _PLAYER_LOOKUP_INDEX.get(player_name, None)


def get_all_player_names():
    """
    Returns list of unique display names for dropdowns and search inputs.
    """
    global _ALL_PLAYER_NAMES_CACHE
    if _ALL_PLAYER_NAMES_CACHE is None:
        load_data()
    return _ALL_PLAYER_NAMES_CACHE


def get_unique_squads():
    """
    Returns sorted list of distinct individual club names.
    """
    global _UNIQUE_SQUADS_CACHE
    if _UNIQUE_SQUADS_CACHE is None:
        load_data()
    return _UNIQUE_SQUADS_CACHE


def get_unique_competitions():
    """
    Returns sorted list of distinct European league names.
    """
    return ["Bundesliga", "La Liga", "Ligue 1", "Premier League", "Serie A"]


def get_unique_subroles():
    """
    Returns ordered list of tactical sub-roles.
    """
    return [
        "Center-Back",
        "Full-Back / Wing-Back",
        "Defensive Midfielder",
        "Central Midfielder",
        "Attacking Midfielder",
        "Center Forward",
        "Winger",
    ]


def get_unique_nations():
    """
    Returns sorted list of unique clean nations.
    """
    global _UNIQUE_NATIONS_CACHE
    if _UNIQUE_NATIONS_CACHE is None:
        load_data()
    return _UNIQUE_NATIONS_CACHE


def get_position_averages(pos=None):
    """
    Returns precomputed mean attribute scores for players in a specific position (or all players).
    """
    if not _POSITION_AVERAGES_CACHE:
        load_data()
    return _POSITION_AVERAGES_CACHE.get(pos, _POSITION_AVERAGES_CACHE.get(None, {}))
