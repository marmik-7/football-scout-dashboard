import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from app.utils.styling import (
    PANEL,
    BORDER,
    TEXT,
    MUTED,
    ACCENT,
    POSITION_COLORS,
    CLUSTER_COLORS,
    ATTRIBUTE_COLUMNS,
    style_figure,
)

PLAYER_COMPARE_COLORS = [
    "#10B981",  # Pitch Emerald
    "#38BDF8",  # Sky Cyan
    "#F59E0B",  # Amber
    "#A855F7",  # Purple
]


def build_radar_chart(players, include_position_avg=False, position_avg_scores=None, height=380):
    """
    Builds a 7-dimensional radar chart for one or multiple players.

    Parameters:
        players (list of dict/Series): List of player data dicts or Series.
        include_position_avg (bool): Whether to overlay the position peer average.
        position_avg_scores (dict): Dict of {attribute: score} for position average.
        height (int): Figure height.
    """
    categories = list(ATTRIBUTE_COLUMNS.keys())
    # Closed loop for radar chart
    categories_closed = categories + [categories[0]]

    fig = go.Figure()

    # Optional position benchmark
    if include_position_avg and position_avg_scores:
        avg_values = [position_avg_scores.get(c, 50.0) for c in categories]
        avg_values_closed = avg_values + [avg_values[0]]
        fig.add_trace(
            go.Scatterpolar(
                r=avg_values_closed,
                theta=categories_closed,
                mode="lines",
                name="Position Peer Avg",
                line=dict(color=MUTED, width=1.8, dash="dash"),
                hoverinfo="r+theta+name",
            )
        )

    # Add each player trace
    multi_player = len(players) >= 3
    for i, p in enumerate(players):
        color = PLAYER_COMPARE_COLORS[i % len(PLAYER_COMPARE_COLORS)]
        values = [float(p[ATTRIBUTE_COLUMNS[c]]) for c in categories]
        values_closed = values + [values[0]]
        player_label = p.get("Player_Unique", p.get("Player", f"Player {i+1}"))
        fill_opacity = 0.04 if multi_player else 0.18

        fig.add_trace(
            go.Scatterpolar(
                r=values_closed,
                theta=categories_closed,
                fill="toself",
                name=player_label,
                line=dict(color=color, width=2.4),
                fillcolor=f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, {fill_opacity})",
                hovertemplate=f"<b>{player_label}</b><br>%{{theta}}: <b>%{{r:.1f}}</b><extra></extra>",
            )
        )

    fig = style_figure(fig, height=height)
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(15, 23, 42, 0.4)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                dtick=25,
                tickfont=dict(color=MUTED, size=9),
                gridcolor=BORDER,
                linecolor=BORDER,
            ),
            angularaxis=dict(
                tickfont=dict(color=TEXT, size=11),
                gridcolor=BORDER,
                linecolor=BORDER,
            ),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.22,
            xanchor="center",
            x=0.5,
            font=dict(color=TEXT, size=11),
        ),
        margin=dict(l=40, r=40, t=30, b=45),
    )
    return fig


