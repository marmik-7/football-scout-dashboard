"""
SCOUT Recruitment Intelligence — Player Tactical & Recruitment Analysis
Generates role-tailored strengths/weaknesses, evidence-based recruitment suitability
assessments, and contextual scouting summaries.
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

from app.utils.data_loader import load_data, get_position_averages, get_player_by_name
from app.utils.styling import ATTRIBUTE_COLUMNS
from app.utils.metric_definitions import (
    ROLE_EVALUATION_ATTRIBUTES,
    SAMPLE_SIZE_THRESHOLD,
    get_metric_info,
)


def get_player_strengths_and_weaknesses(player_series) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Identifies top strengths and developmental areas grounded in the player's
    tactical sub-role requirements, sample size, and verified statistical percentiles.
    """
    if player_series is None:
        return [], []

    subrole = player_series.get("SubRole", "Tactical Specialist")
    pos = player_series.get("Pos", "MF")
    minutes = float(player_series.get("Min", 0))
    is_limited_sample = minutes < SAMPLE_SIZE_THRESHOLD

    # Determine role-relevant attributes
    eval_attrs = ROLE_EVALUATION_ATTRIBUTES.get(
        subrole,
        ["Passing", "Progression", "Defending", "Ball Security", "Creativity"]
    )

    # Calculate percentile scores for role-relevant attributes
    role_scores = []
    for attr in eval_attrs:
        col = ATTRIBUTE_COLUMNS.get(attr)
        if col and col in player_series:
            role_scores.append((attr, float(player_series[col])))

    # Sort role attributes descending
    role_scores.sort(key=lambda x: x[1], reverse=True)

    strengths: List[Dict[str, Any]] = []
    weaknesses: List[Dict[str, Any]] = []

    # 1. Primary role attribute strengths (top attributes >= 55th percentile)
    for attr, score in role_scores:
        if score >= 75:
            strengths.append({
                "attribute": attr,
                "score": score,
                "level": "Elite" if score >= 85 else "Above Average",
                "scout_note": f"Key role asset: {score:.1f}th percentile among peer cohort.",
                "is_limited_sample": is_limited_sample,
            })
        elif score >= 55 and len(strengths) < 2:
            strengths.append({
                "attribute": attr,
                "score": score,
                "level": "Solid",
                "scout_note": f"Dependable foundation: {score:.1f}th percentile.",
                "is_limited_sample": is_limited_sample,
            })

    # If no role attributes exceeded 55th, pick highest role attribute
    if not strengths and role_scores:
        top_attr, top_score = role_scores[0]
        strengths.append({
            "attribute": top_attr,
            "score": top_score,
            "level": "Relative Strength",
            "scout_note": f"Strongest role trait at {top_score:.1f}th percentile.",
            "is_limited_sample": is_limited_sample,
        })

    # 2. Key granular statistical strengths
    g_xg = float(player_series.get("G-xG", 0.0))
    npxg_sh = float(player_series.get("npxG/Sh", 0.0))
    won_pct = float(player_series.get("Won%", 0.0))
    cmp_pct = float(player_series.get("Cmp%", 0.0))
    padj_tkl = float(player_series.get("Tkl_pAdj_per90", 0.0))

    if pos in ["FW", "MF"] and g_xg >= 2.0:
        strengths.append({
            "attribute": "Clinical Finishing",
            "score": 90.0,
            "level": "Outperformer",
            "scout_note": f"Clinical finishing variance: +{g_xg:.2f} goals over xG model.",
            "is_limited_sample": is_limited_sample,
        })
    elif pos == "FW" and npxg_sh >= 0.16:
        strengths.append({
            "attribute": "Shot Quality Discipline",
            "score": 85.0,
            "level": "High Efficiency",
            "scout_note": f"High probability shooting: {npxg_sh:.2f} npxG per attempt.",
            "is_limited_sample": is_limited_sample,
        })

    if won_pct >= 62.0 and "Aerial" in eval_attrs:
        if not any(s["attribute"] == "Aerial" for s in strengths):
            strengths.append({
                "attribute": "Aerial Duel Dominance",
                "score": won_pct,
                "level": "Physical Asset",
                "scout_note": f"Dominant in contested aerials ({won_pct:.1f}% win rate).",
                "is_limited_sample": is_limited_sample,
            })

    # 3. Role-specific developmental areas (only evaluate attributes expected for the role)
    for attr, score in reversed(role_scores):
        if score <= 40:
            weaknesses.append({
                "attribute": attr,
                "score": score,
                "level": "Priority Development" if score <= 25 else "Below Cohort Avg",
                "scout_note": f"Under-indexes role expectation ({score:.1f}th percentile). Verify via match footage.",
                "is_limited_sample": is_limited_sample,
            })
        if len(weaknesses) >= 2:
            break

    # If no role attributes were <= 40, check lowest role attribute if <= 50
    if not weaknesses and role_scores and role_scores[-1][1] <= 50:
        low_attr, low_score = role_scores[-1]
        weaknesses.append({
            "attribute": low_attr,
            "score": low_score,
            "level": "Monitor Area",
            "scout_note": f"Lowest role metric at {low_score:.1f}th percentile.",
            "is_limited_sample": is_limited_sample,
        })

    # Limit to top 3 strengths and top 2 development areas
    return strengths[:3], weaknesses[:2]


