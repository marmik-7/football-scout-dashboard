import pandas as pd
import numpy as np

from app.utils.data_loader import load_data, get_position_averages, get_player_by_name
from app.utils.styling import ATTRIBUTE_COLUMNS


def get_player_strengths_and_weaknesses(player_series):
    """
    Identifies top strengths and developmental areas based on position-relative percentiles.
    """
    if player_series is None:
        return [], []

    scores = {attr: float(player_series[col]) for attr, col in ATTRIBUTE_COLUMNS.items()}
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Top 3 attributes as strengths
    strengths = [
        {"attribute": attr, "score": score, "level": "Elite" if score >= 85 else "Strong"}
        for attr, score in sorted_scores[:3]
        if score >= 55
    ]
    if not strengths:
        # If all scores are moderate, take top 2
        strengths = [{"attribute": attr, "score": score, "level": "Above Average"} for attr, score in sorted_scores[:2]]

    # Bottom 2 attributes as developmental areas
    weaknesses = [
        {"attribute": attr, "score": score, "level": "Vulnerable" if score <= 30 else "Moderate"}
        for attr, score in sorted_scores[-2:]
        if score <= 50
    ]
    if not weaknesses:
        weaknesses = [{"attribute": attr, "score": score, "level": "Lower Priority"} for attr, score in sorted_scores[-2:]]

    return strengths, weaknesses


def generate_scouting_report(player_series):
    """
    Generates a professional data-driven scouting summary.
    """
    if player_series is None:
        return "No player data available."

    name = player_series["Player"]
    club = player_series["Squad"]
    pos = player_series["Pos"]
    pos_full = {"DF": "Defender", "MF": "Midfielder", "FW": "Forward"}.get(pos, pos)
    style = player_series.get("PlayingStyle_Name", "Specialist")
    minutes = int(player_series.get("Min", 0))

    strengths, weaknesses = get_player_strengths_and_weaknesses(player_series)
    strength_names = [f"{s['attribute']} ({s['score']:.1f})" for s in strengths]
    weakness_names = [f"{w['attribute']} ({w['score']:.1f})" for w in weaknesses]

    gls = player_series.get("Gls", 0)
    ast = player_series.get("Ast", 0)
    xg = player_series.get("xG", 0.0)
    xa = player_series.get("xA", 0.0)

    summary_text = (
        f"{name} is an active {pos_full} for {club} with {minutes:,} minutes logged during the 2024–25 campaign. "
        f"Statistical clustering identifies their tactical archetype as a '{style}'. "
    )

    if strength_names:
        summary_text += f"Key analytical strengths relative to position peers include {', '.join(strength_names)}. "

    if weakness_names:
        summary_text += f"Areas displaying lower relative volume or efficiency include {', '.join(weakness_names)}."

    return summary_text


def get_player_attribute_comparison(player_series):
    """
    Returns comparison between player's percentile scores and position peer averages.
    """
    if player_series is None:
        return []

    pos = player_series["Pos"]
    pos_avgs = get_position_averages(pos)

    comparison = []
    for attr, col in ATTRIBUTE_COLUMNS.items():
        player_score = float(player_series[col])
        pos_avg = pos_avgs.get(attr, 50.0)
        diff = player_score - pos_avg
        comparison.append({
            "attribute": attr,
            "player_score": round(player_score, 1),
            "position_avg": round(pos_avg, 1),
            "diff": round(diff, 1),
        })

    return comparison
