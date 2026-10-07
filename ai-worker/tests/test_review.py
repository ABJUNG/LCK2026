import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from review import evidence_for, facts_for, fingerprint, validate_report, generate_review, VERSION
from analyze_saved import process_set
from match_document import reconcile_review


def document():
    players = [{'name': f'p{i}', 'champion': 'Ahri', 'role': 'Mid', 'damage': 100 + i,
                'kills': 1, 'deaths': 2, 'assists': 3, 'build': {'secret': 'exclude'}} for i in range(5)]
    return {'teamA': 'A', 'teamB': 'B', 'winnerTeam': 'B', 'players': {'teamA': players, 'teamB': copy.deepcopy(players)},
            'objects': {'teamA': {'gold': None}, 'teamB': {'gold': 1000}}, 'timeline': {'status': 'unavailable', 'events': [{'timestampMs': 1}]}}


class ReviewTests(unittest.TestCase):
    def test_evidence_excludes_display_and_build_data_and_unavailable_events(self):
        doc = document()
        evidence = evidence_for(doc)
        self.assertNotIn('build', evidence['players']['teamA'][0])
        self.assertEqual(evidence['timeline']['events'], [])
        self.assertIsNone(evidence['objects']['teamA']['gold'])
        changed = dict(doc, fetchedAt='tomorrow', id='new', displayTitle='new')
        self.assertEqual(fingerprint(evidence), fingerprint(evidence_for(changed)))
        changed['winnerTeam'] = 'A'
        self.assertNotEqual(fingerprint(evidence), fingerprint(evidence_for(changed)))

    def test_facts_come_from_data_and_unknown_is_not_zero(self):
        facts = facts_for(evidence_for(document()))
        self.assertIn('B 승리', facts[0]['text'])
        self.assertFalse(any('A: 종료 골드 0' in f['text'] for f in facts))

    def test_unknown_fact_reference_and_empty_report_rejected(self):
        claim = {'text': '해석', 'factIds': ['F1']}
        report = {'summary': claim, 'draft': [claim], 'turningPoints': [claim]}
        self.assertEqual(validate_report(report, [{'id': 'F1'}]), report)
        with self.assertRaises(ValueError): validate_report(report, [{'id': 'F2'}])
        with self.assertRaises(ValueError): validate_report(dict(report, draft=[]), [{'id': 'F1'}])

    def test_failure_saved_separately_from_match_data(self):
        doc = document()
        before = copy.deepcopy(doc)
        states = []
        result = process_set(doc, Mock(side_effect=RuntimeError('API key must not leak')), states.append)
        self.assertEqual(result, 'failed')
        self.assertEqual([s['status'] for s in states], ['pending', 'running', 'failed'])
        self.assertEqual(states[-1]['errorType'], 'RuntimeError')
        self.assertNotIn('API key', str(states))
        self.assertEqual(doc, before)

    def test_existing_report_is_not_regenerated_without_changed_evidence(self):
        doc = document()
        doc['aiReview'] = {'status': 'generated', 'formatVersion': VERSION, 'evidenceFingerprint': fingerprint(evidence_for(doc))}
        generate, persist = Mock(), Mock()
        self.assertEqual(process_set(doc, generate, persist), 'skipped')
        generate.assert_not_called()
        persist.assert_not_called()

    def test_collection_preserves_same_review_but_marks_changed_evidence_stale(self):
        doc = document()
        previous = dict(doc, aiReview={'status': 'generated', 'formatVersion': VERSION, 'summary': '해석', 'evidenceFingerprint': fingerprint(evidence_for(doc))})
        doc['aiReview'] = {'status': 'not_generated'}
        self.assertEqual(reconcile_review(doc, previous)['status'], 'generated')
        doc['winnerTeam'] = 'A'
        self.assertEqual(reconcile_review(doc, previous)['status'], 'stale')

    def test_interrupted_analysis_returns_to_pending_for_retry(self):
        states = []
        with self.assertRaises(KeyboardInterrupt):
            process_set(document(), Mock(side_effect=KeyboardInterrupt), states.append)
        self.assertEqual(states[-1]['status'], 'pending')
        self.assertIn('interruptedAt', states[-1])

    def test_generate_rejects_invalid_evidence_references(self):
        import json
        claim = {'text': '해석', 'factIds': ['missing']}
        client = Mock()
        client.models.generate_content.return_value = SimpleNamespace(text=json.dumps({'summary': claim, 'draft': [claim], 'turningPoints': [claim]}), candidates=[SimpleNamespace(finish_reason='STOP')], usage_metadata=None)
        with self.assertRaises(ValueError): generate_review(document(), client, 'test')

    def test_transaction_refuses_report_for_changed_match(self):
        from analyze_saved import store_review
        from unittest.mock import patch
        doc = document()
        expected = fingerprint(evidence_for(doc))
        doc['winnerTeam'] = 'A'
        db, ref = Mock(), Mock()
        ref.get.return_value.to_dict.return_value = doc
        with patch('google.cloud.firestore.transactional', side_effect=lambda f: f):
            with self.assertRaises(ValueError): store_review(db, ref, expected, {'status': 'generated'})
        db.transaction.return_value.update.assert_not_called()

    def test_stalled_sdk_is_terminated_at_wall_clock_deadline(self):
        from analyze_saved import bounded_review
        from unittest.mock import patch
        context, receiving, sending, process = Mock(), Mock(), Mock(), Mock()
        context.Pipe.return_value = (receiving, sending)
        context.Process.return_value = process
        receiving.poll.return_value = False
        process.is_alive.return_value = True
        with patch('multiprocessing.get_context', return_value=context):
            with self.assertRaises(TimeoutError): bounded_review(document(), 'test', deadline=1)
        process.terminate.assert_called_once()

    def test_rate_limit_retries_are_bounded(self):
        client, sleep = Mock(), Mock()
        exc = RuntimeError('limited')
        exc.code = 429
        client.models.generate_content.side_effect = exc
        with self.assertRaises(RuntimeError): generate_review(document(), client, 'test', sleep)
        self.assertEqual(client.models.generate_content.call_count, 3)
        self.assertEqual(sleep.call_count, 2)