def get_recruitment_suitability_assessment(player_series) -> Dict[str, Any]:
    """
    Produces a cautious, evidence-based recruitment assessment identifying
    statistical attractions, scouting watch-outs, and concrete video/live verification steps.
    Never presents a definitive transfer recommendation.
    """
    if player_series is None:
        return {}

    name = player_series.get("Player", "Target")
    pos = player_series.get("Pos", "MF")
    subrole = player_series.get("SubRole", "Specialist")
    club = player_series.get("Squad", "Club")
    league = player_series.get("Comp_Clean", "Big 5")
    age = int(player_series.get("Age", 25))
    minutes = float(player_series.get("Min", 0))

    is_limited = minutes < SAMPLE_SIZE_THRESHOLD
    matches = minutes / 90.0

    attractions: List[str] = []
    concerns: List[str] = []
    scouting_actions: List[str] = []

    # Evaluate Sample Size & Age
    if is_limited:
        concerns.append(
            f"Limited Sample Size: {int(minutes)} minutes logged (~{matches:.1f} full 90s). Below the 900-minute threshold; statistical rates carry elevated volatility."
        )
    else:
        attractions.append(
            f"Established Volume: {int(minutes):,} minutes (~{matches:.1f} matches) provides a stable statistical sample for baseline evaluation."
        )

    if age <= 21:
        attractions.append(
            f"Youth & Development Trajectory: Age {age} allows substantial physical and tactical runway for progression in a development setup."
        )
    elif age >= 31:
        concerns.append(
            f"Age Horizon: Age {age} represents a veteran profile. Short contractual amortisation horizon; monitor physical recovery and athletic decline."
        )

    # Evaluate Key Positional & Role Metrics
    g_xg = float(player_series.get("G-xG", 0.0))
    npxg_sh = float(player_series.get("npxG/Sh", 0.0))
    prgp = float(player_series.get("PrgP_per90", 0.0))
    prgc = float(player_series.get("PrgC_per90", 0.0))
    cmp_pct = float(player_series.get("Cmp%", 0.0))
    tkl_padj = float(player_series.get("Tkl_pAdj_per90", 0.0))
    won_pct = float(player_series.get("Won%", 0.0))
    mis = float(player_series.get("Mis_per90", 0.0))
    dis = float(player_series.get("Dis_per90", 0.0))

    # Attractions based on elite traits
    if pos in ["FW", "MF"] and g_xg >= 2.5:
        attractions.append(
            f"Finishing Overperformance: Generated +{g_xg:.2f} goals above xG. Displays sharp finishing instincts and confidence in front of goal."
        )
        concerns.append(
            f"Overperformance Regression Risk: +{g_xg:.2f} G-xG differential is historically difficult to sustain over multiple seasons. Expect underlying scoring rate to track xG."
        )
    elif pos in ["FW", "MF"] and g_xg <= -2.0:
        concerns.append(
            f"Cold Finishing Output: Scored {abs(g_xg):.2f} goals below expected model ({player_series.get('Gls', 0)} goals from {player_series.get('xG', 0.0):.2f} xG). Review shot placement and confidence under match pressure."
        )

    if prgp >= 6.0:
        attractions.append(
            f"High-Volume Line Breaking: Produces {prgp:.1f} progressive passes per 90, consistently advancing play through opposition midfield blocks."
        )

    if prgc >= 3.0:
        attractions.append(
            f"Dynamic Ball Carrying: Generates {prgc:.1f} progressive carries per 90, demonstrating capacity to relieve defensive pressure and drive into open territory."
        )

    if pos == "DF" and won_pct >= 65.0:
        attractions.append(
            f"Aerial Solidity: Wins {won_pct:.1f}% of aerial duels, providing backline security on defensive crosses and attacking set-pieces."
        )
    elif pos == "DF" and won_pct <= 45.0:
        concerns.append(
            f"Aerial Vulnerability: Wins only {won_pct:.1f}% of aerial duels. Could represent a target for direct, aerial-heavy opposition structures."
        )

    if (mis + dis) >= 4.5:
        concerns.append(
            f"Turnover Volume: Averages {mis:.1f} miscontrols and {dis:.1f} dispossessions per 90. Scrutinize decision-making speed in high-press congested zones."
        )

    # If attractions or concerns are empty, provide role-based defaults
    if not attractions:
        attractions.append(
            f"Solid Role Baseline: Demonstrates functional statistical contribution within {club}'s structure for {subrole} duties."
        )

    if not concerns:
        concerns.append(
            "Tactical Adaptability: Role is shaped by current team structure. Evaluate how metrics translate to differing possession phases."
        )

    # Next Scouting Steps
    scouting_actions.append(
        f"Video Phase Review: Conduct focused 5-match video scouting assessing defensive transition positioning and decision-making against top-tier opposition in {league}."
    )
    if is_limited:
        scouting_actions.append(
            "Live Match Scouting: Prioritize 2-3 full 90-minute live scouting observations to verify physical duel competitiveness and stamina over 90 minutes."
        )
    else:
        scouting_actions.append(
            "System Compatibility Screening: Compare candidate's pressing triggers, defensive shape discipline, and passing tempo against recruiting club's tactical model."
        )
    scouting_actions.append(
        "Background Due Diligence: Initiate standard recruitment vetting regarding injury durability history, squad leadership, and wage structure alignment."
    )

    return {
        "player": name,
        "subrole": subrole,
        "sample_size_status": "Limited (<900m)" if is_limited else "Qualified (≥900m)",
        "attractions": attractions[:3],
        "concerns": concerns[:3],
        "scouting_actions": scouting_actions[:3],
        "disclaimer": (
            "NOTICE: This assessment is an automated statistical synthesis of match event data. "
            "It does NOT constitute a final transfer endorsement. Final recruitment decisions must be supported "
            "by comprehensive video scouting, live in-person technical evaluation, physical and medical screening, and financial viability analysis."
        ),
    }


