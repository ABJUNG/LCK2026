"""Validated, manually supplied commentary; this module never fetches a website."""
from urllib.parse import urlparse


def commentary_for(doc):
    source = doc.get('communityReview')
    if not source:
        return None
    if not isinstance(source, dict):
        raise ValueError('관전평 형식 불일치')
    url = source.get('url', '')
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.netloc != 'namu.wiki' or not parsed.path.startswith('/w/'):
        raise ValueError('관전평 출처 URL 불일치')
    if not source.get('sourceGameId') or source.get('sourceGameId') != doc.get('sourceGameId'):
        raise ValueError('관전평의 원본 경기 ID 불일치')
    if source.get('setNumber') != doc.get('setNumber'):
        raise ValueError('관전평 세트 불일치')
    paragraphs = source.get('paragraphs')
    if not isinstance(paragraphs, list) or not 1 <= len(paragraphs) <= 12:
        raise ValueError('관전평 개수 불일치')
    if any(not isinstance(p, str) or not 1 <= len(p.strip()) <= 1000 for p in paragraphs):
        raise ValueError('관전평 길이 불일치')
    for field in ('title', 'providedAt', 'attribution', 'license'):
        if not isinstance(source.get(field), str) or not 1 <= len(source[field]) <= 300:
            raise ValueError('관전평 출처 정보 부족')
    return {**{k: source[k] for k in ('url', 'title', 'providedAt', 'attribution', 'license')},
            'paragraphs': paragraphs, 'verification': 'user_provided_unverified',
            'sourceGameId': source['sourceGameId'], 'setNumber': source['setNumber']}
