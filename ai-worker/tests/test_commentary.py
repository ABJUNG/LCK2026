import copy
import unittest
from test_review import document
from commentary import commentary_for
from review import evidence_for, facts_for, fingerprint, validate_report, VERSION
from match_document import reconcile_review


def fixture():
    doc = dict(document(), sourceGameId='game1', setNumber='1')
    doc['communityReview'] = {'url': 'https://namu.wiki/w/example', 'title': '결승 1세트',
        'sourceGameId': 'game1', 'setNumber': '1', 'providedAt': '2026-10-07',
        'attribution': '문서 기여자', 'license': 'CC BY-NC-SA 2.0 KR',
        'paragraphs': ['작성자는 바론 뒤 공성이 중요했다고 평가한다.']}
    return doc


class CommentaryTests(unittest.TestCase):
    def test_commentary_is_labeled_opinion_and_changes_evidence(self):
        doc = fixture()
        facts = facts_for(evidence_for(doc))
        self.assertEqual(facts[-1]['type'], 'community_opinion')
        self.assertEqual(facts[-1]['id'], 'N1')
        old = fingerprint(evidence_for(doc))
        doc['communityReview']['paragraphs'][0] = '다른 평가'
        self.assertNotEqual(old, fingerprint(evidence_for(doc)))

    def test_wrong_match_or_set_and_untrusted_link_rejected(self):
        for key, value in [('sourceGameId', 'game2'), ('setNumber', '2'), ('url', 'javascript:alert(1)')]:
            doc = fixture()
            doc['communityReview'][key] = value
            with self.assertRaises(ValueError): commentary_for(doc)

    def test_opinion_provenance_is_preserved_without_repeated_attribution_text(self):
        facts = facts_for(evidence_for(fixture()))
        claim = {'text': '바론 획득 후 공성으로 연결한 흐름.', 'factIds': ['N1']}
        report = {'summary': claim, 'draft': [claim], 'turningPoints': [claim]}
        self.assertEqual(validate_report(report, facts), report)
        self.assertEqual(facts[-1]['type'], 'community_opinion')

    def test_supplied_commentary_cannot_be_silently_ignored(self):
        facts = facts_for(evidence_for(fixture()))
        claim = {'text': '해석', 'factIds': ['F1']}
        with self.assertRaises(ValueError): validate_report({'summary': claim, 'draft': [claim], 'turningPoints': [claim]}, facts)

    def test_same_commentary_survives_reconciliation(self):
        doc = fixture()
        previous = copy.deepcopy(doc)
        previous['aiReview'] = {'status': 'generated', 'formatVersion': VERSION, 'evidenceFingerprint': fingerprint(evidence_for(doc))}
        doc['aiReview'] = {'status': 'not_generated'}
        self.assertEqual(reconcile_review(doc, previous)['status'], 'generated')
        doc['communityReview']['paragraphs'][0] = '변경된 관전평'
        self.assertEqual(reconcile_review(doc, previous)['status'], 'stale')
