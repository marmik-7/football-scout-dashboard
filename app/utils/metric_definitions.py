"""
SCOUT Recruitment Intelligence — Metric Definitions & Role Taxonomy
Provides scout-friendly translations, analyst depth metadata, role-tailored
metric priorities, and sample-size qualification utilities.
"""

from typing import Dict, Any, List, Optional
import dash_mantine_components as dmc
from dash import html

# Minimum sample size threshold (in minutes) for reliable statistical rate modeling
SAMPLE_SIZE_THRESHOLD = 900

METRIC_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    # ─── FINISHING & SCORING ───
    "Gls": {
        "technical_name": "Goals",
        "scout_name": "Total Goals",
        "category": "Finishing & Scoring",
        "description": "Total non-shootout goals scored in league competition.",
        "why_it_matters": "Direct goal scoring volume.",
        "tier": "scout",
        "unit": "goals",
    },
    "Gls_per90": {
        "technical_name": "Gls / 90",
        "scout_name": "Goals per 90",
        "category": "Finishing & Scoring",
        "description": "Standardized rate of goals scored per 90 minutes of pitch time.",
        "why_it_matters": "Primary scoring efficiency metric normalized for playing time.",
        "tier": "scout",
        "unit": "goals/90",
    },
    "xG": {
        "technical_name": "Expected Goals (xG)",
        "scout_name": "Expected Goals (xG)",
        "category": "Finishing & Scoring",
        "description": "Cumulative probability of shots resulting in goals based on historical shot models.",
        "why_it_matters": "Underlying scoring threat independent of luck or goalkeeper quality.",
        "tier": "scout",
        "unit": "xG",
    },
    "xG_per90": {
        "technical_name": "xG / 90",
        "scout_name": "Expected Goals (xG) / 90",
        "category": "Finishing & Scoring",
        "description": "Expected goals generated per 90 minutes played.",
        "why_it_matters": "Evaluates whether a player consistently gets into high-probability scoring positions.",
        "tier": "scout",
        "unit": "xG/90",
    },
    "G-xG": {
        "technical_name": "Finishing Variance (G - xG)",
        "scout_name": "Finishing Over/Underperformance",
        "category": "Finishing & Scoring",
        "description": "Actual goals minus expected goals. Positive indicates clinical finishing; negative indicates wastefulness or bad luck.",
        "why_it_matters": "Identifies outlier overperformers who may regress, or clinical finishers who consistently beat shot models.",
        "tier": "analyst",
        "unit": "goals",
    },
    "npxG/Sh": {
        "technical_name": "npxG / Shot",
        "scout_name": "Shot Quality (npxG/Shot)",
        "category": "Finishing & Scoring",
        "description": "Average expected goal probability per non-penalty shot attempt.",
        "why_it_matters": "Measures shot selection discipline. Separates speculative long-range shooters from disciplined box finishers.",
        "tier": "analyst",
        "unit": "xG/shot",
    },
    "Sh_per90": {
        "technical_name": "Shots / 90",
        "scout_name": "Shot Attempts / 90",
        "category": "Finishing & Scoring",
        "description": "Total shot attempts per 90 minutes.",
        "why_it_matters": "Indicates shooting volume and attacking aggression.",
        "tier": "scout",
        "unit": "shots/90",
    },
    "SoT_per90": {
        "technical_name": "Shots on Target / 90",
        "scout_name": "Shots on Target / 90",
        "category": "Finishing & Scoring",
        "description": "Accurate shots on target per 90 minutes.",
        "why_it_matters": "Evaluates shot accuracy and direct work demanded of the opposition goalkeeper.",
        "tier": "scout",
        "unit": "sot/90",
    },
    "SoT%": {
        "technical_name": "SoT%",
        "scout_name": "Shot Accuracy %",
        "category": "Finishing & Scoring",
        "description": "Percentage of total shots that hit the target.",
        "why_it_matters": "Basic indicator of shooting accuracy.",
        "tier": "scout",
        "unit": "%",
    },

    # ─── CREATION & PLAYMAKING ───
    "Ast": {
        "technical_name": "Assists",
        "scout_name": "Assists",
        "category": "Creation & Playmaking",
        "description": "Total final passes leading directly to a goal.",
        "why_it_matters": "Raw creation output leading to goals.",
        "tier": "scout",
        "unit": "assists",
    },
    "Ast_per90": {
        "technical_name": "Ast / 90",
        "scout_name": "Assists per 90",
        "category": "Creation & Playmaking",
        "description": "Goal-assisting passes per 90 minutes.",
        "why_it_matters": "Time-normalized assist rate.",
        "tier": "scout",
        "unit": "assists/90",
    },
    "xA": {
        "technical_name": "Expected Assists (xA)",
        "scout_name": "Expected Assists (xA)",
        "category": "Creation & Playmaking",
        "description": "Probability that a completed pass becomes a goal assist, regardless of teammate finishing.",
        "why_it_matters": "Reflects true chance-creation quality without being penalized by poor finishing from teammates.",
        "tier": "scout",
        "unit": "xA",
    },
    "xA_per90": {
        "technical_name": "xA / 90",
        "scout_name": "Expected Assists (xA) / 90",
        "category": "Creation & Playmaking",
        "description": "Expected assists generated per 90 minutes.",
        "why_it_matters": "Underlying creative delivery rate.",
        "tier": "scout",
        "unit": "xA/90",
    },
    "KP_per90": {
        "technical_name": "Key Passes / 90",
        "scout_name": "Chances Created / 90",
        "category": "Creation & Playmaking",
        "description": "Passes directly leading to a teammate shot attempt per 90 minutes.",
        "why_it_matters": "Volume of shooting opportunities created for teammates.",
        "tier": "scout",
        "unit": "passes/90",
    },
    "SCA_per90": {
        "technical_name": "SCA / 90",
        "scout_name": "Shot-Creating Actions / 90",
        "category": "Creation & Playmaking",
        "description": "Two offensive actions leading directly to a shot (passes, dribbles, fouls drawn).",
        "why_it_matters": "Holistic playmaking contribution beyond the final pass.",
        "tier": "scout",
        "unit": "actions/90",
    },
    "GCA_per90": {
        "technical_name": "GCA / 90",
        "scout_name": "Goal-Creating Actions / 90",
        "category": "Creation & Playmaking",
        "description": "Two offensive actions directly leading to a goal.",
        "why_it_matters": "High-impact playmaking that decisively breaks defenses.",
        "tier": "analyst",
        "unit": "actions/90",
    },

    # ─── PASSING & BALL PROGRESSION ───
    "Cmp%": {
        "technical_name": "Pass Completion %",
        "scout_name": "Passing Accuracy %",
        "category": "Passing & Progression",
        "description": "Percentage of attempted passes successfully completed to a teammate.",
        "why_it_matters": "General ball retention and passing reliability. Contextualize with passing difficulty.",
        "tier": "scout",
        "unit": "%",
    },
    "PrgP_per90": {
        "technical_name": "PrgP / 90",
        "scout_name": "Progressive Passes / 90",
        "category": "Passing & Progression",
        "description": "Completed passes that move the ball at least 10 yards closer to the opponent's goal or into the penalty box.",
        "why_it_matters": "The primary indicator of line-breaking passing capability and forward momentum generation.",
        "tier": "scout",
        "unit": "passes/90",
    },
    "PrgC_per90": {
        "technical_name": "PrgC / 90",
        "scout_name": "Progressive Carries / 90",
        "category": "Passing & Progression",
        "description": "Carries that advance the ball at least 10 yards towards the opponent goal or into the penalty area.",
        "why_it_matters": "Measures ability to break opposition defensive lines via ball-carrying and driving forward.",
        "tier": "scout",
        "unit": "carries/90",
    },
    "PrgDist_per90": {
        "technical_name": "PrgDist / 90",
        "scout_name": "Progressive Pass Distance / 90",
        "category": "Passing & Progression",
        "description": "Total yards advanced toward the opponent goal via completed forward passes per 90.",
        "why_it_matters": "Measures verticality and range of forward passing distribution.",
        "tier": "analyst",
        "unit": "yards/90",
    },
    "TB_per90": {
        "technical_name": "Through Balls / 90",
        "scout_name": "Through Balls / 90",
        "category": "Passing & Progression",
        "description": "Completed passes sent between backline defenders into open space per 90.",
        "why_it_matters": "Elite technical vision and defense-unlocking pass execution.",
        "tier": "analyst",
        "unit": "passes/90",
    },
    "Sw_per90": {
        "technical_name": "Switches / 90",
        "scout_name": "Field Switches / 90",
        "category": "Passing & Progression",
        "description": "Long passes traveling more than 40 yards across the pitch width.",
        "why_it_matters": "Ability to shift the point of attack and exploit weak-side defensive overload.",
        "tier": "analyst",
        "unit": "switches/90",
    },
    "PPA_per90": {
        "technical_name": "PPA / 90",
        "scout_name": "Passes into Penalty Area / 90",
        "category": "Passing & Progression",
        "description": "Completed passes into the 18-yard box per 90 minutes (excluding set-pieces).",
        "why_it_matters": "Measures final-third penetration and service into the dangerous penalty box.",
        "tier": "scout",
        "unit": "passes/90",
    },
    "CPA_per90": {
        "technical_name": "CPA / 90",
        "scout_name": "Carries into Penalty Area / 90",
        "category": "Passing & Progression",
        "description": "Carries entering the opposition 18-yard box per 90.",
        "why_it_matters": "Direct box penetration via dribbling and 1v1 threat.",
        "tier": "scout",
        "unit": "carries/90",
    },
    "Succ_per90": {
        "technical_name": "Take-Ons Won / 90",
        "scout_name": "Successful Dribbles / 90",
        "category": "Passing & Progression",
        "description": "Successful dribbles past an opposing player per 90 minutes.",
        "why_it_matters": "1v1 isolation ability and press resistance.",
        "tier": "scout",
        "unit": "dribbles/90",
    },

    # ─── DEFENDING & BALL RECOVERY ───
    "Tkl_pAdj_per90": {
        "technical_name": "pAdj Tackles / 90",
        "scout_name": "Possession-Adjusted Tackles / 90",
        "category": "Defending & Recovery",
        "description": "Tackles standardized to a 50% possession baseline using the team possession factor.",
        "why_it_matters": "Prevents penalizing defenders who play in dominant, high-possession teams with fewer defensive opportunities.",
        "tier": "analyst",
        "unit": "tackles/90",
    },
    "Int_pAdj_per90": {
        "technical_name": "pAdj Interceptions / 90",
        "scout_name": "Possession-Adjusted Interceptions / 90",
        "category": "Defending & Recovery",
        "description": "Interceptions adjusted to a 50% possession baseline.",
        "why_it_matters": "Measures anticipation and lane-reading without possession team bias.",
        "tier": "analyst",
        "unit": "interceptions/90",
    },
    "Clr_pAdj_per90": {
        "technical_name": "pAdj Clearances / 90",
        "scout_name": "Possession-Adjusted Clearances / 90",
        "category": "Defending & Recovery",
        "description": "Clearances adjusted to a 50% possession baseline.",
        "why_it_matters": "Box-defending emergency volume normalized across possession structures.",
        "tier": "analyst",
        "unit": "clearances/90",
    },
    "Tkl_per90": {
        "technical_name": "Tackles / 90",
        "scout_name": "Tackles / 90",
        "category": "Defending & Recovery",
        "description": "Raw unadjusted tackles per 90 minutes.",
        "why_it_matters": "Actual match volume of tackling duels engaged.",
        "tier": "scout",
        "unit": "tackles/90",
    },
    "Int_per90": {
        "technical_name": "Interceptions / 90",
        "scout_name": "Interceptions / 90",
        "category": "Defending & Recovery",
        "description": "Raw unadjusted interceptions per 90 minutes.",
        "why_it_matters": "Actual match volume of passing lanes cut.",
        "tier": "scout",
        "unit": "interceptions/90",
    },
    "Clr_per90": {
        "technical_name": "Clearances / 90",
        "scout_name": "Clearances / 90",
        "category": "Defending & Recovery",
        "description": "Defensive clearances per 90 minutes.",
        "why_it_matters": "Frequency of clearing immediate box danger.",
        "tier": "scout",
        "unit": "clearances/90",
    },
    "Recov_per90": {
        "technical_name": "Recoveries / 90",
        "scout_name": "Loose Ball Recoveries / 90",
        "category": "Defending & Recovery",
        "description": "Loose balls recovered per 90 minutes.",
        "why_it_matters": "Second-ball winning and defensive positioning.",
        "tier": "scout",
        "unit": "recoveries/90",
    },
    "pAdj_Factor": {
        "technical_name": "pAdj Factor",
        "scout_name": "Possession Adjustment Factor",
        "category": "Defending & Recovery",
        "description": "Multiplier calculated as 2 / (1 + exp(-0.1 * (opp_poss - 50))), adjusting stats to a neutral 50% possession baseline.",
        "why_it_matters": "Mathematical adjustment factor applied to all defensive volume metrics.",
        "tier": "analyst",
        "unit": "factor",
    },

    # ─── AERIAL & PHYSICALITY ───
    "Won%": {
        "technical_name": "Aerial Win %",
        "scout_name": "Aerial Duel Win Rate %",
        "category": "Aerial & Physicality",
        "description": "Percentage of aerial duels won when contested.",
        "why_it_matters": "Direct measure of aerial dominance and physical duel effectiveness.",
        "tier": "scout",
        "unit": "%",
    },
    "Won_per90": {
        "technical_name": "Aerials Won / 90",
        "scout_name": "Aerial Duels Won / 90",
        "category": "Aerial & Physicality",
        "description": "Total aerial duels won per 90 minutes.",
        "why_it_matters": "Volume of aerial contests won on the pitch.",
        "tier": "scout",
        "unit": "duels/90",
    },

    # ─── BALL RETENTION & SECURITY ───
    "Mis_per90": {
        "technical_name": "Miscontrols / 90",
        "scout_name": "Miscontrols / 90 (Lower is Better)",
        "category": "Ball Security",
        "description": "Times player failed when attempting to control the ball per 90.",
        "why_it_matters": "Technical touch reliability and ball security under pressure.",
        "tier": "analyst",
        "unit": "turnovers/90",
    },
    "Dis_per90": {
        "technical_name": "Dispossessed / 90",
        "scout_name": "Dispossessed / 90 (Lower is Better)",
        "category": "Ball Security",
        "description": "Times player was tackled away by opponent without attempting a dribble per 90.",
        "why_it_matters": "Resistance to counter-pressing and ball retention under pressure.",
        "tier": "analyst",
        "unit": "turnovers/90",
    },
}