class GenerationRecoveryTests(unittest.TestCase):
    def response(self, report, reason='STOP'):
        import json
        return SimpleNamespace(text=json.dumps(report), candidates=[SimpleNamespace(finish_reason=reason)],
            usage_metadata=SimpleNamespace(prompt_token_count=100, candidates_token_count=50, thoughts_token_count=10, total_token_count=160))

    def report(self, ids=None, text='해석으로 볼 수 있습니다.'):
        claim = {'text': text, 'factIds': ids or ['F1']}
        return {'summary': dict(claim), 'draft': [dict(claim)], 'turningPoints': [dict(claim)]}

    def test_incomplete_json_is_rejected_even_when_it_parses(self):
        client = Mock()
        client.models.generate_content.return_value = self.response(self.report(), reason='MAX_TOKENS')
        with self.assertRaises(ValueError): generate_review(document(), client, 'test')
        self.assertEqual(client.models.generate_content.call_count, 1)

    def test_generated_opinion_keeps_source_without_injecting_repeated_words(self):
        from test_commentary import fixture
        client = Mock()
        client.models.generate_content.return_value = self.response(self.report(['N1']))
        review = generate_review(fixture(), client, 'test')
        self.assertEqual(review['summary'], '해석으로 볼 수 있습니다.')
        self.assertEqual(review['report']['summary']['factIds'], ['N1'])
        self.assertEqual(review['usage']['totalTokens'], 160)
        self.assertEqual(review['usage']['thoughtTokens'], 10)
        self.assertEqual(review['commentarySource']['verification'], 'user_provided_unverified')
        self.assertEqual(review['promptVersion'], 'spectator-v7')

    def test_unknown_opinion_reference_is_not_repaired_into_valid_evidence(self):
        facts = [{'id':'N1','type':'community_opinion'}]
        report = self.report(['N999'])
        with self.assertRaises(ValueError): validate_report(report, facts)

    def test_transport_timeout_retries_remain_bounded(self):
        import httpx
        client, sleep = Mock(), Mock()
        client.models.generate_content.side_effect = httpx.ReadTimeout('secret must not be saved')
        with self.assertRaises(httpx.ReadTimeout): generate_review(document(), client, 'test', sleep)
        self.assertEqual(client.models.generate_content.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_child_failure_preserves_safe_type_and_code(self):
        from analyze_saved import RemoteReviewError
        states=[]
        self.assertEqual(process_set(document(), Mock(side_effect=RemoteReviewError({'type':'ServerError','code':503})), states.append), 'failed')
        self.assertEqual(states[-1]['errorType'], 'ServerError')
        self.assertEqual(states[-1]['errorCode'], 503)


class ConciseWordingTests(unittest.TestCase):
    def test_only_known_opinion_labels_are_removed_without_altering_evidence(self):
        from review import clean_report_wording
        known = {'text': '관전평에 따르면, 바론 뒤 공성을 이어갔습니다(관전평 참고).', 'factIds': ['N1']}
        unknown = {'text': '관전평에서는 다른 사건을 설명합니다.', 'factIds': ['N999']}
        report = {'summary': known, 'draft': [unknown], 'turningPoints': [known]}
        before = copy.deepcopy(report)
        cleaned = clean_report_wording(report, [{'id': 'N1', 'type': 'community_opinion'}])
        self.assertEqual(cleaned['summary']['text'], '바론 뒤 공성을 이어갔습니다.')
        self.assertEqual(cleaned['summary']['factIds'], ['N1'])
        self.assertEqual(cleaned['draft'][0], unknown)
        self.assertEqual(report, before)


    def test_reference_ids_are_removed_but_game_details_are_preserved(self):
        from review import clean_report_wording
        claim = {'text': '교전에서 승리했습니다(N1, F1). 기록(13/13)은 유지합니다.', 'factIds': ['N1', 'F1']}
        report = {'summary': claim, 'draft': [claim], 'turningPoints': [claim]}
        cleaned = clean_report_wording(report, [{'id': 'N1', 'type': 'community_opinion'}, {'id': 'F1'}])
        self.assertEqual(cleaned['summary']['text'], '교전에서 승리했습니다. 기록(13/13)은 유지합니다.')
        self.assertEqual(cleaned['summary']['factIds'], ['N1', 'F1'])
