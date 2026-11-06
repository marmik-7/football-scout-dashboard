import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import dash
# Initialize dash app with use_pages=True before importing pages
app = dash.Dash(__name__, use_pages=True, pages_folder="../app/pages")

from app.utils.data_loader import load_data, get_unique_competitions, get_player_by_name
from app.utils.similarity import find_similar_players
import app.pages.overview as overview
import app.pages.player_explorer as player_explorer
import app.pages.player_profile as player_profile
import app.pages.player_comparison as player_comparison
import app.pages.player_rankings as player_rankings
import app.pages.similar_players as similar_players
import app.pages.playing_styles as playing_styles

def test_phase2():
    print("=== TEST 1: Data Loader & Competition Metadata ===")
    df = load_data()
    assert "Comp_Clean" in df.columns, "Comp_Clean column missing!"
    comps = get_unique_competitions()
    print(f"Loaded {len(df)} players. Competitions found: {comps}")
    assert len(comps) >= 5, f"Expected at least 5 leagues, got {comps}"
    assert "Premier League" in comps
    assert "La Liga" in comps
    assert "Bundesliga" in comps
    assert "Serie A" in comps
    assert "Ligue 1" in comps
    print("PASS: Data Loader & Competition Metadata")

    print("\n=== TEST 2: Succession Planning & Young Player Similarity ===")
    # Find U-23 players in Bundesliga similar to Kevin De Bruyne
    kdb_sim = find_similar_players("Kevin De Bruyne", top_n=5, comp_filter="Bundesliga", max_age=23)
    assert not kdb_sim.empty, "Similarity search returned empty DataFrame!"
    for _, row in kdb_sim.iterrows():
        assert row["Age"] <= 23, f"Player {row['Player']} age {row['Age']} exceeds max_age=23"
        assert "Bundesliga" in row["Comp_Clean"], f"Player {row['Player']} league {row['Comp_Clean']} not Bundesliga"
        print(f" - {row['Player']} ({row['Squad']}, Age {row['Age']}): {row['Similarity_Pct']:.1f}%")
    print("PASS: Succession Planning Similarity")

    print("\n=== TEST 3: Similar Players Page Callback ===")
    res_sim = similar_players.update_similar_players(
        ref_name="Erling Haaland",
        pos_filter="ALL",
        club_filter="ALL",
        comp_filter="La Liga",
        max_age=25,
        top_n=5
    )
    # Returns: banner, radar_fig, methodology, table
    assert res_sim[0] is not None
    assert res_sim[1] is not None
    assert res_sim[2] is not None
    assert res_sim[3] is not None
    print("PASS: Similar Players Callback")

    print("\n=== TEST 4: Player Rankings Page Callback ===")
    res_rank = player_rankings.update_rankings(
        "FW", "Finishing", "Premier League", "U-23", 10, "desc", "ALL"
    )
    # Returns: notice_container, bar_fig, table_container
    assert res_rank[0] is not None
    assert res_rank[1] is not None
    assert res_rank[2] is not None
    print("PASS: Player Rankings Callback")

    print("\n=== TEST 5: Player Explorer Multi-Attribute Screening Callback ===")
    # Screen for Midfielders in Serie A, age U-23, with Passing >= 70 AND Progression >= 70
    table_ui, count_text, total_pages = player_explorer.update_explorer_table(
        search="",
        pos="MF",
        comp="Serie A",
        squad="ALL",
        nation="ALL",
        age_preset="U-23",
        sort_attr="Passing_Score",
        sort_order="desc",
        min_min=500,
        min_score=70,
        sec_attr="Progression_Score",
        sec_score=70,
        page=1
    )
    print(f" - Explorer results count text: '{count_text}' | Total pages: {total_pages}")
    assert table_ui is not None
    assert "Showing" in count_text
    print("PASS: Player Explorer Callback")

    print("\n=== TEST 6: Player Profile Callback (Per-90 vs Season Totals) ===")
    res_p90 = player_profile.update_player_profile("Bukayo Saka", metric_mode="per90")
    assert len(res_p90) == 7
    assert res_p90[0] is not None
    assert res_p90[4] is not None

    res_tot = player_profile.update_player_profile("Bukayo Saka", metric_mode="total")
    assert len(res_tot) == 7
    assert res_tot[0] is not None
    assert res_tot[4] is not None
    print("PASS: Player Profile Callback")

    print("\n=== TEST 7: Player Comparison Callback (Per-90 vs Season Totals) ===")
    warn_p90, rad_p90, bar_p90, tbl_p90, prof_p90 = player_comparison.update_comparison_views(["Erling Haaland", "Kylian Mbappé"], metric_mode="per90")
    assert tbl_p90 is not None
    assert rad_p90 is not None

    warn_tot, rad_tot, bar_tot, tbl_tot, prof_tot = player_comparison.update_comparison_views(["Erling Haaland", "Kylian Mbappé"], metric_mode="total")
    assert tbl_tot is not None
    assert rad_tot is not None
    print("PASS: Player Comparison Callback")

    print("\n=== TEST 8: All Page Layouts Evaluation ===")
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
    print("PASS: All 7 Page Layouts successfully instantiated!")

    print("\nALL PHASE 2 UNIT AND INTEGRATION TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_phase2()