# ─── ROLE-SPECIFIC PRIMARY METRICS FOR SCOUT VIEW ───
# Defines the 6 most relevant match production metrics for each tactical role
ROLE_PRIMARY_METRICS: Dict[str, List[str]] = {
    "Center Forward": [
        "Gls_per90",
        "xG_per90",
        "G-xG",
        "npxG/Sh",
        "SCA_per90",
        "Won%",
    ],
    "Winger": [
        "Gls_per90",
        "xG_per90",
        "PrgC_per90",
        "KP_per90",
        "SCA_per90",
        "Ast_per90",
    ],
    "Attacking Midfielder": [
        "KP_per90",
        "xA_per90",
        "SCA_per90",
        "PrgP_per90",
        "Gls_per90",
        "Cmp%",
    ],
    "Central Midfielder": [
        "PrgP_per90",
        "PrgC_per90",
        "Cmp%",
        "KP_per90",
        "Tkl_pAdj_per90",
        "Int_pAdj_per90",
    ],
    "Defensive Midfielder": [
        "Tkl_pAdj_per90",
        "Int_pAdj_per90",
        "Cmp%",
        "PrgP_per90",
        "Won%",
        "Clr_pAdj_per90",
    ],
    "Full-Back / Wing-Back": [
        "PrgP_per90",
        "PrgC_per90",
        "KP_per90",
        "Tkl_pAdj_per90",
        "Int_pAdj_per90",
        "Cmp%",
    ],
    "Center-Back": [
        "Tkl_pAdj_per90",
        "Int_pAdj_per90",
        "Clr_pAdj_per90",
        "Won%",
        "PrgP_per90",
        "Cmp%",
    ],
}

