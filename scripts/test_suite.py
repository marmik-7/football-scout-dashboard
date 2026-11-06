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

    print("\n=== TEST 3: Similar Players Page Callback ===")
    res_sim = similar_players.update_similar_players(
        ref_name="Trent Alexander-Arnold",
        pos_filter="DF",
        subrole_filter="Full-Back / Wing-Back",
        club_filter="ALL",
        comp_filter="ALL",
        max_age="ALL",
        top_n=5,
    )
    assert res_sim[0] is not None
    assert res_sim[1] is not None
    assert res_sim[3] is not None
    print("PASS: Similar Players Page Callback")

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

    print("\n=== TEST 6: Player Profile Callback with pAdj & Finishing Metrics ===")
    res_prof_p90 = player_profile.update_player_profile("Erling Haaland", metric_mode="per90")
    assert len(res_prof_p90) == 7
    assert res_prof_p90[0] is not None
    assert res_prof_p90[4] is not None

    res_prof_tot = player_profile.update_player_profile("William Saliba", metric_mode="total")
    assert len(res_prof_tot) == 7
    assert res_prof_tot[0] is not None
    assert res_prof_tot[4] is not None
    print("PASS: Player Profile Callback")

    print("\n=== TEST 7: Player Comparison Delta Calculation & Export ===")
    warn, rad, bar, stats_tbl, profs = player_comparison.update_comparison_views(
        ["William Saliba", "Virgil van Dijk"], metric_mode="per90", show_deltas=True
    )
    assert stats_tbl is not None
    assert rad is not None
    assert bar is not None
    assert profs is not None

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
    print("PASS: Player Comparison Delta Matrix & CSV Export")

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

    print("\n=== TEST 10: All 8 Page Layouts Instantiation ===")
    def get_layout(mod, *args, **kwargs):
        if callable(getattr(mod, "layout", None)):
            return mod.layout(*args, **kwargs)
        return getattr(mod, "layout", None)

    assert get_layout(overview) is not None
    assert get_layout(player_explorer) is not None
    assert get_layout(player_profile, "Rodri") is not None
    assert get_layout(player_comparison) is not None
    assert get_layout(player_rankings) is not None
    assert get_layout(similar_players) is not None
    assert get_layout(playing_styles) is not None
    assert get_layout(shortlists) is not None
    print("PASS: All 8 Page Layouts successfully instantiated!")

    print("\nALL RECRUITMENT INTELLIGENCE & SHORTLISTING TESTS PASSED PERFECTLY!")


if __name__ == "__main__":
    run_full_scout_test_suite()
