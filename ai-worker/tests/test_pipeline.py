import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from leaguepedia import kst_bounds, CargoReader, SourceError, assemble_matches, ROLES
from match_document import build_match_document, reconcile_review

def fixture():
    game = dict(GameId='g1', MatchId='s1', Tournament='LCK 2026', utcDateTime='2026-08-15 15:30:00', Team1='T1', Team2='Gen.G', Winner='1', setNumber='1', Patch='26.15')
    players = [dict(GameId='g1', Team=team, Role=role, Link=role, Champion='Garen', Kills='0', Deaths='1', Assists='2') for team in ('T1', 'Gen.G') for role in ROLES]
    return [game], [dict(GameId='g1')], players

class PipelineTests(unittest.TestCase):
    def test_kst_boundary(self):
        self.assertEqual(kst_bounds('2026-08-16'), ('2026-08-15 15:00:00', '2026-08-16 15:00:00'))
        self.assertEqual(assemble_matches(*fixture())[0]['date_kst'], '2026-08-16')
    def test_missing_is_not_zero(self):
        match = assemble_matches(*fixture())[0]
        self.assertIsNone(match['team_A_players'][0]['damage'])
        self.assertEqual(match['team_A_players'][0]['kills'], 0)
    def test_incomplete_roster_rejected(self):
        games, bans, players = fixture()
        with self.assertRaises(ValueError): assemble_matches(games, bans, players[:-1])
        players[0]['Role'] = 'Mid'
        with self.assertRaises(ValueError): assemble_matches(games, bans, players)
    def test_bounded_retry(self):
        error = RuntimeError('limited'); error.code = 'ratelimited'
        client, sleep = Mock(), Mock(); client.query.side_effect = error
        with self.assertRaises(SourceError): CargoReader(client, sleep).query()
        self.assertEqual(client.query.call_count, 3)
    def test_changed_patch_invalidates_review(self):
        match = assemble_matches(*fixture())[0]
        old = build_match_document(match, 'report')
        self.assertEqual(reconcile_review(build_match_document(match), old)['summary'], 'report')
        match['patch'] = '26.16'
        self.assertEqual(reconcile_review(build_match_document(match), old)['status'], 'stale')