# Fallback by primary general position if sub-role is missing or unknown
POSITION_FALLBACK_METRICS: Dict[str, List[str]] = {
    "FW": ["Gls_per90", "xG_per90", "G-xG", "npxG/Sh", "SCA_per90", "Won%"],
    "MF": ["PrgP_per90", "PrgC_per90", "Cmp%", "KP_per90", "Tkl_pAdj_per90", "Int_pAdj_per90"],
    "DF": ["Tkl_pAdj_per90", "Int_pAdj_per90", "Clr_pAdj_per90", "Won%", "PrgP_per90", "Cmp%"],
}

# Key tactical attributes relevant to each sub-role for Strengths/Weaknesses evaluation
ROLE_EVALUATION_ATTRIBUTES: Dict[str, List[str]] = {
    "Center Forward": ["Finishing", "Aerial", "Progression", "Creativity"],
    "Winger": ["Progression", "Finishing", "Creativity", "Ball Security"],
    "Attacking Midfielder": ["Creativity", "Passing", "Progression", "Finishing"],
    "Central Midfielder": ["Passing", "Progression", "Ball Security", "Defending"],
    "Defensive Midfielder": ["Defending", "Ball Security", "Passing", "Aerial"],
    "Full-Back / Wing-Back": ["Progression", "Defending", "Passing", "Creativity"],
    "Center-Back": ["Defending", "Aerial", "Passing", "Ball Security"],
}