def generate_scouting_report(player_series) -> str:
    """
    Generates a professional data-driven scouting summary written from the perspective
    of a Chief Scout and recruitment analyst.
    """
    if player_series is None:
        return "No player data available."

    name = player_series["Player"]
    club = player_series["Squad"]
    comp = player_series.get("Comp_Clean", "Big 5")
    pos = player_series["Pos"]
    pos_full = {"DF": "Defender", "MF": "Midfielder", "FW": "Forward"}.get(pos, pos)
    subrole = player_series.get("SubRole", "Tactical Specialist")
    style = player_series.get("PlayingStyle_Name", "Tactical Specialist")
    minutes = int(player_series.get("Min", 0))

    strengths, weaknesses = get_player_strengths_and_weaknesses(player_series)
    strength_names = [f"{s['attribute']} ({s['score']:.1f}th pct)" for s in strengths]
    weakness_names = [f"{w['attribute']} ({w['score']:.1f}th pct)" for w in weaknesses]

    sample_ctx = "establishing a reliable statistical baseline" if minutes >= SAMPLE_SIZE_THRESHOLD else "representing an emerging sample requiring sample-size caution"

    summary_text = (
        f"{name} operates as a {subrole} ({pos_full}) for {club} in the {comp}, logging {minutes:,} minutes ({sample_ctx}). "
        f"Tactical clustering places them within the '{style}' archetype. "
    )

    if strength_names:
        summary_text += f"Primary role strengths relative to positional peers include {', '.join(strength_names)}. "

    if weakness_names:
        summary_text += f"Key areas for tactical monitoring or development include {', '.join(weakness_names)}. "
    else:
        summary_text += "Maintains balanced output across core role responsibilities without pronounced statistical deficits. "

    summary_text += "Final recruitment evaluation requires complementary video assessment of off-ball positioning and structural discipline."

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
