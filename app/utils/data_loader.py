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
    ("MF", 0): "Ball-Winning Anchor",
    ("MF", 1): "Box-to-Box Threat",
    ("MF", 2): "Deep-Lying Controller",
    ("MF", 3): "Advanced Playmaker",
    ("FW", 0): "Aerial Target Man",
    ("FW", 1): "High-Pressing Winger",
    ("FW", 2): "Complete Forward",
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


def load_data():
    """
    Loads and caches the 1,692 player dataset with precomputed
    percentile scores, K-Means clusters, and PCA coordinates.
    """
    global _CACHED_DF
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

    # Batch assign to avoid DataFrame fragmentation warning
    df = df.assign(
        Nation_Clean=nation_clean,
        Nation_Display=nation_display,
        Player_Unique=player_unique,
        PlayingStyle_Name=cluster_names,
        Age=pd.to_numeric(df["Age"], errors="coerce").fillna(0).astype(int),
        Born=pd.to_numeric(df["Born"], errors="coerce").fillna(0).astype(int),
        Min=pd.to_numeric(df["Min"], errors="coerce").fillna(0).astype(int),
    )

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
    Looks up a single player by unique or standard name.
    """
    df = load_data()
    match = df[df["Player_Unique"] == player_name]
    if match.empty:
        match = df[df["Player"] == player_name]
    if match.empty:
        return None
    return match.iloc[0]


def get_all_player_names():
    """
    Returns list of unique display names for dropdowns and search inputs.
    """
    df = load_data()
    return sorted(df["Player_Unique"].tolist())


def get_unique_squads():
    """
    Returns sorted list of unique club squads.
    """
    df = load_data()
    return sorted([s for s in df["Squad"].dropna().unique() if str(s).strip()])


def get_unique_nations():
    """
    Returns sorted list of unique clean nations.
    """
    df = load_data()
    return sorted([n for n in df["Nation_Clean"].unique() if n != "N/A"])


def get_position_averages(pos=None):
    """
    Returns mean attribute scores for players in a specific position (or all players).
    """
    df = load_data()
    from app.utils.styling import ATTRIBUTE_COLUMNS

    if pos and pos in ["DF", "MF", "FW"]:
        sub_df = df[df["Pos"] == pos]
    else:
        sub_df = df

    return {k: float(sub_df[v].mean()) for k, v in ATTRIBUTE_COLUMNS.items()}
