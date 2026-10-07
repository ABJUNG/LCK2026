import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from match_document import extract_source_identity, build_match_document


def fixture():
    return {
        "tournament": "LCK", "week_kr": "1주차", "week_en": "Week 1",
        "date_kst": "2026-09-22", "time_kst": "17:00", "patch": "26.15",
        "team_A": "Gen.G", "team_B": "T1", "set_number": "1",
        "team_A_score": 1, "team_B_score": 0,
        "team_A_players": [{"name": "Mid player", "role": "Mid"}, {"name": "Top player", "role": "Top"}],
        "team_B_players": [], "team_A_bans": ["Lux"], "team_B_bans": ["Garen"],
    }


class MatchDocumentTests(unittest.TestCase):
    def test_identity_survives_source_to_document(self):
        source = {"MatchId": " LCK/2026/Week 1/Match 1 ", "GameId": "LCK/2026/Week 1/Match 1/1"}
        match = {**fixture(), **extract_source_identity(source)}
        doc = build_match_document(match, "리포트")
        self.assertEqual(doc["seriesId"], "LCK/2026/Week 1/Match 1")
        self.assertEqual(doc["sourceGameId"], source["GameId"])
        self.assertEqual(doc["aiReview"]["summary"], "리포트")

    def test_sets_share_series_but_have_distinct_game_ids(self):
        first = extract_source_identity({"MatchId": "series-1", "GameId": "game-1"})
        second = extract_source_identity({"MatchId": "series-1", "GameId": "game-2"})
        self.assertEqual(first["seriesId"], second["seriesId"])
        self.assertNotEqual(first["sourceGameId"], second["sourceGameId"])

    def test_missing_invalid_identity_is_not_invented(self):
        for value in [None, "", "  ", 12, []]:
            self.assertEqual(extract_source_identity({"MatchId": value, "GameId": value}), {})
        doc = build_match_document(fixture(), "legacy")
        self.assertNotIn("seriesId", doc)
        self.assertNotIn("sourceGameId", doc)

    def test_existing_content_and_input_preserved(self):
        match = fixture()
        before = copy.deepcopy(match)
        doc = build_match_document(match, "기존 분석")
        self.assertEqual(match, before)
        self.assertEqual([p["role"] for p in doc["players"]["teamA"]], ["Top", "Mid"])
        self.assertEqual(doc["score"], {"teamA": 1, "teamB": 0})
        self.assertEqual(doc["bans"]["teamA"], ["Lux"])


if __name__ == "__main__":
    unittest.main()
