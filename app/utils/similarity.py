import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

from app.utils.data_loader import load_data, get_player_by_name
from app.utils.styling import ATTRIBUTE_COLUMNS

SIMILARITY_FEATURES = list(ATTRIBUTE_COLUMNS.values())

# Cached scaled matrices and index maps
_SCALED_MATRICES = {}
_OVERALL_SCALED = None


def _init_similarity_cache():
    """
    Initializes and caches position-wise and overall standard scalers.
    """
    global _SCALED_MATRICES, _OVERALL_SCALED
    if _SCALED_MATRICES:
        return

    df = load_data()

    # Position-wise scaling (primary analytical approach from Notebook 05)
    for pos in ["DF", "MF", "FW"]:
        sub_df = df[df["Pos"] == pos]
        scaler = StandardScaler()
        mat = scaler.fit_transform(sub_df[SIMILARITY_FEATURES].values)
        _SCALED_MATRICES[pos] = {
            "indices": sub_df.index.tolist(),
            "matrix": mat,
            "scaler": scaler,
        }

    # Cross-position scaling for exploratory cross-position search
    overall_scaler = StandardScaler()
    _OVERALL_SCALED = {
        "indices": df.index.tolist(),
        "matrix": overall_scaler.fit_transform(df[SIMILARITY_FEATURES].values),
        "scaler": overall_scaler,
    }


def find_similar_players(player_name, position_filter=None, club_filter=None, top_n=10):
    """
    Finds the most statistically similar players to a reference player
    using cosine similarity on standardized attribute features.

    Parameters:
        player_name (str): The unique or standard player name.
        position_filter (str): "SAME", "ALL", "DF", "MF", or "FW".
        club_filter (str): Optional club name to filter candidates.
        top_n (int): Number of similar players to retrieve.

    Returns:
        pd.DataFrame: Top similar players with similarity score and attributes.
    """
    _init_similarity_cache()
    df = load_data()

    ref_player = get_player_by_name(player_name)
    if ref_player is None:
        return pd.DataFrame()

    ref_idx = ref_player.name
    ref_pos = ref_player["Pos"]

    # Determine whether to use position-specific or cross-position scaling
    target_pos = position_filter
    if target_pos in [None, "SAME", ref_pos]:
        cache = _SCALED_MATRICES[ref_pos]
        pos_indices = cache["indices"]
        pos_matrix = cache["matrix"]

        ref_local_idx = pos_indices.index(ref_idx)
        ref_vec = pos_matrix[ref_local_idx : ref_local_idx + 1]

        sims = cosine_similarity(ref_vec, pos_matrix)[0]

        candidates = df.loc[pos_indices].copy()
        candidates["Similarity_Score"] = sims
    else:
        # Cross-position search
        cache = _OVERALL_SCALED
        all_indices = cache["indices"]
        all_matrix = cache["matrix"]

        ref_vec = all_matrix[ref_idx : ref_idx + 1]
        sims = cosine_similarity(ref_vec, all_matrix)[0]

        candidates = df.copy()
        candidates["Similarity_Score"] = sims

        if target_pos in ["DF", "MF", "FW"]:
            candidates = candidates[candidates["Pos"] == target_pos]

    # Exclude the reference player itself
    candidates = candidates[candidates.index != ref_idx]

    # Optional club filter
    if club_filter and str(club_filter).strip() and club_filter != "ALL":
        candidates = candidates[candidates["Squad"] == club_filter]

    if candidates.empty:
        return pd.DataFrame()

    # Sort descending by similarity
    results = candidates.sort_values("Similarity_Score", ascending=False).head(top_n).copy()

    # Scale similarity score to intuitive percentage (0 to 100%)
    # Cosine similarity of standardized vectors can be negative, so map smoothly:
    # Most close players have cosine similarity between 0.70 and 0.99
    results["Similarity_Pct"] = results["Similarity_Score"].apply(
        lambda s: max(0.0, min(100.0, ((s + 1.0) / 2.0) * 100.0))
    )

    return results
