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
    "#84CC16",  # Primary SCOUT Lime
    "#38BDF8",  # Cyan Blue
    "#F59E0B",  # Amber Orange
    "#EC4899",  # Pink
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
    for i, p in enumerate(players):
        color = PLAYER_COMPARE_COLORS[i % len(PLAYER_COMPARE_COLORS)]
        values = [float(p[ATTRIBUTE_COLUMNS[c]]) for c in categories]
        values_closed = values + [values[0]]
        player_label = p.get("Player_Unique", p.get("Player", f"Player {i+1}"))

        fig.add_trace(
            go.Scatterpolar(
                r=values_closed,
                theta=categories_closed,
                fill="toself",
                name=player_label,
                line=dict(color=color, width=2.2),
                fillcolor=f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.18)",
                hovertemplate=f"<b>{player_label}</b><br>%{{theta}}: <b>%{{r:.1f}}</b><extra></extra>",
            )
        )

    fig = style_figure(fig, height=height)
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(19, 30, 48, 0.7)",
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


def build_pca_cluster_scatter(df, pos="FW", selected_cluster="ALL", height=480):
    """
    Builds an interactive 2D PCA scatter plot colored by Playing Style clusters.
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

    fig = style_figure(fig, height=height)
    fig.update_layout(
        title=dict(
            text=f"2D PCA Projection — {pos} Playing Styles",
            font=dict(color=TEXT, size=15),
            subtitle=dict(text="Clustered using K-Means on the 7 core scouting dimensions", font=dict(color=MUTED, size=11)),
        ),
        xaxis=dict(
            title=dict(text="Principal Component 1 (PC1)", font=dict(color=MUTED, size=11)),
            gridcolor=BORDER,
            zerolinecolor=BORDER,
            tickfont=dict(color=MUTED),
        ),
        yaxis=dict(
            title=dict(text="Principal Component 2 (PC2)", font=dict(color=MUTED, size=11)),
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
            bgcolor="rgba(19, 30, 48, 0.7)",
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