def get_metric_info(col_name: str) -> Dict[str, Any]:
    """Retrieve full metric dictionary entry, with sensible fallbacks."""
    if col_name in METRIC_DEFINITIONS:
        return METRIC_DEFINITIONS[col_name]
    clean_name = col_name.replace("_per90", " / 90").replace("_", " ")
    return {
        "technical_name": clean_name,
        "scout_name": clean_name,
        "category": "General Performance",
        "description": f"Statistical tracking for {clean_name}.",
        "why_it_matters": "Evaluates player performance contribution.",
        "tier": "analyst",
        "unit": "",
    }


def get_metric_label(col_name: str, mode: str = "scout") -> str:
    """Return user-facing label according to view mode ('scout' or 'analyst')."""
    info = get_metric_info(col_name)
    if mode == "scout":
        return info["scout_name"]
    return info["technical_name"]


def get_metric_tooltip(col_name: str) -> str:
    """Return plain-English tooltip explanation combining definition and scouting relevance."""
    info = get_metric_info(col_name)
    return f"{info['description']} Why it matters: {info['why_it_matters']}"


def get_role_metrics(subrole: Optional[str], pos: Optional[str] = None) -> List[str]:
    """Return prioritized metrics for a player's subrole or primary position."""
    if subrole and subrole in ROLE_PRIMARY_METRICS:
        return ROLE_PRIMARY_METRICS[subrole]
    if pos and pos in POSITION_FALLBACK_METRICS:
        return POSITION_FALLBACK_METRICS[pos]
    return ROLE_PRIMARY_METRICS["Central Midfielder"]


def get_sample_size_badge(minutes: float, show_ok: bool = False) -> Optional[dmc.Badge]:
    """
    Generate a sample-size warning badge if minutes played is below threshold.
    Returns None if sample size is sufficient and show_ok is False.
    """
    mins = float(minutes) if minutes is not None else 0.0
    if mins < SAMPLE_SIZE_THRESHOLD:
        matches_equiv = mins / 90.0
        return dmc.Tooltip(
            label=f"Sample: {int(mins)} mins (~{matches_equiv:.1f} full matches). Below the 900-minute benchmark. Statistical rates carry higher short-term variance. Further live or video scouting advised.",
            multiline=True,
            w=280,
            children=dmc.Badge(
                f"Limited Sample ({int(mins)}m)",
                color="orange",
                variant="light",
                size="xs",
                style={"cursor": "help", "fontWeight": 600},
            ),
        )
    elif show_ok:
        return dmc.Badge(
            f"Qualified Sample ({int(mins)}m)",
            color="teal",
            variant="outline",
            size="xs",
            style={"opacity": 0.8},
        )
    return None
