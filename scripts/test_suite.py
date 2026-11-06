import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import dash
# Initialize dash app with use_pages=True before importing pages
app = dash.Dash(__name__, use_pages=True, pages_folder="../app/pages")

from app.utils.data_loader import (
    load_data,
    get_unique_competitions,
    get_unique_subroles,
    get_player_by_name,
)
from app.utils.charts import build_pizza_chart, build_pca_cluster_scatter
from app.utils.similarity import find_similar_players
import app.pages.overview as overview
import app.pages.player_explorer as player_explorer
import app.pages.player_profile as player_profile
import app.pages.player_comparison as player_comparison
import app.pages.player_rankings as player_rankings
import app.pages.similar_players as similar_players
import app.pages.playing_styles as playing_styles
import app.pages.shortlists as shortlists


def run_full_scout_test_suite():
    print("=== TEST 1: Data Loader & Advanced Analytics Columns ===")
    df = load_data()
    expected_cols = ["SubRole", "pAdj_Factor", "Tkl_pAdj", "Int_pAdj", "G-xG", "npxG/Sh"]
    for c in expected_cols:
        assert c in df.columns, f"Expected column '{c}' missing from loaded dataset!"

    subroles = get_unique_subroles()
    print(f"Total players: {len(df)}. Tactical sub-roles ({len(subroles)}): {subroles}")
    assert len(subroles) == 7
    assert "Center-Back" in subroles
    assert "Full-Back / Wing-Back" in subroles
    assert "Defensive Midfielder" in subroles
    assert "Central Midfielder" in subroles
    assert "Attacking Midfielder" in subroles
    assert "Center Forward" in subroles
    assert "Winger" in subroles

    # Verify no infinite or NaN values in analytical metrics
    for col in ["pAdj_Factor", "G-xG", "npxG/Sh", "Defending_Score"]:
        assert df[col].isna().sum() == 0, f"Column {col} has unexpected NaN values!"
    print("PASS: Data Loader & Advanced Analytics Columns")

    print("\n=== TEST 2: Tactical Sub-Role Similarity Modeling ===")
    saliba_sim = find_similar_players("William Saliba", subrole_filter="Center-Back", top_n=5)
    assert not saliba_sim.empty, "Similar CBs query returned empty!"
    for _, r in saliba_sim.iterrows():
        assert r["SubRole"] == "Center-Back", f"Player {r['Player']} has unexpected subrole {r['SubRole']}"
        print(f" - {r['Player']} ({r['Squad']}, {r['SubRole']}): {r['Similarity_Pct']:.1f}%")

    saka_sim = find_similar_players("Bukayo Saka", subrole_filter="Winger", max_age=23, top_n=5)
    assert not saka_sim.empty, "Similar Wingers query returned empty!"
    for _, r in saka_sim.iterrows():
        assert r["SubRole"] == "Winger"
        assert r["Age"] <= 23
        print(f" - {r['Player']} ({r['Squad']}, Age {r['Age']}): {r['Similarity_Pct']:.1f}%")
    print("PASS: Tactical Sub-Role Similarity Modeling")

    print("\n=== TEST 3: Similar Players Page Callback & Explainable Similarity ===")
    from app.utils.similarity import explain_similarity
    p_ref = get_player_by_name("Trent Alexander-Arnold")
    p_cand = get_player_by_name("Achraf Hakimi")
    explanation = explain_similarity(p_ref, p_cand)
    assert "shared_strengths" in explanation and len(explanation["shared_strengths"]) > 0
    assert "key_differences" in explanation and len(explanation["key_differences"]) > 0
    assert "succession_note" in explanation
    assert "positional_compatibility" in explanation
    assert "tactical_disclaimer" in explanation

    # Scout View test
    res_sim_scout = similar_players.update_similar_players(
        ref_name="Trent Alexander-Arnold",
        pos_filter="DF",
        subrole_filter="Full-Back / Wing-Back",
        club_filter="ALL",
        comp_filter="ALL",
        max_age="ALL",
        top_n=5,
        scout_analyst_mode="scout",
    )
    assert res_sim_scout[0] is not None
    assert res_sim_scout[1] is not None
    assert "THE 3 DRIVERS OF SIMILARITY" in str(res_sim_scout[2])
    assert "Strongest Shared Tactical Attributes" in str(res_sim_scout[2])
    assert "Direct Twin" in str(res_sim_scout[3]) or "Strong Match" in str(res_sim_scout[3]) or "Partial Match" in str(res_sim_scout[3])

    # Analyst View test
    res_sim_analyst = similar_players.update_similar_players(
        ref_name="Trent Alexander-Arnold",
        pos_filter="DF",
        subrole_filter="Full-Back / Wing-Back",
        club_filter="ALL",
        comp_filter="ALL",
        max_age="ALL",
        top_n=5,
        scout_analyst_mode="analyst",
    )
    assert "ANALYST METHODOLOGY & MATHEMATICAL FORMULATION" in str(res_sim_analyst[2])
    print("PASS: Similar Players Page Callback & Explainable Similarity")

    print("\n=== TEST 4: Player Rankings with Sub-Role Filtering ===")
    res_rank = player_rankings.update_rankings(
        pos="FW",
        subrole="Center Forward",
        attr="Finishing",
        comp="Premier League",
        age_group="ALL",
        depth=10,
        order="desc",
        squad="ALL",
    )
    assert res_rank[0] is not None
    assert res_rank[1] is not None
    assert res_rank[2] is not None
    print("PASS: Player Rankings Callback")

    print("\n=== TEST 5: Player Explorer with Sub-Role & Advanced Sorting ===")
    table_ui, count_text, total_pages = player_explorer.update_explorer_table(
        search="",
        pos="DF",
        subrole="Center-Back",
        comp="Premier League",
        squad="ALL",
        nation="ALL",
        age_preset="ALL",
        sort_attr="G-xG",
        sort_order="desc",
        min_min=600,
        min_score=0,
        sec_attr="NONE",
        sec_score=0,
        page=1,
    )
    assert table_ui is not None
    assert "Center-Back" in str(count_text) or "matching players" in str(count_text)
    print(f" - Explorer output: {count_text}")
    print("PASS: Player Explorer Callback")

    print("\n=== TEST 6: Player Profile Callback with Pizza & Radar Views ===")
    # 1. Scout View (Role-Tailored metrics & Recruitment Assessment)
    res_prof_scout = player_profile.update_player_profile("Erling Haaland", metric_mode="per90", chart_type="pizza", scout_analyst_mode="scout")
    assert len(res_prof_scout) == 8
    assert res_prof_scout[0] is not None
    assert res_prof_scout[1] is not None  # Pizza Chart Figure
    assert res_prof_scout[2] is not None  # Chart note
    assert len(res_prof_scout[1].data) == 3  # 3 polar traces (Attacking, Possession, Defending)
    
    # Verify Scout View recruitment suitability assessment and role metrics
    scouting_summary_str = str(res_prof_scout[4])
    assert "RECRUITMENT SUITABILITY ASSESSMENT" in scouting_summary_str
    assert "Statistical Attractions" in scouting_summary_str
    assert "Recommended Next Scouting Steps" in scouting_summary_str
    assert "NOTICE: This assessment is an automated statistical synthesis" in scouting_summary_str
    
    stats_grid_scout_str = str(res_prof_scout[5])
    assert "ROLE-TAILORED METRICS" in stats_grid_scout_str
    assert "Center Forward" in stats_grid_scout_str

    # 2. Analyst View (Comprehensive 15-item matrix)
    res_prof_analyst = player_profile.update_player_profile("William Saliba", metric_mode="total", chart_type="radar", scout_analyst_mode="analyst")
    assert len(res_prof_analyst) == 8
    assert res_prof_analyst[0] is not None
    assert res_prof_analyst[1] is not None  # Radar Figure
    assert len(res_prof_analyst[1].data) >= 1
    stats_grid_analyst_str = str(res_prof_analyst[5])
    assert "pAdj Defending Actions" in stats_grid_analyst_str or "PADJ" in stats_grid_analyst_str

    # 3. Low-Minutes Player Sample-Size Warning (<900m)
    df_all = load_data()
    low_min_player = df_all[df_all["Min"] < 800].iloc[0]["Player"]
    res_prof_low = player_profile.update_player_profile(low_min_player, metric_mode="per90", chart_type="pizza", scout_analyst_mode="scout")
    assert "Limited Sample" in str(res_prof_low[0]) or "Limited" in str(res_prof_low[4])
    print(f" - Low minutes test verified for {low_min_player} (<900m sample warning badge present)")
    print("PASS: Player Profile Callback (Scout, Analyst, Pizza, Radar & Sample Size)")

    print("\n=== TEST 7: Player Comparison Delta Calculation & Export ===")
    warn, rad, bar, stats_tbl, profs = player_comparison.update_comparison_views(
        ["William Saliba", "Virgil van Dijk"], metric_mode="per90", show_deltas=True, scout_analyst_mode="scout"
    )
    assert stats_tbl is not None
    assert rad is not None
    assert bar is not None
    assert profs is not None
    stats_tbl_str = str(stats_tbl)
    assert "EXECUTIVE HEAD-TO-HEAD RECRUITMENT VERDICT" in stats_tbl_str
    assert "Baseline Starter Advantage" in stats_tbl_str
    assert "Target Alternative Advantage" in stats_tbl_str

    # Analyst mode check
    warn_a, rad_a, bar_a, stats_tbl_a, profs_a = player_comparison.update_comparison_views(
        ["William Saliba", "Virgil van Dijk"], metric_mode="total", show_deltas=True, scout_analyst_mode="analyst"
    )
    assert "ANALYST VIEW" in str(stats_tbl_a)

    # Verify comparison export CSV
    csv_dict = player_comparison.export_comparison_csv(
        n_clicks=1,
        selected_names=["William Saliba", "Virgil van Dijk"],
        metric_mode="per90",
    )
    assert csv_dict is not None
    assert "filename" in csv_dict
    assert "scout_comparison_William_Saliba_matrix.csv" in csv_dict["filename"]
    assert "content" in csv_dict
    print("PASS: Player Comparison Delta Matrix, Executive Verdict & CSV Export")

    print("\n=== TEST 8: Player Profile Shortlist Bookmarking ===")
    mock_store = []
    updated_store, feedback = player_profile.save_profile_to_shortlist(
        n_clicks=1,
        player_name="Martin Ødegaard",
        tier="A-List Target",
        notes="Elite creative playmaker for possession-dominant setup.",
        current_data=mock_store,
    )
    assert len(updated_store) == 1
    assert updated_store[0]["player"] == "Martin Ødegaard"
    assert updated_store[0]["tier"] == "A-List Target"
    assert feedback is not None
    print("PASS: Player Profile Shortlist Bookmarking")

    print("\n=== TEST 9: Recruitment Shortlists View & Dossier Export ===")
    test_shortlist = [
        {"player": "Martin Ødegaard", "tier": "A-List Target", "notes": "Primary playmaker target"},
        {"player": "Moisés Caicedo", "tier": "Primary Alternative", "notes": "Elite ball winner"},
        {"player": "William Saliba", "tier": "Monitor / Development", "notes": "Top tier CB"},
    ]
    # Filter: ALL
    metrics_ui, table_ui = shortlists.update_shortlist_view(
        shortlist_data=test_shortlist,
        search="",
        filter_tier="ALL",
        filter_pos="ALL",
        filter_subrole="ALL",
    )
    assert metrics_ui is not None
    assert table_ui is not None

    # Filter: Tier = A-List Target
    metrics_ui_a, table_ui_a = shortlists.update_shortlist_view(
        shortlist_data=test_shortlist,
        search="",
        filter_tier="A-List Target",
        filter_pos="ALL",
        filter_subrole="ALL",
    )
    assert metrics_ui_a is not None
    assert table_ui_a is not None

    # Export Dossier CSV
    dossier_csv = shortlists.export_shortlist_dossier(n_clicks=1, shortlist_data=test_shortlist)
    assert dossier_csv is not None
    assert "filename" in dossier_csv
    assert "scout_recruitment_dossier_2024_25.csv" in dossier_csv["filename"]
    assert "content" in dossier_csv
    print("PASS: Shortlists View & Dossier Export")

    print("\n=== TEST 10: Percentile Pizza Chart Generator ===")
    for test_p in ["Erling Haaland", "William Saliba", "Bukayo Saka"]:
        p_rec = get_player_by_name(test_p)
        assert p_rec is not None
        pizza_fig = build_pizza_chart(p_rec, height=400)
        assert len(pizza_fig.data) == 3  # Attacking, Possession, Defending
        # Total wedges = 4 + 4 + 4 = 12
        total_slices = sum(len(tr.r) for tr in pizza_fig.data)
        assert total_slices == 12, f"Expected 12 pizza slices, got {total_slices}"
        print(f" - {test_p}: 12 radial wedges generated with valid percentiles")
    print("PASS: Percentile Pizza Chart Generator")

    print("\n=== TEST 11: Tactical Playing Styles & 2D PCA Locator ===")
    # 1. Test locator dropdown options
    opts, default_val = playing_styles.update_locator_dropdown("FW")
    assert len(opts) > 50
    assert default_val == "NONE"

    # 2. Test PCA Scatter with highlighted target and Scout View
    cards_ui, pca_fig, dna_fig, tbl_ui, roster_ui = playing_styles.update_playing_styles(
        pos="FW",
        cluster_filter="ALL",
        locator_player="Erling Haaland",
        scout_analyst_mode="scout",
    )
    assert pca_fig is not None
    # Verify PCA axes titles are mathematically honest without fake subjective labels
    xaxis_title = pca_fig.layout.xaxis.title.text
    yaxis_title = pca_fig.layout.yaxis.title.text
    assert "Principal Component 1" in xaxis_title
    assert "Principal Component 2" in yaxis_title
    assert "Defensive & Duel Solidity" not in xaxis_title  # Verified no fake axis definitions

    # Verify highlight traces (halo + diamond marker + annotations)
    trace_names = [tr.name for tr in pca_fig.data]
    assert any("Erling Haaland" in str(n) for n in trace_names), "Expected player pin trace in PCA plot!"
    print(" - Highlight pin and annotation verified for Erling Haaland in 2D PCA Space")

    # Verify cluster cards contain empirical archetype names and anchors
    cards_str = str(cards_ui)
    assert "EMPIRICAL FW TACTICAL ARCHETYPES" in cards_str
    assert "Aerial Target Man" in cards_str
    assert "Anchors:" in cards_str

    # Analyst View check
    cards_a, _, _, _, _ = playing_styles.update_playing_styles(
        pos="MF",
        cluster_filter="ALL",
        scout_analyst_mode="analyst",
    )
    assert "ANALYST VIEW" in str(cards_a)
    print("PASS: Tactical Playing Styles, Objective PCA Axes & 2D Locator")

    print("\n=== TEST 12: All 8 Page Layouts Instantiation ===")
    def get_layout(mod, *args, **kwargs):
        if callable(getattr(mod, "layout", None)):
            return mod.layout(*args, **kwargs)
        return getattr(mod, "layout", None)

    assert get_layout(overview) is not None
    assert get_layout(player_explorer) is not None
    assert get_layout(player_profile, "Bukayo Saka") is not None
    assert get_layout(player_comparison) is not None
    assert get_layout(player_rankings) is not None
    assert get_layout(similar_players) is not None
    assert get_layout(playing_styles) is not None
    assert get_layout(shortlists) is not None
    print("PASS: All 8 Page Layouts successfully instantiated!")

    print("\n=== TEST 13: Metric Definitions & Global View Infrastructure ===")
    from app.utils.metric_definitions import (
        METRIC_DEFINITIONS,
        get_metric_label,
        get_metric_tooltip,
        get_role_metrics,
        get_sample_size_badge,
        SAMPLE_SIZE_THRESHOLD,
    )
    from app.app import app as main_app

    # Verify key metrics exist
    for m in ["Gls_per90", "xG_per90", "G-xG", "npxG/Sh", "PrgP_per90", "Tkl_pAdj_per90", "Won%"]:
        assert m in METRIC_DEFINITIONS, f"Metric '{m}' missing from METRIC_DEFINITIONS!"
        info = METRIC_DEFINITIONS[m]
        assert "scout_name" in info and len(info["scout_name"]) > 0
        assert "technical_name" in info and len(info["technical_name"]) > 0
        assert "category" in info
        assert "description" in info
        assert "why_it_matters" in info
        assert info["tier"] in ["scout", "analyst"]

    # Verify labels in both scout and analyst mode
    assert get_metric_label("G-xG", mode="scout") == "Finishing Over/Underperformance"
    assert get_metric_label("G-xG", mode="analyst") == "Finishing Variance (G - xG)"
    assert "Measures shot selection discipline" in get_metric_tooltip("npxG/Sh")

    # Verify all 7 subroles have 6 role-tailored metrics
    for sr in [
        "Center Forward",
        "Winger",
        "Attacking Midfielder",
        "Central Midfielder",
        "Defensive Midfielder",
        "Full-Back / Wing-Back",
        "Center-Back",
    ]:
        role_mets = get_role_metrics(sr)
        assert len(role_mets) == 6, f"Expected 6 role metrics for {sr}, got {len(role_mets)}"

    # Verify sample size thresholds
    badge_low = get_sample_size_badge(450)
    assert badge_low is not None
    badge_high = get_sample_size_badge(1800)
    assert badge_high is None

    # Verify layout contains scout-analyst-mode store and global-view-toggle
    layout_str = str(main_app.layout)
    assert "scout-analyst-mode" in layout_str
    assert "global-view-toggle" in layout_str
    print("PASS: Metric Definitions & Global View Infrastructure")

    print("\n========================================================")
    print("ALL 13 UNIT AND INTEGRATION TEST SUITES PASSED PERFECTLY!")
    print("========================================================")


if __name__ == "__main__":
    run_full_scout_test_suite()
