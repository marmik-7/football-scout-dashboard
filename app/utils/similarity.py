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


def find_similar_players(player_name, position_filter=None, club_filter=None, comp_filter=None, max_age=None, subrole_filter=None, top_n=10):
    """
    Finds the most statistically similar players to a reference player
    using cosine similarity on standardized attribute features.

    Parameters:
        player_name (str): The unique or standard player name.
        position_filter (str): "SAME", "ALL", "DF", "MF", or "FW".
        club_filter (str): Optional club name to filter candidates.
        comp_filter (str): Optional league name (e.g. "Premier League") to filter candidates.
        max_age (int/str): Optional max age threshold for youth/succession planning.
        subrole_filter (str): Optional tactical sub-role (e.g. "Center-Back", "Winger").
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

    # Optional club filter (supports multi-club transfer records)
    if club_filter and str(club_filter).strip() and club_filter != "ALL":
        candidates = candidates[candidates["Squad"].apply(lambda s: club_filter in [c.strip() for c in str(s).split(",")])]

    # Optional competition / league filter
    if comp_filter and str(comp_filter).strip() and comp_filter != "ALL":
        candidates = candidates[candidates["Comp_Clean"].apply(lambda c: comp_filter in [x.strip() for x in str(c).split(",")])]

    # Optional max age filter (succession recruitment)
    if max_age and str(max_age).strip() and max_age != "ALL":
        try:
            m_age = int(max_age)
            candidates = candidates[(candidates["Age"] > 0) & (candidates["Age"] <= m_age)]
        except (ValueError, TypeError):
            pass

    # Optional tactical sub-role filter
    if subrole_filter and str(subrole_filter).strip() and subrole_filter != "ALL":
        candidates = candidates[candidates["SubRole"] == subrole_filter]

    if candidates.empty:
        return pd.DataFrame()

    # Sort descending by similarity
    results = candidates.sort_values("Similarity_Score", ascending=False).head(top_n).copy()

    # Scale similarity score to intuitive percentage (0 to 100%)
    # Similarity_Score is Pearson correlation r in [-1, 1] on standardized attributes.
    # Positive correlation scales linearly to 0–100%; negative or zero correlation represents 0% match.
    results["Similarity_Pct"] = results["Similarity_Score"].apply(
        lambda s: max(0.0, min(100.0, float(s) * 100.0))
    )

    return results


def explain_similarity(ref_player, candidate_player) -> dict:
    """
    Deconstructs statistical similarity between a reference benchmark and candidate player.
    Distinguishes statistical similarity, positional compatibility, tactical suitability,
    and recruitment suitability as separate, structured concepts.
    """
    if ref_player is None or candidate_player is None:
        return {}

    ref_name = ref_player.get("Player", "Benchmark")
    cand_name = candidate_player.get("Player", "Candidate")
    ref_subrole = ref_player.get("SubRole", "Specialist")
    cand_subrole = candidate_player.get("SubRole", "Specialist")
    ref_pos = ref_player.get("Pos", "MF")
    cand_pos = candidate_player.get("Pos", "MF")
    ref_age = int(ref_player.get("Age", 25))
    cand_age = int(candidate_player.get("Age", 25))
    cand_mins = float(candidate_player.get("Min", 0))

    # 1. Positional & Tactical Compatibility
    if ref_subrole == cand_subrole:
        pos_compat = f"Direct Role Match ({cand_subrole})"
        pos_compat_level = "Direct"
    elif ref_pos == cand_pos:
        pos_compat = f"Same Unit ({cand_pos}), Variant Role ({cand_subrole} vs {ref_subrole})"
        pos_compat_level = "Adjacent"
    else:
        pos_compat = f"Cross-Position Transition ({ref_pos} → {cand_pos})"
        pos_compat_level = "Transitional"

    # 2. Attribute Differences and Shared Strengths
    diffs = []
    for attr, col in ATTRIBUTE_COLUMNS.items():
        ref_val = float(ref_player.get(col, 50.0))
        cand_val = float(candidate_player.get(col, 50.0))
        delta = cand_val - ref_val
        abs_delta = abs(delta)
        diffs.append({
            "attribute": attr,
            "ref_val": ref_val,
            "cand_val": cand_val,
            "delta": delta,
            "abs_delta": abs_delta,
        })

    # Smallest absolute difference = Shared Core Strengths
    diffs_sorted_asc = sorted(diffs, key=lambda x: x["abs_delta"])
    shared_strengths = []
    for d in diffs_sorted_asc:
        if d["abs_delta"] <= 14.0 or (d["ref_val"] >= 65 and d["cand_val"] >= 65):
            shared_strengths.append(
                f"{d['attribute']} (Candidate: {d['cand_val']:.1f}th pct vs Ref: {d['ref_val']:.1f}th pct, Δ {d['delta']:+.1f})"
            )
        if len(shared_strengths) >= 3:
            break

    if not shared_strengths and diffs_sorted_asc:
        top_match = diffs_sorted_asc[0]
        shared_strengths.append(
            f"{top_match['attribute']} (Candidate: {top_match['cand_val']:.1f} vs Ref: {top_match['ref_val']:.1f})"
        )

    # Largest absolute difference = Key Tactical Differences
    diffs_sorted_desc = sorted(diffs, key=lambda x: x["abs_delta"], reverse=True)
    key_differences = []
    for d in diffs_sorted_desc:
        if d["abs_delta"] >= 8.0:
            if d["delta"] > 0:
                key_differences.append(
                    f"{d['attribute']}: Candidate leads by +{d['delta']:.1f} pct ({d['cand_val']:.1f} vs {d['ref_val']:.1f})"
                )
            else:
                key_differences.append(
                    f"{d['attribute']}: Benchmark leads by +{abs(d['delta']):.1f} pct ({d['ref_val']:.1f} vs {d['cand_val']:.1f})"
                )
        if len(key_differences) >= 3:
            break

    if not key_differences:
        key_differences.append("Extremely tight profile match with negligible variance across all 7 dimensions.")

    # 3. Succession & Age Runway
    age_delta = cand_age - ref_age
    if age_delta < 0:
        succession_note = f"{abs(age_delta)} years younger ({cand_age} vs {ref_age}) — High-value developmental succession target."
    elif age_delta > 0:
        succession_note = f"{age_delta} years older ({cand_age} vs {ref_age}) — Experienced alternative profile."
    else:
        succession_note = f"Same age ({cand_age}) — Direct lateral peer replacement."

    # 4. Sample Size Status
    is_limited = cand_mins < 900
    sample_status = f"Limited Sample ({int(cand_mins)}m)" if is_limited else f"Established Volume ({int(cand_mins):,}m)"

    return {
        "candidate": cand_name,
        "reference": ref_name,
        "positional_compatibility": pos_compat,
        "positional_compat_level": pos_compat_level,
        "shared_strengths": shared_strengths,
        "key_differences": key_differences,
        "succession_note": succession_note,
        "sample_size_status": sample_status,
        "is_limited_sample": is_limited,
        "tactical_disclaimer": "Notice: Statistical similarity models numerical event volume, not tactical interchangeability. Video scouting and physical screening required.",
    }

