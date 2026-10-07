import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from review_quality import screen_report, require_supported_claims

def report(text, ids=None):
    claim = {'text': text, 'factIds': ids or ['F1']}
    return {'summary': claim, 'draft': [{'text': '조합에서 기대할 역할.', 'factIds': ['F1']}],
            'turningPoints': [{'text': '포탑 기록을 확인합니다.', 'factIds': ['F1']}]}

class QualityTests(unittest.TestCase):
    def setUp(self):
        self.facts = [{'id': 'F1', 'text': '종료 골드와 오브젝트 기록'},
                      {'id': 'N1', 'type': 'community_opinion', 'text': '작성자의 교전 설명'}]
        self.evidence = {'timeline': {'status': 'available'}}
    def test_known_unsupported_claims_are_rejected(self):
        for text, code in [
            ('전 라인에서 우위를 점했습니다.', 'unsupported_lane_lead'),
            ('바론 뒤 골드 격차를 크게 벌렸습니다.', 'unsupported_gold_trend'),
            ('중반까지 팽팽한 경기였습니다.', 'unsupported_balance'),
            ('교전에서 화력으로 상대를 제압했습니다.', 'unsupported_fight_scene')]:
            with self.subTest(code=code):
                issues = screen_report(report(text), self.facts, self.evidence)['issues']
                self.assertIn(code, [i['code'] for i in issues])
                with self.assertRaises(ValueError): require_supported_claims(report(text), self.facts, self.evidence)
    def test_opinion_reference_permits_narrative_but_does_not_verify_truth(self):
        result = require_supported_claims(report('교전에서 승리했습니다.', ['N1']), self.facts, self.evidence)
        self.assertEqual(result['semanticVerification'], 'not_performed')
    def test_unrelated_opinion_in_another_claim_does_not_bypass_scope(self):
        value = report('골드 격차를 벌렸습니다.')
        value['draft'][0]['factIds'] = ['N1']
        with self.assertRaises(ValueError): require_supported_claims(value, self.facts, self.evidence)
    def test_sequence_requires_timeline_or_cited_narrative(self):
        with self.assertRaises(ValueError):
            require_supported_claims(report('바론 이후 포탑을 철거했습니다.'), self.facts, {'timeline': {'status': 'unavailable'}})
        require_supported_claims(report('바론 이후 포탑을 철거했습니다.', ['N1']), self.facts, {'timeline': {'status': 'unavailable'}})
    def test_readability_warning_is_not_a_truth_check_or_block(self):
        value = report('가' * 101)
        result = require_supported_claims(value, self.facts, self.evidence)
        self.assertEqual(result['issues'][0]['severity'], 'warning')
    def test_objective_sequence_and_final_gold_description_are_allowed(self):
        require_supported_claims(report('바론 획득 이후 포탑을 철거했습니다.'), self.facts, self.evidence)
        require_supported_claims(report('종료 골드가 상대보다 많았습니다.'), self.facts, self.evidence)


class FinalsRegressionTests(unittest.TestCase):
    def test_observed_six_unsupported_claims_are_detected_and_revisions_pass(self):
        import json
        from pathlib import Path
        from review import validate_report, facts_for
        cases = json.loads((Path(__file__).resolve().parents[2] / 'docs/evaluations/finals-review-2026-10-07.json').read_text(encoding='utf-8'))['cases']
        counts = []
        for case in cases:
            self.assertEqual(case['facts'], facts_for(case['evidence']))
            before = screen_report(case['beforeReport'], case['facts'], case['evidence'])
            counts.append(len([i for i in before['issues'] if i['severity'] == 'block']))
            validate_report(case['afterReport'], case['facts'])
            self.assertEqual(require_supported_claims(case['afterReport'], case['facts'], case['evidence'])['issues'], [])
        self.assertEqual(counts, [0, 1, 2, 3])

    def test_stale_facts_are_not_screened_as_current(self):
        from test_review import document
        from review import evidence_for, facts_for, fingerprint
        from review_quality import evaluate_document
        doc = document()
        doc['aiReview'] = {'status': 'generated', 'evidenceFingerprint': fingerprint(evidence_for(doc)), 'facts': facts_for(evidence_for(doc)), 'report': report('기록에 근거한 요약.')}
        self.assertEqual(evaluate_document(doc)['status'], 'screened')
        doc['winnerTeam'] = 'A'
        self.assertEqual(evaluate_document(doc)['issues'][0]['code'], 'stale_evidence')

    def test_generation_refuses_a_known_unsupported_claim(self):
        import json
        from unittest.mock import Mock
        from types import SimpleNamespace
        from test_review import document
        from review import generate_review
        client = Mock()
        client.models.generate_content.return_value = SimpleNamespace(
            text=json.dumps(report('전 라인에서 우위를 점했습니다.')),
            candidates=[SimpleNamespace(finish_reason='STOP')], usage_metadata=None)
        with self.assertRaises(ValueError): generate_review(document(), client, 'test')
