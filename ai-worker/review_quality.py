"""Conservative screening of known unsupported claims, not semantic truth verification."""
import re

VERSION = 'quality-v1'


def screen_report(report, facts, evidence):
    fact_map = {f['id']: f for f in facts}
    issues = []
    claims = [('summary', report['summary'])]
    for section in ('draft', 'turningPoints'):
        claims.extend((f'{section}.{i}', c) for i, c in enumerate(report[section]))
    seen = {}
    for location, claim in claims:
        text = claim['text'].strip()
        cited = [fact_map[i] for i in claim['factIds'] if i in fact_map]
        opinion = any(f.get('type') == 'community_opinion' for f in cited)
        def add(code, reason, severity='block'):
            issues.append({'location': location, 'code': code, 'severity': severity, 'reason': reason})
        if text in seen:
            add('repeated_claim', '같은 문장이 여러 항목에 반복됐습니다.', 'warning')
        seen[text] = location
        if len(text) > 100:
            add('long_claim', '짧은 문장 목표인 100자를 넘었습니다.', 'warning')
        if opinion:
            continue  # Narrative claims still require a source/sequence review.
        if re.search(r'(?:전|모든)\s*라인.*(?:우위|압도|승리)|라인전.*(?:이겼|승리|압도)', text):
            add('unsupported_lane_lead', '종료 스탯·오브젝트 기록으로 라인전 우위를 판단할 수 없습니다.')
        if re.search(r'(?:골드|성장)\s*(?:격차|차이).*(?:벌|넓|줄|뒤집|역전)', text):
            add('unsupported_gold_trend', '시점별 골드 변화가 분석 근거에 없습니다.')
        if re.search(r'팽팽|대등|치열한 접전', text):
            add('unsupported_balance', '오브젝트 획득 기록만으로 경기의 균형을 판단할 수 없습니다.')
        if location != 'draft' and not location.startswith('draft.'):
            if re.search(r'교전.*(?:승리|제압|화력)|파상공세', text):
                add('unsupported_fight_scene', '교전 장면·결과를 설명할 관전평 또는 교전 기록이 없습니다.')
            if evidence.get('timeline', {}).get('status') != 'available' and re.search(r'이후|직후|이어|연속', text):
                add('unsupported_sequence', '타임라인·관전평이 없으므로 사건 순서를 확인할 수 없습니다.')
    return {'version': VERSION, 'issues': issues, 'semanticVerification': 'not_performed'}


def require_supported_claims(report, facts, evidence):
    result = screen_report(report, facts, evidence)
    blocked = [i for i in result['issues'] if i['severity'] == 'block']
    if blocked:
        raise ValueError('분석 근거 범위 초과: ' + ','.join(sorted({i['code'] for i in blocked})))
    return result


def evaluate_document(doc):
    from review import evidence_for, facts_for, fingerprint, validate_report
    review = doc.get('aiReview') or {}
    evidence = evidence_for(doc)
    facts = facts_for(evidence)
    issues = []
    if review.get('status') != 'generated':
        issues.append({'code': 'review_unavailable', 'severity': 'block', 'location': 'review', 'reason': '생성된 분석이 없습니다.'})
    elif review.get('evidenceFingerprint') != fingerprint(evidence) or review.get('facts') != facts:
        issues.append({'code': 'stale_evidence', 'severity': 'block', 'location': 'review', 'reason': '현재 경기 근거와 저장된 분석 근거가 다릅니다.'})
    else:
        try:
            validate_report(review.get('report'), facts)
        except ValueError:
            issues.append({'code': 'invalid_report', 'severity': 'block', 'location': 'report', 'reason': '분석 구조·근거 ID가 유효하지 않습니다.'})
        else:
            issues.extend(screen_report(review['report'], facts, evidence)['issues'])
    return {'setNumber': doc.get('setNumber'), 'sourceGameId': doc.get('sourceGameId'),
            'status': 'needs_correction' if any(i['severity'] == 'block' for i in issues) else 'screened',
            'version': VERSION, 'issues': issues, 'semanticVerification': 'not_performed',
            'humanReviewStatus': review.get('humanReviewStatus', 'not_reviewed')}
