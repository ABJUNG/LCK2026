import json
import sys
import uuid
from contextlib import contextmanager
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from collection_job import run_job, worker_lock
from collect import discover, processor


@contextmanager
def test_folder():
    folder = Path(__file__).resolve().parents[1] / '.collection-runs' / ('test-' + uuid.uuid4().hex)
    folder.mkdir(parents=True)
    try:
        yield folder
    finally:
        for item in folder.iterdir():
            item.unlink()
        folder.rmdir()


class CollectionTests(unittest.TestCase):
    def test_failure_continues_and_resume_retries_only_unfinished(self):
        with test_folder() as folder:
            path = Path(folder) / 'job.json'
            job = {'series': [{'seriesId': sid, 'status': 'pending'} for sid in ('a', 'b', 'c')]}
            visited = []
            def first(entry):
                visited.append(entry['seriesId'])
                if entry['seriesId'] == 'b': raise RuntimeError('secret must not enter journal')
                return {'status': 'saved'}
            self.assertEqual(run_job(path, job, first), 1)
            self.assertEqual(visited, ['a', 'b', 'c'])
            self.assertNotIn('secret', path.read_text(encoding='utf-8'))
            resumed = json.loads(path.read_text(encoding='utf-8'))
            callback = Mock(return_value={'status': 'skipped'})
            self.assertEqual(run_job(path, resumed, callback), 0)
            self.assertEqual(callback.call_count, 1)
            self.assertEqual(callback.call_args.args[0]['seriesId'], 'b')
            self.assertEqual(resumed['series'][1]['attempts'], 2)
            self.assertNotIn('errorType', resumed['series'][1])

    def test_interrupt_retains_checkpoint_and_running_entry_can_resume(self):
        with test_folder() as folder:
            path = Path(folder) / 'job.json'
            job = {'series': [{'seriesId': 'a', 'status': 'pending'}]}
            with self.assertRaises(KeyboardInterrupt):
                run_job(path, job, Mock(side_effect=KeyboardInterrupt))
            restored = json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(restored['status'], 'interrupted')
            self.assertEqual(restored['series'][0]['status'], 'running')
            self.assertEqual(run_job(path, restored, Mock(return_value={'status': 'skipped'})), 0)

    def test_os_lock_rejects_overlap_and_releases_after_error(self):
        with test_folder() as folder:
            path = Path(folder) / 'worker.lock'
            with worker_lock(path):
                with self.assertRaises(ValueError):
                    with worker_lock(path): pass
            with self.assertRaises(RuntimeError):
                with worker_lock(path): raise RuntimeError()
            with worker_lock(path): pass

    def test_discovery_exact_scope_and_no_latest_limit(self):
        reader = Mock()
        row = {'MatchId': 'series', 'Tournament': 'LCK 2026 Season Playoffs', 'Team1': 'Dplus Kia', 'Team2': 'T1'}
        reader.pages.return_value = [dict(row, GameId=f'g{i}') for i in range(25)] + [dict(row, GameId='foreign', Team2='G2 Esports')]
        result = discover(reader, 'LCK_POSTSEASON', 2026, '2026-09-13')
        self.assertEqual(len(result[0]['expectedGameIds']), 25)
        where = reader.pages.call_args.kwargs['where']
        self.assertIn("DateTime_UTC >= '2026-09-12 15:00:00'", where)
        self.assertNotIn('LIKE', where)

    def test_duplicate_source_id_is_not_silent_success(self):
        reader = Mock()
        row = dict(GameId='g', MatchId='s', Tournament='Worlds 2026', Team1='T1', Team2='G2')
        reader.pages.return_value = [row, row]
        with self.assertRaises(ValueError): discover(reader, 'WORLDS', 2026)

    def test_existing_complete_series_skips_expensive_fetch_and_write(self):
        scope = {'competition': 'WORLDS', 'year': 2026}
        entry = {'seriesId': 's', 'tournament': 'Worlds 2026', 'expectedGameIds': ['g']}
        with patch('collect.saved_series', return_value=[{'sourceGameId': 'g'}]), patch('collect.verified_summary', return_value=True), patch('leaguepedia.fetch_matches') as fetch, patch('analyzer.save_documents') as save:
            result = processor(Mock(), Mock(), scope, True)(entry)
            self.assertEqual(result['status'], 'skipped')
            fetch.assert_not_called()
            save.assert_not_called()

    def test_missing_summary_repaired_and_postsave_verified(self):
        scope = {'competition': 'WORLDS', 'year': 2026}
        entry = {'seriesId': 's', 'tournament': 'Worlds 2026', 'expectedGameIds': ['g']}
        row = {'sourceGameId': 'g', 'detailCoverage': {'stats': 'available', 'timeline': 'unavailable'}}
        match = {'sourceGameId': 'g', 'tournament': 'Worlds 2026', 'set_number': '1'}
        with patch('collect.saved_series', return_value=[row]), patch('collect.verified_summary', side_effect=[False, True]), patch('leaguepedia.fetch_matches', return_value=[match]), patch('match_document.build_match_document', return_value=row.copy()), patch('analyzer.save_documents') as save:
            result = processor(Mock(), Mock(), scope, True)(entry)
            self.assertEqual(result['status'], 'saved')
            self.assertEqual(result['detailUnavailableGameIds'], ['g'])
            save.assert_called_once()

    def test_storage_rejects_truncated_zip_and_duplicate_input_before_batch(self):
        from analyzer import save_documents
        with patch('analyzer.connect_firestore') as connect:
            with self.assertRaises(ValueError): save_documents([{'sourceGameId': 'g'}], [])
            with self.assertRaises(ValueError): save_documents([{'sourceGameId': 'g'}, {'sourceGameId': 'g'}], [{}, {}])
            connect.return_value.batch.assert_not_called()

    def test_new_document_keys_depend_only_on_source_game_id(self):
        from analyzer import source_document_id
        self.assertEqual(source_document_id('game1'), source_document_id('game1'))
        self.assertNotEqual(source_document_id('game1'), source_document_id('game2'))
        self.assertNotIn('/', source_document_id('LCK/2026/Finals_1_1'))

    def test_gap_in_set_numbers_rejected_before_write(self):
        entry = {'seriesId': 's', 'tournament': 'Worlds 2026', 'expectedGameIds': ['g']}
        match = {'sourceGameId': 'g', 'tournament': 'Worlds 2026', 'set_number': '2'}
        with patch('collect.saved_series', return_value=[]), patch('leaguepedia.fetch_matches', return_value=[match]), patch('analyzer.save_documents') as save:
            with self.assertRaises(ValueError):
                processor(Mock(), Mock(), {'competition': 'WORLDS', 'year': 2026}, True)(entry)
            save.assert_not_called()


if __name__ == '__main__': unittest.main()
