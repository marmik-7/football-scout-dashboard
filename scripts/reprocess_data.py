"""
SCOUT Platform — Data Reprocessing Pipeline (Phase 3: Advanced Football Analytics)
1. Fixes the aerial duels Won% data corruption by using Lost_stats_misc (Aerial Duels Lost).
2. Calculates Club Possession & Possession-Adjusted Defending (pAdj) for Tkl, Int, Blocks, Clr, Recov.
3. Classifies Tactical Sub-Roles (Center-Back, Full-Back/Wing-Back, Defensive Midfielder,
   Central Midfielder, Attacking Midfielder, Center Forward, Winger).
4. Retains and calculates Finishing Efficiency metrics (npxG, G-xG, npxG/Sh, Dist).
5. Recomputes players_clean.csv, players_engineered.csv, players_clustered.csv, and cluster_summary.csv.
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

METADATA_COLUMNS = feature_config["metadata_columns"]
DISCIPLINE_COLUMNS = feature_config["discipline_columns"]
DUPLICATE_COLUMNS = feature_config["duplicate_columns"]

df_raw = pd.read_csv(RAW_DATA_PATH)
df = df_raw.copy()

# Step 1: Remove goalkeepers
df = df[~df["Pos"].str.contains("GK", na=False)].copy()

# Preserve raw position string before splitting
df["Pos_Raw"] = df["Pos"].fillna("").astype(str)

# Calculate estimated club possession per competition
print("2. Calculating competition-level squad possession estimates...")
poss_dict = {}
for comp in df["Comp"].dropna().unique():
    cdf = df[df["Comp"] == comp]
    csp = cdf.groupby("Squad")["Att"].sum()
    n = len(csp)
    if n <= 1:
        continue
    tot = csp.sum()
    for sq, p in csp.items():
        opp = (tot - p) / (n - 1)
        poss = (p / (p + opp)) * 100.0
        poss_dict[sq] = poss

# Step 2: Remove duplicate statistics columns (preserving analytical fields)
columns_to_drop = [col for col in DUPLICATE_COLUMNS if col in df.columns]
df = df.drop(columns=columns_to_drop)

# Step 3: Aggregate multi-club records
print("3. Aggregating transferred players with corrected Aerial Duels & Finishing metrics...")
SUM_COLUMNS = [
    "Min", "Gls", "xG", "npxG", "Sh", "SoT", "Ast", "xA", "KP", "SCA", "GCA", "TB",
    "Cmp", "Att", "PrgP", "PrgDist", "PPA", "Sw", "PrgC", "Carries", "CPA", "Succ",
    "Tkl", "TklW", "Int", "Blocks_stats_defense", "Clr", "Recov", "Mis", "Dis", "Rec",
    "Won", "Lost_stats_misc", "Crs", "Touches", "Att Pen", "Dist",
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
        if col == "Dist":
            # Weighted average shot distance by shots
            shots = pd.to_numeric(group["Sh"], errors="coerce").fillna(0)
            dists = pd.to_numeric(group["Dist"], errors="coerce").fillna(0)
            tot_sh = shots.sum()
            main_record["Dist"] = (shots * dists).sum() / tot_sh if tot_sh > 0 else dists.mean()
        else:
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
            main_record["Pos_Raw"] = pos_min.idxmax()

    # Recalculate pass completion %
    if {"Cmp", "Att"}.issubset(group.columns):
        att = main_record["Att"]
        main_record["Cmp%"] = (main_record["Cmp"] / att * 100 if pd.notna(att) and att > 0 else np.nan)

    # Correctly use Lost_stats_misc (Aerial Duels Lost)
    if {"Won", "Lost_stats_misc"}.issubset(group.columns):
        total_aerial = main_record["Won"] + main_record["Lost_stats_misc"]
        main_record["Won%"] = (main_record["Won"] / total_aerial * 100 if pd.notna(total_aerial) and total_aerial > 0 else np.nan)

    # Recalculate goals per shot
    if {"Gls", "Sh"}.issubset(group.columns):
        shots = main_record["Sh"]
        main_record["G/Sh"] = (main_record["Gls"] / shots if pd.notna(shots) and shots > 0 else np.nan)

    # Calculate finishing efficiency metrics
    gls = pd.to_numeric(main_record.get("Gls", 0), errors="coerce")
    xg = pd.to_numeric(main_record.get("xG", 0), errors="coerce")
    npxg = pd.to_numeric(main_record.get("npxG", xg), errors="coerce")
    sh = pd.to_numeric(main_record.get("Sh", 0), errors="coerce")

    main_record["G-xG"] = float(gls - xg) if pd.notna(gls) and pd.notna(xg) else 0.0
    main_record["npxG/Sh"] = float(npxg / max(1, sh)) if pd.notna(npxg) and pd.notna(sh) and sh > 0 else 0.0

    aggregated_records.append(main_record)

aggregated_df = pd.DataFrame(aggregated_records)
result = pd.concat([aggregated_df, incomplete_identity], ignore_index=True)

# Filter by minimum 600 minutes
result = result[result["Min"] >= 600].copy()

# Standardize primary positions
result["Pos_Primary"] = result["Pos"].fillna("").str.split(",").str[0].str.strip()
result["Pos"] = result["Pos_Primary"].map({"DF": "DF", "MF": "MF", "FW": "FW"})
result = result[result["Pos"].notna()].copy()

# Step 4: Calculate Possession Adjustment Factor & Adjusted Defending Metrics
print("4. Computing pAdj defending metrics and tactical sub-roles...")
def compute_padj_factor(row):
    sq = str(row.get("Squad", "")).split(",")[0].strip()
    poss = poss_dict.get(sq, 50.0)
    # Standard StatsBomb pAdj formulation: 50 / (100 - team_poss)
    factor = 50.0 / (100.0 - poss)
    # Analytical safety bounds
    return float(np.clip(factor, 0.70, 1.45))

result["pAdj_Factor"] = result.apply(compute_padj_factor, axis=1)

# Apply pAdj to raw volume defensive metrics
for metric in ["Tkl", "TklW", "Int", "Clr", "Recov"]:
    if metric in result.columns:
        result[f"{metric}_pAdj"] = result[metric] * result["pAdj_Factor"]
if "Blocks_stats_defense" in result.columns:
    result["Blocks_pAdj"] = result["Blocks_stats_defense"] * result["pAdj_Factor"]

# Step 5: Classify Tactical Sub-Roles
def classify_subrole(row):
    mpos = row["Pos"]
    raw_pos = str(row.get("Pos_Raw", row["Pos"]))
    mins = max(1.0, float(row.get("Min", 1.0)))

    crs_p90 = float(row.get("Crs", 0.0)) / mins * 90.0
    prgc_p90 = float(row.get("PrgC", 0.0)) / mins * 90.0
    kp_p90 = float(row.get("KP", 0.0)) / mins * 90.0
    attpen_p90 = float(row.get("Att Pen", 0.0)) / mins * 90.0
    tklint_p90 = (float(row.get("Tkl", 0.0)) + float(row.get("Int", 0.0))) / mins * 90.0

    if mpos == "DF":
        # Full-backs/wing-backs deliver significant crosses or high progressive carries
        if crs_p90 >= 1.2 or (crs_p90 >= 0.8 and prgc_p90 >= 1.5) or ("MF" in raw_pos and crs_p90 >= 0.5):
            return "Full-Back / Wing-Back"
        return "Center-Back"
    elif mpos == "MF":
        # Attacking midfielders generate high key passes & penalty box entries
        if "FW" in raw_pos or (kp_p90 >= 1.8 and attpen_p90 >= 2.0) or (kp_p90 >= 2.2):
            return "Attacking Midfielder"
        # Defensive midfielders prioritize shielding and ball winning
        elif tklint_p90 >= 3.2 and attpen_p90 < 2.0 and kp_p90 < 1.4:
            return "Defensive Midfielder"
        return "Central Midfielder"
    elif mpos == "FW":
        # Wingers cross, carry, and enter from wide positions
        if crs_p90 >= 1.5 or (prgc_p90 >= 3.0 and crs_p90 >= 0.8) or ("MF" in raw_pos):
            return "Winger"
        return "Center Forward"
    return mpos

result["SubRole"] = result.apply(classify_subrole, axis=1)

# Fill residual rate NaNs with position medians
for col in ["Cmp%", "Won%", "G/Sh"]:
    if col in result.columns:
        result[col] = result.groupby("Pos")[col].transform(lambda s: s.fillna(s.median()))

clean_path = PROCESSED_DIR / "players_clean.csv"
result.to_csv(clean_path, index=False)
print(f"   Saved {clean_path} with shape {result.shape}")

# Step 6: Feature Engineering & Percentiles
print("5. Feature Engineering per-90 rates and position-relative percentiles...")
df_eng = result.copy()

PER_90_COLUMNS = [
    "Gls", "xG", "npxG", "Sh", "SoT", "Ast", "xA", "KP", "SCA", "GCA", "TB",
    "PrgP", "PrgDist", "PPA", "Sw", "PrgC", "Carries", "CPA", "Succ",
    "Tkl", "TklW", "Int", "Blocks_stats_defense", "Clr", "Recov",
    "Tkl_pAdj", "TklW_pAdj", "Int_pAdj", "Blocks_pAdj", "Clr_pAdj", "Recov_pAdj",
    "Mis", "Dis", "Rec", "Won", "Crs", "Touches", "Att Pen",
]

for col in PER_90_COLUMNS:
    if col in df_eng.columns:
        df_eng[f"{col}_per90"] = df_eng[col] / df_eng["Min"] * 90.0

NEGATIVE_FEATURES = ["Mis_per90", "Dis_per90"]
POSITIVE_FEATURES = [f"{col}_per90" for col in PER_90_COLUMNS if f"{col}_per90" not in NEGATIVE_FEATURES]
RATE_FEATURES = ["Cmp%", "Won%", "G/Sh", "npxG/Sh", "G-xG"]
SCORING_FEATURES = POSITIVE_FEATURES + NEGATIVE_FEATURES + RATE_FEATURES

for col in SCORING_FEATURES:
    if col in df_eng.columns:
        pct_col = f"{col}_pct"
        if col in NEGATIVE_FEATURES:
            df_eng[pct_col] = df_eng.groupby("Pos")[col].rank(pct=True, ascending=False) * 100.0
        else:
            df_eng[pct_col] = df_eng.groupby("Pos")[col].rank(pct=True, ascending=True) * 100.0

# Compute the 7 composite attribute scores with pAdj Defending
ATTRIBUTE_MAP_PADJ = {
    "Finishing": ["Gls_per90_pct", "xG_per90_pct", "Sh_per90_pct", "SoT_per90_pct", "G/Sh_pct"],
    "Creativity": ["Ast_per90_pct", "xA_per90_pct", "KP_per90_pct", "SCA_per90_pct", "GCA_per90_pct", "TB_per90_pct"],
    "Passing": ["Cmp%_pct", "PrgP_per90_pct", "PrgDist_per90_pct", "PPA_per90_pct", "TB_per90_pct", "Sw_per90_pct"],
    "Progression": ["PrgC_per90_pct", "PrgP_per90_pct", "Carries_per90_pct", "CPA_per90_pct", "Succ_per90_pct"],
    "Defending": ["Tkl_pAdj_per90_pct", "TklW_pAdj_per90_pct", "Int_pAdj_per90_pct", "Blocks_pAdj_per90_pct", "Clr_pAdj_per90_pct", "Recov_pAdj_per90_pct"],
    "BallSecurity": ["Cmp%_pct", "Mis_per90_pct", "Dis_per90_pct", "Rec_per90_pct"],
    "Aerial": ["Won_per90_pct", "Won%_pct"],
}

for attr, feat_pcts in ATTRIBUTE_MAP_PADJ.items():
    available_pcts = [p for p in feat_pcts if p in df_eng.columns]
    df_eng[f"{attr}_Score"] = df_eng[available_pcts].mean(axis=1)

# Raw unadjusted defending for transparency
raw_def_pcts = ["Tkl_per90_pct", "TklW_per90_pct", "Int_per90_pct", "Blocks_stats_defense_per90_pct", "Clr_per90_pct", "Recov_per90_pct"]
avail_raw = [p for p in raw_def_pcts if p in df_eng.columns]
df_eng["Defending_Score_Raw"] = df_eng[avail_raw].mean(axis=1)

eng_path = PROCESSED_DIR / "players_engineered.csv"
df_eng.to_csv(eng_path, index=False)
print(f"   Saved {eng_path} with shape {df_eng.shape}")

# Step 7: K-Means Clustering & 2D PCA per Position
print("6. Fitting K-Means (k=4) and 2D PCA per position...")
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

# Step 8: Cluster Summary
print("7. Generating empirical cluster summary...")
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
print("Reprocessing successfully complete with Phase 3 Advanced Football Analytics!")