def build_pizza_chart(player, height=400):
    """
    Builds a StatsBomb/FBref-style 12-slice percentile pizza chart (polar bar chart).
    Each wedge has a uniform angular width (26.5 deg) and radial distance equal to
    the player's position-relative percentile rank (0-100), eliminating geometric area distortion.

    Slices are partitioned into 3 color-coded tactical domains:
      - Attacking (Crimson #EF4444): Goals/90, NP xG/90, Shot Quality, Finishing (G-xG)
      - Possession & Creation (Sky Blue #0EA5E9): xA/90, Key Passes/90, Prog Passes/90, Prog Carries/90
      - Defending & Physical (Pitch Lime #84CC16): pAdj Tackles/90, pAdj Interceptions/90, pAdj Clearances/90, Aerial Win %
    """
    if player is None:
        fig = go.Figure()
        fig.add_annotation(
            text="Select a player to view the Percentile Pizza chart.",
            showarrow=False,
            font=dict(color=MUTED, size=13),
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
        )
        return style_figure(fig, height=height)

    domains = [
        {
            "domain": "Attacking",
            "color": "#EF4444",
            "metrics": [
                ("Goals / 90", "Gls_per90_pct", "Gls_per90", "{:.2f}/90"),
                ("NP xG / 90", "npxG_per90_pct", "npxG_per90", "{:.2f}/90"),
                ("Shot Quality", "npxG/Sh_pct", "npxG/Sh", "{:.2f} npxG/Sh"),
                ("Finishing (G-xG)", "G-xG_pct", "G-xG", "{:+.2f} vs xG"),
            ],
        },
        {
            "domain": "Possession & Creation",
            "color": "#0EA5E9",
            "metrics": [
                ("xAssists / 90", "xA_per90_pct", "xA_per90", "{:.2f}/90"),
                ("Key Passes / 90", "KP_per90_pct", "KP_per90", "{:.2f}/90"),
                ("Prog Passes / 90", "PrgP_per90_pct", "PrgP_per90", "{:.1f}/90"),
                ("Prog Carries / 90", "PrgC_per90_pct", "PrgC_per90", "{:.1f}/90"),
            ],
        },
        {
            "domain": "Defending (pAdj)",
            "color": "#84CC16",
            "metrics": [
                ("pAdj Tackles / 90", "Tkl_pAdj_per90_pct", "Tkl_pAdj_per90", "{:.2f}/90"),
                ("pAdj Interceptions / 90", "Int_pAdj_per90_pct", "Int_pAdj_per90", "{:.2f}/90"),
                ("pAdj Clearances / 90", "Clr_pAdj_per90_pct", "Clr_pAdj_per90", "{:.2f}/90"),
                ("Aerial Win %", "Won%_pct", "Won%", "{:.1f}%"),
            ],
        },
    ]

    fig = go.Figure()
    angles = []
    labels = []
    current_idx = 0

    for group in domains:
        g_angles = []
        g_radii = []
        g_hover = []
        dom_name = group["domain"]
        for m_label, pct_col, raw_col, fmt in group["metrics"]:
            angle = current_idx * 30
            angles.append(angle)
            labels.append(m_label)
            g_angles.append(angle)

            pct_val = max(1.0, min(100.0, float(player.get(pct_col, 50.0) or 50.0)))
            raw_val = float(player.get(raw_col, 0.0) or 0.0)
            formatted_raw = fmt.format(raw_val)

            g_radii.append(pct_val)
            g_hover.append(
                f"<b>{m_label}</b> ({dom_name})<br>"
                f"Percentile Rank: <b>{pct_val:.1f}th %tile</b><br>"
                f"Season Rate: <b>{formatted_raw}</b><extra></extra>"
            )
            current_idx += 1

        fig.add_trace(
            go.Barpolar(
                r=g_radii,
                theta=g_angles,
                width=[26.5] * len(g_radii),
                marker_color=group["color"],
                marker_line_color="#101827",
                marker_line_width=1.5,
                opacity=0.88,
                name=dom_name,
                hovertext=g_hover,
                hoverinfo="text",
            )
        )

    fig = style_figure(fig, height=height)
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(15, 23, 42, 0.4)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                dtick=25,
                tickfont=dict(color=MUTED, size=9),
                gridcolor="rgba(255, 255, 255, 0.08)",
                linecolor=BORDER,
            ),
            angularaxis=dict(
                tickmode="array",
                tickvals=angles,
                ticktext=labels,
                tickfont=dict(color=TEXT, size=9, weight=600),
                rotation=90,
                direction="clockwise",
                gridcolor="rgba(255, 255, 255, 0.08)",
                linecolor=BORDER,
            ),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.16,
            xanchor="center",
            x=0.5,
            font=dict(color=TEXT, size=10),
        ),
        margin=dict(l=40, r=40, t=30, b=35),
    )
    return fig


