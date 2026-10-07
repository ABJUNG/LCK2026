import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from competition import competition_info, source_names

class CompetitionTest(unittest.TestCase):
    def test_postseason_and_finals(self):
        info = competition_info('LCK 2026 Season Playoffs', 'LCK/2026 Season/Season Playoffs_Finals_1')
        self.assertEqual(info['competitionId'], 'LCK_POSTSEASON')
        self.assertEqual(info['stage'], 'FINALS')
        self.assertEqual(competition_info('LCK 2026 Season Play-In')['stage'], 'PLAY_IN')
    def test_exact_names_exclude_academy_showmatches_and_other_world_events(self):
        for name in ['LCK CL 2026 Season Playoffs', 'Esports World Cup 2026', 'World Star Challengers Invitational 2026', 'MSI 2026: LoL Classic Showmatch']:
            self.assertEqual(competition_info(name), {})
        self.assertEqual(competition_info('Worlds 2026 Main Event')['league'], 'WORLDS')
    def test_unsupported_regions_and_seasons_rejected(self):
        for league, year in [('LPL',2026), ('LCK',2025), ('WORLDS',2027)]:
            with self.assertRaises(ValueError): source_names(league,year)

    def test_team_capitalization_does_not_drop_dplus_series(self):
        from leaguepedia import is_lck
        self.assertTrue(is_lck({'Team1':'Dplus Kia','Team2':'KT Rolster'}))
        self.assertFalse(is_lck({'Team1':'Dplus Kia','Team2':'Foreign Team'}))
