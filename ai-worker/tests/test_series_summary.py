import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from series_summary import build_summaries

def match(n, flip=False):
    return dict(id=f'doc{n}', sourceGameId=f'g{n}', seriesId='series', tournament='LCK',
        dateKST='2026-08-16', timeKST='17:00', setNumber=n,
        teamA='B' if flip else 'A', teamB='A' if flip else 'B',
        score={'teamA': 0 if flip else 1, 'teamB': 2 if flip else 0}, players={'private': 'excluded'})

class SummariesTest(unittest.TestCase):
    def test_aligns_final_score_preserves_whole_series_and_omits_details(self):
        docs = [match(2, True), match(1)]
        summaries = build_summaries(docs)
        summary = next(iter(summaries.values()))
        self.assertEqual(summary['score'], {'teamA': 2, 'teamB': 0})
        self.assertEqual(summary['setIds'], ['doc1', 'doc2'])
        self.assertNotIn('players', summary)
        self.assertEqual(summaries, build_summaries(list(reversed(docs))))
    def test_duplicate_source_or_set_rejected(self):
        with self.assertRaises(ValueError): build_summaries([match(1), match(1)])
        second = match(1); second['sourceGameId'] = 'another'
        with self.assertRaises(ValueError): build_summaries([match(1), second])
    def test_legacy_excluded_team_conflict_rejected(self):
        legacy = match(1); legacy.pop('seriesId')
        self.assertEqual(build_summaries([legacy]), {})
        second = match(2); second['teamB'] = 'C'
        with self.assertRaises(ValueError): build_summaries([match(1), second])
