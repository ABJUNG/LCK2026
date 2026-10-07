"""외부 API나 인증 없이 경기 문서를 조립하는 순수 함수."""


def extract_source_identity(row):
    """원본 ID만 보존한다. 없거나 잘못된 ID를 팀/날짜로 추측하지 않는다."""
    identity = {}
    for source, target in (("MatchId", "seriesId"), ("GameId", "sourceGameId")):
        value = row.get(source)
        if isinstance(value, str) and value.strip():
            identity[target] = value.strip()
    return identity


def build_match_document(match_data, ai_review_text=None):
    # 포지션 순서 정렬 도우미
    role_order = {"Top": 1, "Jungle": 2, "Mid": 3, "Bot": 4, "Support": 5}
    
    team_a_sorted = sorted(match_data["team_A_players"], key=lambda x: role_order.get(x["role"], 99))
    team_b_sorted = sorted(match_data["team_B_players"], key=lambda x: role_order.get(x["role"], 99))

    doc_data = {
        **extract_source_identity({
            "MatchId": match_data.get("seriesId"),
            "GameId": match_data.get("sourceGameId"),
        }),
        "tournament": match_data["tournament"],
        "week": match_data["week_kr"],
        "weekEn": match_data["week_en"],
        "dateKST": match_data["date_kst"],
        "timeKST": match_data["time_kst"],
        "displayTitle": f"{match_data['tournament']} {match_data['week_kr']} | {match_data['date_kst']} {match_data['time_kst']} KST",
        "teamA": match_data["team_A"],
        "teamB": match_data["team_B"],
        "setNumber": match_data["set_number"],
        "status": "COMPLETED",
        "score": {"teamA": match_data["team_A_score"], "teamB": match_data["team_B_score"]},
        "players": {
            "teamA": team_a_sorted,
            "teamB": team_b_sorted
        },
        "bans": {
            "teamA": match_data["team_A_bans"],
            "teamB": match_data["team_B_bans"]
        },
        "aiReview": {
            "patchVersion": match_data["patch"],
            "summary": ai_review_text
        }
    }
    from competition import competition_info
    doc_data.update(competition_info(doc_data['tournament'], doc_data.get('seriesId', '')))
    doc_data['winnerTeam'] = match_data.get('winnerTeam')
    doc_data['objects'] = match_data.get('objects', {})
    doc_data['source'] = 'Leaguepedia'
    for field in ('gameLength', 'timeline', 'detailCoverage', 'teamSides'):
        doc_data[field] = match_data.get(field)
    doc_data['aiReview']['status'] = 'generated' if ai_review_text else 'not_generated'
    import hashlib
    import json
    doc_data['patchVersion'] = match_data['patch']
    evidence = {key: value for key, value in doc_data.items() if key != 'aiReview'}
    doc_data['dataFingerprint'] = hashlib.sha256(json.dumps(evidence, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return doc_data


def reconcile_review(document, previous):
    """재수집 시 기존 분석을 보존하되 변경된 데이터의 최신 분석으로 표시하지 않는다."""
    if document['aiReview']['status'] == 'generated':
        return document['aiReview']
    old = previous.get('aiReview') or {}
    if old.get('formatVersion'):
        from review import evidence_for, fingerprint
        if old.get('evidenceFingerprint') == fingerprint(evidence_for(document)):
            return old
        return {**old, 'status': 'stale'}
    if not old.get('summary'):
        return document['aiReview']
    if previous.get('dataFingerprint') == document['dataFingerprint']:
        return old
    return {**old, 'status': 'stale'}
