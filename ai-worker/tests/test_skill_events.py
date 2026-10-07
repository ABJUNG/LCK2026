import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from postgame import player_skill_events

class SkillEventsTest(unittest.TestCase):
    def test_ignores_unassigned_and_invalid_slots_and_keeps_player_order(self):
        data = {'frames': [{'events': [
            {'type': 'SKILL_LEVEL_UP', 'participantId': 1, 'skillSlot': 4, 'timestamp': 900},
            {'type': 'SKILL_LEVEL_UP', 'participantId': 0, 'skillSlot': 4, 'timestamp': 0},
            {'type': 'SKILL_LEVEL_UP', 'participantId': 1, 'skillSlot': 1, 'timestamp': 100},
            {'type': 'SKILL_LEVEL_UP', 'participantId': 1, 'skillSlot': 5, 'timestamp': 200},
            {'type': 'ITEM_PURCHASED', 'participantId': 1, 'timestamp': 0},
        ]}]}
        self.assertEqual(player_skill_events(data, [1, 2]), {
            1: [{'skillSlot': 1, 'timestampMs': 100}, {'skillSlot': 4, 'timestampMs': 900}], 2: []})