def build_comparison_bars(players, height=380):
    """
    Builds a grouped bar chart comparing multiple players across the 7 attributes.
    """
    categories = list(ATTRIBUTE_COLUMNS.keys())
    fig = go.Figure()

    for i, p in enumerate(players):
        color = PLAYER_COMPARE_COLORS[i % len(PLAYER_COMPARE_COLORS)]
        values = [float(p[ATTRIBUTE_COLUMNS[c]]) for c in categories]
        player_label = p.get("Player_Unique", p.get("Player", f"Player {i+1}"))

        fig.add_trace(
            go.Bar(
                x=categories,
                y=values,
                name=player_label,
                marker_color=color,
                text=[f"{v:.1f}" for v in values],
                textposition="outside",
                cliponaxis=False,
                hovertemplate=f"<b>{player_label}</b><br>%{{x}}: <b>%{{y:.1f}}</b><extra></extra>",
            )
        )

    fig = style_figure(fig, height=height)
    fig.update_layout(
        barmode="group",
        yaxis=dict(
            range=[0, 110],
            title=dict(text="Percentile Score", font=dict(color=MUTED, size=11)),
            gridcolor=BORDER,
            tickfont=dict(color=MUTED),
        ),
        xaxis=dict(
            gridcolor=BORDER,
            tickfont=dict(color=TEXT, size=11),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(color=TEXT, size=11),
        ),
        margin=dict(l=40, r=25, t=30, b=55),
    )
    return fig


