# SCOUT — Football Scouting & Player Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Dash](https://img.shields.io/badge/Dash-4.5.0-008080.svg)](https://dash.plotly.com/)
[![Dash Mantine Components](https://img.shields.io/badge/DMC-3.0.0-339AF0.svg)](https://dash-mantine-components.com/)
[![Plotly](https://img.shields.io/badge/Plotly-7.1.0-3F4F75.svg)](https://plotly.com/)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.9.0-F7931E.svg)](https://scikit-learn.org/)

**SCOUT** is a professional football scouting and player intelligence platform built with Plotly Dash, Dash Mantine Components, and Scikit-learn. It delivers multi-dimensional performance evaluations, position-relative percentile profiling, unsupervised playing style clustering, and candidate similarity matching for **1,692 qualified players** across Europe's top leagues (2024–25 Season, minimum 600 minutes played).

---

## 🌟 Executive Features & Analytical Modules

SCOUT is organized into seven modular analytical suites:

### 1. `01 Overview`
- **KPI Metric Summary**: High-level counts of total qualified talent (1,692), defenders (702), midfielders (564), and forwards (426).
- **Squad Composition Donut**: Positional balance visualization with center volume annotation.
- **Attribute Distribution Box Plots**: Fixed 0–100 percentile scale visualization displaying median, quartiles ($Q_1$, $Q_3$), and full spread across all 7 scouting dimensions.
- **Interactive Top Performers**: Horizontal ranking chart filterable by position group and attribute with contextual analytical notices regarding position-relative benchmarking.

### 2. `02 Player Explorer`
- **Comprehensive Database Filter**: Search 1,692 players by text query, position group (DF, MF, FW), club (204 teams), and nationality (101 nations).
- **Dynamic Threshold Sliders**: Filter by minimum minutes played (600m to 3,000m) and minimum attribute percentile scores.
- **Sortable Roster Table**: Paginated data grid displaying player metadata, G+A volume, and all 7 core percentiles with direct navigation to deep player profiles.

### 3. `03 Player Profile`
- **7-Dimensional Scouting Radar**: Multi-axis polar footprint overlaid against the positional peer group average benchmark.
- **Tactical Archetype DNA**: Categorization into empirical playing-style clusters (e.g. *Attacking Full-Back*, *Deep-Lying Controller*, *Aerial Target Man*).
- **Attribute Breakdown Cards**: Score cards with qualitative classifications (*Elite*, *Strong*, *Average*, *Developing*) and deviation ($\Delta$) against position averages.
- **Production Statistics Grid**: Season volume and efficiency metrics (Goals, Assists, xG, xA, SCA, Progressive Passes, Progressive Carries, Tackles, Interceptions).
- **Automated Scouting Assessment**: Programmatic narrative synthesizing player strengths, tactical role, and developmental priorities.

### 4. `04 Player Comparison`
- **Multi-Candidate Evaluation**: Simultaneously compare between 2 and 4 players across clubs or positions.
- **Overlaid Radar Footprints & Grouped Bar Charts**: Visual side-by-side benchmarking of 7-dimensional profiles.
- **Head-to-Head Matrix**: Full statistical comparison table comparing metadata, engineered percentiles, and match volume.
- **Cross-Position Warning System**: Dynamic analytical alert warning scouts when comparing players from differing position groups where percentiles are calculated within position cohorts.

### 5. `05 Similar Players`
- **Algorithmic Player Replacement**: Cosine similarity engine operating on position-standardized attribute vectors to identify statistical twins.
- **Candidate Filtering**: Scope similarity searches to the same position group or cross-position candidates with club filters.
- **Head-to-Head Comparison**: Overlaid radar chart benchmarking the target player against their #1 statistical match.
- **Ranked Match Table**: Similarity index percentages (e.g. 98.5%) and full attribute profiles for candidate recruitment.

### 6. `06 Playing Styles`
- **Unsupervised K-Means Clustering**: 4 distinct tactical sub-roles identified for each position group (12 total archetypes) derived from the 7 scouting dimensions.
- **2D PCA Projection Scatter**: Interactive spatial mapping of principal components (PC1 vs PC2) with cluster highlighting and hover inspection.
- **Tactical Archetype Radar**: Overlaid mean attribute profiles illustrating positional archetypes.
- **Representative Rosters**: Cluster summary means and player rosters assigned to each playing style.

### 7. `07 Player Rankings`
- **Global Leaderboards**: Interactive leaderboards for all 7 scouting dimensions: *Finishing*, *Creativity*, *Passing*, *Progression*, *Defending*, *Ball Security*, and *Aerial*.
- **Configurable Depths**: View Top 10, Top 25, Top 50, or Top 100 leaders with ascending/descending sorting.
- **Position & Club Scopes**: Default position set to Forwards (FW) with position-relative warning displayed when viewing All Positions.

---

## 📐 7 Core Engineered Scouting Dimensions

All scores represent **position-relative percentile ranks (0–100)** calculated relative to players in the same position group with $\ge 600$ minutes:

| Attribute | Engineered Column | Primary Statistical Inputs |
| :--- | :--- | :--- |
| **Finishing** | `Finishing_Score` | Goals, xG, Shot volume, Shots on target, Goal conversion |
| **Creativity** | `Creativity_Score` | Assists, xA, Key passes, Shot-creating actions (SCA), Goal-creating actions (GCA) |
| **Passing** | `Passing_Score` | Pass completion %, Progressive passes, Through balls, Switches |
| **Progression** | `Progression_Score` | Progressive carries, Progressive carry distance, Passes into penalty area, Successful take-ons |
| **Defending** | `Defending_Score` | Tackles won, Interceptions, Blocks, Recoveries |
| **Ball Security** | `BallSecurity_Score` | Low dispossessions, Low miscontrols, Retained carries, Pass security |
| **Aerial** | `Aerial_Score` | Aerial duels won per 90, Aerial duel win percentage |

---

## 📁 Project Architecture

```text
football-scout-dashboard/
├── app/
│   ├── app.py                   # Master Dash application, router & navigation shell
│   ├── pages/                   # Dash Pages multi-page architecture
│   │   ├── overview.py          # Module 1: Executive Overview
│   │   ├── player_explorer.py   # Module 2: Search & Filter Database
│   │   ├── player_profile.py    # Module 3: Deep Player Profile & Radar
│   │   ├── player_comparison.py # Module 4: Multi-Player Head-to-Head
│   │   ├── similar_players.py   # Module 5: Cosine Similarity Matching
│   │   ├── playing_styles.py    # Module 6: K-Means & PCA Clustering
│   │   └── player_rankings.py   # Module 7: Global Attribute Leaderboards
│   ├── utils/                   # Reusable business logic & chart components
│   │   ├── styling.py           # Design tokens, palette, style_figure, cards
│   │   ├── data_loader.py       # Cached DataFrame, cluster summaries, helpers
│   │   ├── charts.py            # Reusable Plotly radars, bars, PCA scatter
│   │   ├── similarity.py        # Position-standardized cosine similarity engine
│   │   └── player_analysis.py   # Automated scouting narrative & strengths/weaknesses
│   └── assets/
│       └── style.css            # Dark navy theme & custom Mantine CSS overrides
├── config/
│   ├── feature_config.json      # Metric groupings & feature definitions
│   └── preprocessing_config.json# Filtering & data thresholds
├── data/
│   ├── processed/               # Cleaned, engineered & clustered datasets
│   └── raw/                     # Raw player match statistics
├── notebooks/                   # Jupyter data science & modeling workflows
│   ├── 01_data_understanding.ipynb
│   ├── 02_feature_selection.ipynb
│   ├── 03_preprocessing.ipynb
│   ├── 04_feature_engineering.ipynb
│   ├── 05_similarity.ipynb
│   ├── 06_clustering.ipynb
│   └── 07_visualization.ipynb
├── requirements.txt             # Python dependencies
├── .gitignore                   # Version control ignore rules
└── README.md                    # Platform documentation
```

---

## 🚀 Installation & Running Locally

### 1. Clone repository
```bash
git clone https://github.com/marmik-7/football-scout-dashboard.git
cd football-scout-dashboard
```

### 2. Set up virtual environment
```bash
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
python app/app.py
```

Open your browser and navigate to:
**`http://127.0.0.1:8050/`**

---

## 🎨 Visual Identity & Design System

- **Background Canvas**: `#101827` (Deep Midnight Navy)
- **Panel Surface**: `#172438` / `#131E30`
- **Borders & Dividers**: `#263449`
- **Primary Accent**: `#84CC16` (SCOUT Electric Lime)
- **Defender Accent**: `#38BDF8` (Cyan Blue)
- **Midfielder Accent**: `#A3E635` (Lime Green)
- **Forward Accent**: `#F59E0B` (Amber Orange)
- **Typography**: Inter (`#F8FAFC` headings, `#94A3B8` secondary)
