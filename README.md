# SCOUT — Football Scouting & Player Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Dash](https://img.shields.io/badge/Dash-4.5.0-008080.svg)](https://dash.plotly.com/)
[![Dash Mantine Components](https://img.shields.io/badge/DMC-3.0.0-339AF0.svg)](https://dash-mantine-components.com/)
[![Plotly](https://img.shields.io/badge/Plotly-7.1.0-3F4F75.svg)](https://plotly.com/)

**SCOUT** is an advanced football scouting and player analytics dashboard built with Plotly Dash and Dash Mantine Components. It delivers high-density performance evaluations, position-relative percentile profiling, and playing style intelligence for players across Europe's top leagues (2024–25 Season, minimum 600 minutes played).

---

## 🌟 Key Features

- **Executive Overview Dashboard**:
  - **KPI Metric Cards**: Quick-reference summary of total evaluated players, defenders, midfielders, and forwards.
  - **Squad Composition**: Interactive donut visualization showing positional balance.
  - **Attribute Distribution**: Box plot visualization showing median, quartiles ($Q_1$, $Q_3$), and full spread (0–100 percentile scale) across all 7 scouting dimensions.
  - **Top Performers Ranking**: Interactive horizontal bar chart ranking the top 10 players by attribute and position group, complete with club, position, and nationality tooltips.
- **Position-Relative Analytical Benchmarking**:
  - Attribute scores are engineered as position-specific percentiles (e.g., defender finishing benchmarked against other defenders).
  - Clear analytical notices explaining cross-position comparison limitations when viewing all positions together.
- **7 Core Scouting Dimensions**:
  1. **Finishing** (`Finishing_Score`)
  2. **Creativity** (`Creativity_Score`)
  3. **Passing** (`Passing_Score`)
  4. **Progression** (`Progression_Score`)
  5. **Defending** (`Defending_Score`)
  6. **Ball Security** (`BallSecurity_Score`)
  7. **Aerial** (`Aerial_Score`)
- **End-to-End Data Pipeline**:
  - Exploratory analysis, feature engineering, player similarity modeling, and unsupervised clustering notebooks included in `notebooks/`.

---

## 📁 Project Structure

```text
football-scout-dashboard/
├── app/
│   ├── app.py                   # Main Dash application & callbacks
│   └── assets/
│       └── style.css            # Custom CSS styling (SCOUT dark navy & lime theme)
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
├── requirements.txt             # Python package dependencies
├── .gitignore                   # Ignored files & artifacts
└── README.md                    # Project documentation
```

---

## 🚀 Getting Started

### 1. Clone the repository
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

### 4. Run the dashboard
```bash
python app/app.py
```

The application will start locally at **`http://127.0.0.1:8050/`**.

---

## 🎨 Visual Identity & UI Design

- **Background**: `#101827` (Dark Navy)
- **Panel Surface**: `#172438`
- **Borders & Dividers**: `#263449`
- **Primary Accent**: `#84CC16` (SCOUT Lime)
- **Typography**: Inter / Sans-serif (`#F8FAFC` headings, `#94A3B8` secondary)
