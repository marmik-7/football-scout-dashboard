"""
SCOUT Platform — Data Reprocessing Pipeline
Fixes the aerial duels Won% data corruption by using Lost_stats_misc (Aerial Duels Lost)
instead of Lost (Challenges Lost / Dribbled Past).
Recomputes players_clean.csv, players_engineered.csv, players_clustered.csv, and cluster_summary.csv.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "players_data_light-2024_2025.csv"
FEATURE_CONFIG_PATH = PROJECT_ROOT / "config" / "feature_config.json"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

print("1. Loading raw dataset and configuration...")
with open(FEATURE_CONFIG_PATH, "r", encoding="utf-8") as f:
    feature_config = json.load(f)

ATTRIBUTE_MAP = feature_config["attribute_map"]
METADATA_COLUMNS = feature_config["metadata_columns"]
DISCIPLINE_COLUMNS = feature_config["discipline_columns"]
DUPLICATE_COLUMNS = feature_config["duplicate_columns"]
DERIVED_COLUMNS = feature_config["derived_columns"]

df_raw = pd.read_csv(RAW_DATA_PATH)
df = df_raw.copy()

# Step 1: Remove goalkeepers
df = df[~df["Pos"].str.contains("GK", na=False)].copy()

# Step 2: Remove duplicate statistics columns
columns_to_drop = [col for col in DUPLICATE_COLUMNS if col in df.columns]
df = df.drop(columns=columns_to_drop)

# Step 3: Remove derived columns
columns_to_drop = [col for col in DERIVED_COLUMNS if col in df.columns]
df = df.drop(columns=columns_to_drop)

# Step 4: Aggregate multi-club records with FIXED Aerial Duels Lost
print("2. Aggregating transferred players with corrected Aerial Duels Lost...")
SUM_COLUMNS = [
    "Min", "Gls", "xG", "Sh", "SoT", "Ast", "xA", "KP", "SCA", "GCA", "TB",
    "Cmp", "Att", "PrgP", "PrgDist", "PPA", "Sw", "PrgC", "Carries", "CPA", "Succ",
    "Tkl", "TklW", "Int", "Blocks_stats_defense", "Clr", "Recov", "Mis", "Dis", "Rec",
    "Won", "Lost_stats_misc",
] + DISCIPLINE_COLUMNS
SUM_COLUMNS = list(dict.fromkeys(SUM_COLUMNS))

identity_columns = ["Player", "Nation", "Born"]
complete_identity = df[df[identity_columns].notna().all(axis=1)].copy()
incomplete_identity = df[df[identity_columns].isna().any(axis=1)].copy()

sum_columns = [col for col in SUM_COLUMNS if col in df.columns]
aggregated_records = []

for _, group in complete_identity.groupby(identity_columns, sort=False):
    group = group.copy()
    group["Min"] = pd.to_numeric(group["Min"], errors="coerce")
    valid_minutes = group["Min"].dropna()
    if valid_minutes.empty:
        main_record = group.iloc[0].copy()
    else:
        main_record = group.loc[valid_minutes.idxmax()].copy()

    for col in sum_columns:
        main_record[col] = pd.to_numeric(group[col], errors="coerce").sum(min_count=1)

    # Combine clubs and competitions
    if "Squad" in group.columns:
        clubs = group["Squad"].dropna().unique()
        if len(clubs) > 0:
            main_record["Squad"] = ", ".join(sorted(clubs))
    if "Comp" in group.columns:
        comps = group["Comp"].dropna().unique()
        if len(comps) > 0:
            main_record["Comp"] = ", ".join(sorted(comps))
    if "Pos" in group.columns:
        pos_min = group.assign(Min=pd.to_numeric(group["Min"], errors="coerce")).groupby("Pos", dropna=True)["Min"].sum()
        if not pos_min.empty:
            main_record["Pos"] = pos_min.idxmax()

    # Recalculate pass completion %
    if {"Cmp", "Att"}.issubset(group.columns):
        att = main_record["Att"]
        main_record["Cmp%"] = (main_record["Cmp"] / att * 100 if pd.notna(att) and att > 0 else np.nan)

    # FIX: Correctly use Lost_stats_misc (Aerial Duels Lost) instead of Lost (Challenges Lost)
    if {"Won", "Lost_stats_misc"}.issubset(group.columns):
        total_aerial = main_record["Won"] + main_record["Lost_stats_misc"]
        main_record["Won%"] = (main_record["Won"] / total_aerial * 100 if pd.notna(total_aerial) and total_aerial > 0 else np.nan)

    # Recalculate goals per shot
    if {"Gls", "Sh"}.issubset(group.columns):
        shots = main_record["Sh"]
        main_record["G/Sh"] = (main_record["Gls"] / shots if pd.notna(shots) and shots > 0 else np.nan)

    aggregated_records.append(main_record)

aggregated_df = pd.DataFrame(aggregated_records)
result = pd.concat([aggregated_df, incomplete_identity], ignore_index=True)

# Select relevant features
attribute_columns = []
for attr, details in ATTRIBUTE_MAP.items():
    attribute_columns.extend(details["features"])
selected_columns = list(dict.fromkeys(METADATA_COLUMNS + DISCIPLINE_COLUMNS + attribute_columns))
available_columns = [col for col in selected_columns if col in result.columns]
df_clean = result[available_columns].copy()

# Filter by minimum 600 minutes
df_clean = df_clean[df_clean["Min"] >= 600].copy()

# Standardize positions
df_clean["Pos"] = df_clean["Pos"].fillna("").str.split(",").str[0].str.strip()
df_clean["Pos"] = df_clean["Pos"].map({"DF": "DF", "MF": "MF", "FW": "FW"})

# Fill any residual rate NaNs with position medians
for col in ["Cmp%", "Won%", "G/Sh"]:
    if col in df_clean.columns:
        df_clean[col] = df_clean.groupby("Pos")[col].transform(lambda s: s.fillna(s.median()))

clean_path = PROCESSED_DIR / "players_clean.csv"
df_clean.to_csv(clean_path, index=False)
print(f"   Saved {clean_path} with shape {df_clean.shape}")

# Step 5: Feature Engineering & Percentiles
print("3. Feature Engineering per-90 rates and position-relative percentiles...")
df_eng = df_clean.copy()

PER_90_COLUMNS = [
    "Gls", "xG", "Sh", "SoT", "Ast", "xA", "KP", "SCA", "GCA", "TB",
    "PrgP", "PrgDist", "PPA", "Sw", "PrgC", "Carries", "CPA", "Succ",
    "Tkl", "TklW", "Int", "Blocks_stats_defense", "Clr", "Recov",
    "Mis", "Dis", "Rec", "Won",
]

for col in PER_90_COLUMNS:
    if col in df_eng.columns:
        df_eng[f"{col}_per90"] = df_eng[col] / df_eng["Min"] * 90

NEGATIVE_FEATURES = ["Mis_per90", "Dis_per90"]
POSITIVE_FEATURES = [f"{col}_per90" for col in PER_90_COLUMNS if f"{col}_per90" not in NEGATIVE_FEATURES]
RATE_FEATURES = ["Cmp%", "Won%", "G/Sh"]
SCORING_FEATURES = POSITIVE_FEATURES + NEGATIVE_FEATURES + RATE_FEATURES

for col in SCORING_FEATURES:
    pct_col = f"{col}_pct"
    if col in NEGATIVE_FEATURES:
        df_eng[pct_col] = df_eng.groupby("Pos")[col].rank(pct=True, ascending=False) * 100
    else:
        df_eng[pct_col] = df_eng.groupby("Pos")[col].rank(pct=True, ascending=True) * 100

# Compute the 7 composite attribute scores
for attr, details in ATTRIBUTE_MAP.items():
    feat_pcts = []
    for f_name in details["features"]:
        if f_name in RATE_FEATURES:
            p_col = f"{f_name}_pct"
        else:
            p_col = f"{f_name}_per90_pct"
        if p_col in df_eng.columns:
            feat_pcts.append(p_col)

    df_eng[f"{attr}_Score"] = df_eng[feat_pcts].mean(axis=1)

eng_path = PROCESSED_DIR / "players_engineered.csv"
df_eng.to_csv(eng_path, index=False)
print(f"   Saved {eng_path} with shape {df_eng.shape}")

# Step 6: K-Means Clustering & 2D PCA per Position
print("4. Fitting K-Means (k=4) and 2D PCA per position...")
CLUSTERING_FEATURES = [
    "Finishing_Score", "Creativity_Score", "Passing_Score",
    "Progression_Score", "Defending_Score", "BallSecurity_Score", "Aerial_Score",
]

df_clust = df_eng.copy()
df_clust_scaled = df_eng.copy()

for pos in sorted(df_clust["Pos"].unique()):
    mask = df_clust["Pos"] == pos
    scaler = StandardScaler()
    scaled_vals = scaler.fit_transform(df_clust.loc[mask, CLUSTERING_FEATURES])
    df_clust_scaled.loc[mask, CLUSTERING_FEATURES] = scaled_vals

    # K-Means clustering (k=4, random_state=42)
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    labels = kmeans.fit_predict(scaled_vals)
    df_clust.loc[mask, "PlayingStyle_Cluster"] = labels

    # 2D PCA
    pca = PCA(n_components=2)
    coords = pca.fit_transform(scaled_vals)
    df_clust.loc[mask, "PC1"] = coords[:, 0]
    df_clust.loc[mask, "PC2"] = coords[:, 1]

df_clust["PlayingStyle_Cluster"] = df_clust["PlayingStyle_Cluster"].astype(int)

clust_path = PROCESSED_DIR / "players_clustered.csv"
df_clust.to_csv(clust_path, index=False)
print(f"   Saved {clust_path} with shape {df_clust.shape}")

# Step 7: Cluster Summary
print("5. Generating empirical cluster summary...")
cluster_summary = (
    df_clust.groupby(["Pos", "PlayingStyle_Cluster"])
    .agg(
        Player_Count=("Player", "count"),
        Finishing=("Finishing_Score", "mean"),
        Creativity=("Creativity_Score", "mean"),
        Passing=("Passing_Score", "mean"),
        Progression=("Progression_Score", "mean"),
        Defending=("Defending_Score", "mean"),
        BallSecurity=("BallSecurity_Score", "mean"),
        Aerial=("Aerial_Score", "mean"),
    )
    .round(2)
    .reset_index()
)

summary_path = PROCESSED_DIR / "cluster_summary.csv"
cluster_summary.to_csv(summary_path, index=False)
print(f"   Saved {summary_path}")
print("Reprocessing successfully complete!")

