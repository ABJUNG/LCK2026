import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from postgame import parse_timeline, verified_teams, verified_sides

class TimelineTests(unittest.TestCase):
    def data(self, events):
        return {'endOfGameResult': 'GameComplete', 'frames': [{'events': events + [{'type': 'GAME_END', 'gameId': 1, 'timestamp': 60000}]}]}
    def parse(self, events):
        return parse_timeline(self.data(events), {'gameId': 1, 'gameDuration': 60}, {'team_A': 'T1', 'team_B': 'Gen.G'}, {100: 'A', 200: 'B'})
    def test_plate_owner_is_opponent_and_minion_last_hit_counts(self):
        result, plates, _ = self.parse([{'type': 'TURRET_PLATE_DESTROYED', 'teamId': 200, 'killerId': 0, 'laneType': 'TOP_LANE', 'timestamp': 10000}])
        self.assertEqual(plates['A']['total'], 1)
        self.assertEqual(plates['B']['total'], 0)
        self.assertEqual(result['events'][0]['team'], 'T1')
    def test_soul_transformation_is_not_acquisition(self):
        result, _, souls = self.parse([{'type': 'DRAGON_SOUL_GIVEN', 'teamId': 0, 'name': 'Infernal', 'timestamp': 1000}, {'type': 'DRAGON_SOUL_GIVEN', 'teamId': 200, 'name': 'Infernal', 'timestamp': 2000}])
        self.assertEqual(len(result['events']), 1)
        self.assertEqual(souls, {'A': None, 'B': 'Infernal'})
    def test_incomplete_timeline_does_not_produce_zero(self):
        with self.assertRaises(ValueError): parse_timeline({'frames': []}, {'gameId': 1}, {}, {})
    def test_wrong_game_rejected(self):
        with self.assertRaises(ValueError): parse_timeline(self.data([]), {'gameId': 2}, {}, {})
    def test_unrecognized_owner_rejected(self):
        with self.assertRaises(ValueError): self.parse([{'type': 'TURRET_PLATE_DESTROYED', 'teamId': 0}])
    def test_team_mapping_not_array_position(self):
        match = {'team_A_players': [{'champion': f'Champion{i}'} for i in range(5)], 'team_B_players': [{'champion': f'Champion{i}'} for i in range(5, 10)]}
        stats = {'participants': [{'participantId': i + 1, 'championName': f'Champion{i}', 'teamId': 200 if i < 5 else 100} for i in range(10)]}
        self.assertEqual(verified_teams(stats, match), {200: 'A', 100: 'B'})
        self.assertEqual(verified_sides(stats, match), {'teamA': 'RED', 'teamB': 'BLUE'})
        stats['participants'].reverse()
        self.assertEqual(verified_sides(stats, match), {'teamA': 'RED', 'teamB': 'BLUE'})


class PlayerBuildTests(unittest.TestCase):
    def test_ids_and_runes_without_account_information(self):
        from postgame import player_build
        build = player_build({'spell1Id': 4, 'spell2Id': 12, 'item0': 1001, 'puuid': 'secret', 'perks': {'styles': [{'style': 8000, 'selections': [{'perk': 8010}]}], 'statPerks': {'offense': 5008}}}, '16.15.1')
        self.assertEqual(build['spellIds'], [4, 12])
        self.assertEqual(build['runeStyles'][0]['selectedIds'], [8010])
        self.assertNotIn('puuid', build)
        self.assertEqual(build['timelineStatus'], 'unavailable')
    def test_player_scope_and_undo_preserve_original_order(self):
        from postgame import player_item_events
        data = {'frames': [{'events': [
            {'type': 'ITEM_PURCHASED', 'participantId': 0, 'itemId': 999, 'timestamp': 0},
            {'type': 'ITEM_PURCHASED', 'participantId': 1, 'itemId': 1054, 'timestamp': 1000},
            {'type': 'ITEM_UNDO', 'participantId': 1, 'beforeId': 1054, 'afterId': 0, 'timestamp': 1000},
            {'type': 'ITEM_DESTROYED', 'participantId': 1, 'itemId': 1054, 'timestamp': 2000},
            {'type': 'ITEM_SOLD', 'participantId': 2, 'itemId': 1001, 'timestamp': 3000}]}]}
        result = player_item_events(data, [1, 2])
        self.assertEqual([e['type'] for e in result[1]], ['ITEM_PURCHASED', 'ITEM_UNDO'])
        self.assertEqual(result[1][1]['beforeId'], 1054)
        self.assertEqual(result[2][0]['type'], 'ITEM_SOLD')