def build_pca_cluster_scatter(df, pos="FW", selected_cluster="ALL", highlight_player=None, height=480):
    """
    Builds an interactive 2D PCA scatter plot colored by Playing Style clusters.
    Optionally highlights coordinates for a specific targeted player.
    """
    pos_df = df[df["Pos"] == pos].copy()

    # Create hover text
    pos_df["Hover_Text"] = pos_df.apply(
        lambda r: (
            f"<b>{r['Player']}</b> ({r['Squad']})<br>"
            f"Style: {r['PlayingStyle_Name']}<br>"
            f"Min: {r['Min']} | Age: {r['Age']}<br>"
            f"PC1: {r['PC1']:.2f} | PC2: {r['PC2']:.2f}"
        ),
        axis=1,
    )

    fig = go.Figure()

    clusters = sorted(pos_df["PlayingStyle_Cluster"].unique())

    for c in clusters:
        cluster_df = pos_df[pos_df["PlayingStyle_Cluster"] == c]
        color = CLUSTER_COLORS[int(c) % len(CLUSTER_COLORS)]
        style_name = cluster_df["PlayingStyle_Name"].iloc[0] if not cluster_df.empty else f"Cluster {c}"

        is_dimmed = selected_cluster != "ALL" and str(selected_cluster) != str(c)
        opacity = 0.15 if is_dimmed else 0.85
        size = 6 if is_dimmed else 9

        fig.add_trace(
            go.Scatter(
                x=cluster_df["PC1"],
                y=cluster_df["PC2"],
                mode="markers",
                name=style_name,
                marker=dict(
                    color=color,
                    size=size,
                    opacity=opacity,
                    line=dict(color="#101827", width=0.5),
                ),
                text=cluster_df["Hover_Text"],
                hoverinfo="text",
            )
        )

    # Optional Highlight Pin for Target Candidate
    if highlight_player and str(highlight_player).strip() != "" and highlight_player != "NONE":
        p_matches = pos_df[pos_df["Player"] == highlight_player]
        if not p_matches.empty:
            p_row = p_matches.iloc[0]
            # Outer glowing halo
            fig.add_trace(
                go.Scatter(
                    x=[p_row["PC1"]],
                    y=[p_row["PC2"]],
                    mode="markers",
                    name="Target Halo",
                    marker=dict(
                        symbol="circle",
                        color="rgba(132, 204, 22, 0.22)",
                        size=28,
                        line=dict(color="#84CC16", width=2),
                    ),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )
            # Sharp diamond pin
            fig.add_trace(
                go.Scatter(
                    x=[p_row["PC1"]],
                    y=[p_row["PC2"]],
                    mode="markers+text",
                    name=f"📍 {p_row['Player']}",
                    marker=dict(
                        symbol="diamond",
                        color="#FFFFFF",
                        size=14,
                        line=dict(color="#84CC16", width=2.5),
                    ),
                    text=[f"  <b>{p_row['Player']}</b>"],
                    textposition="top right",
                    textfont=dict(color="#FFFFFF", size=12, family="Inter, sans-serif"),
                    hoverinfo="text",
                    hovertext=(
                        f"<b>📍 LOCATED CANDIDATE: {p_row['Player']}</b><br>"
                        f"Squad: {p_row['Squad']} • Pos: {p_row['Pos']} ({p_row.get('SubRole', 'N/A')})<br>"
                        f"Style Archetype: <b>{p_row.get('PlayingStyle_Name', 'Cluster')}</b><br>"
                        f"Coordinates: PC1={p_row['PC1']:.2f}, PC2={p_row['PC2']:.2f}"
                    ),
                    showlegend=True,
                )
            )
            # Directional callout annotation
            fig.add_annotation(
                x=p_row["PC1"],
                y=p_row["PC2"],
                text=f"<b>{p_row['Player']}</b>",
                showarrow=True,
                arrowhead=2,
                arrowsize=1.0,
                arrowwidth=2,
                arrowcolor="#84CC16",
                ax=35,
                ay=-35,
                font=dict(color="#FFFFFF", size=11, family="Inter, sans-serif"),
                bgcolor="#1E293B",
                bordercolor="#84CC16",
                borderwidth=1.5,
                borderpad=4,
                opacity=0.95,
            )

    fig = style_figure(fig, height=height)
    fig.update_layout(
        title=dict(
            text=f"2D PCA Projection — {pos} Tactical Clusters",
            font=dict(color=TEXT, size=15),
            subtitle=dict(
                text="Mathematical dimensionality reduction preserving multi-dimensional distance. Clusters reflect observed feature distributions.",
                font=dict(color=MUTED, size=11),
            ),
        ),
        xaxis=dict(
            title=dict(text="Principal Component 1 (PC1) — Primary Variance Axis", font=dict(color=MUTED, size=11)),
            gridcolor=BORDER,
            zerolinecolor=BORDER,
            tickfont=dict(color=MUTED),
        ),
        yaxis=dict(
            title=dict(text="Principal Component 2 (PC2) — Secondary Variance Axis", font=dict(color=MUTED, size=11)),
            gridcolor=BORDER,
            zerolinecolor=BORDER,
            tickfont=dict(color=MUTED),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.28,
            xanchor="center",
            x=0.5,
            font=dict(color=TEXT, size=11),
        ),
        margin=dict(l=40, r=25, t=55, b=65),
    )
    return fig


def build_cluster_dna_radar(cluster_summary_df, pos="FW", height=420):
    """
    Builds an overlaid radar chart comparing the 4 tactical cluster profiles for a position.
    """
    categories = list(ATTRIBUTE_COLUMNS.keys())
    categories_closed = categories + [categories[0]]

    sub_summary = cluster_summary_df[cluster_summary_df["Pos"] == pos].sort_values("PlayingStyle_Cluster")

    fig = go.Figure()

    summary_col_map = {
        "Finishing": "Finishing",
        "Creativity": "Creativity",
        "Passing": "Passing",
        "Progression": "Progression",
        "Defending": "Defending",
        "Ball Security": "BallSecurity",
        "Aerial": "Aerial",
    }

    for idx, row in sub_summary.iterrows():
        c_id = int(row["PlayingStyle_Cluster"])
        color = CLUSTER_COLORS[c_id % len(CLUSTER_COLORS)]
        name = row["Cluster_Name"]

        values = [float(row[summary_col_map.get(c, c)]) for c in categories]
        values_closed = values + [values[0]]

        fig.add_trace(
            go.Scatterpolar(
                r=values_closed,
                theta=categories_closed,
                fill="toself",
                name=name,
                line=dict(color=color, width=2),
                fillcolor=f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.12)",
                hovertemplate=f"<b>{name}</b><br>%{{theta}}: <b>%{{r:.1f}}</b><extra></extra>",
            )
        )

    fig = style_figure(fig, height=height)
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(15, 23, 42, 0.4)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                dtick=25,
                tickfont=dict(color=MUTED, size=9),
                gridcolor=BORDER,
            ),
            angularaxis=dict(
                tickfont=dict(color=TEXT, size=11),
                gridcolor=BORDER,
            ),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(color=TEXT, size=11),
        ),
        margin=dict(l=40, r=40, t=30, b=55),
    )
    return fig
