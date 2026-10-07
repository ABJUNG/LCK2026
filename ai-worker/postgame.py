"""Leaguepedia V5 경기 JSON의 공개 경기 스탯만 선별한다. 계정 식별자는 저장하지 않는다."""
import json
import re

PLAYER_STATS = ('champLevel', 'totalDamageTaken', 'damageSelfMitigated', 'physicalDamageDealtToChampions',
    'magicDamageDealtToChampions', 'trueDamageDealtToChampions', 'damageDealtToTurrets',
    'damageDealtToObjectives', 'totalHeal', 'totalHealsOnTeammates', 'totalDamageShieldedOnTeammates',
    'wardsPlaced', 'wardsKilled', 'detectorWardsPlaced', 'timeCCingOthers', 'totalTimeSpentDead',
    'neutralMinionsKilled', 'totalMinionsKilled', 'objectivesStolen', 'doubleKills', 'tripleKills', 'quadraKills', 'pentaKills')


def champion_key(value):
    value = re.sub(r'[^a-z0-9]', '', value.lower())
    return {'wukong': 'monkeyking', 'renataglasc': 'renata', 'nunuwillump': 'nunu'}.get(value, value)


def verified_teams(stats, match):
    players = stats.get('participants', [])
    if len(players) != 10 or len({p.get('participantId') for p in players}) != 10:
        raise ValueError('JSON participant identity mismatch')
    mapping = {}
    for side in ('A', 'B'):
        roster = match[f'team_{side}_players']
        expected = {champion_key(p['champion']) for p in roster}
        found = [team for team in (100, 200) if {champion_key(p['championName']) for p in players if p['teamId'] == team} == expected]
        if len(found) != 1: raise ValueError('JSON team mismatch')
        mapping[found[0]] = side
    if len(mapping) != 2: raise ValueError('JSON duplicate team')
    return mapping


def verified_sides(stats, match):
    """Use participant team IDs after matching all five champions to each team."""
    return {f"team{side}": "BLUE" if team_id == 100 else "RED"
            for team_id, side in verified_teams(stats, match).items()}


def read_json(reader, title):
    if not title: return None
    response = reader.client.client.api('query', prop='revisions', titles=title, rvprop='content', rvslots='main')
    pages = list(response.get('query', {}).get('pages', {}).values())
    if len(pages) != 1 or 'missing' in pages[0]: return None
    raw = pages[0].get('revisions', [{}])[0].get('slots', {}).get('main', {}).get('*')
    return json.loads(raw) if raw else None


def parse_timeline(data, stats, match, mapping):
    events = [e for frame in data.get('frames', []) for e in frame.get('events', [])]
    ends = [e for e in events if e.get('type') == 'GAME_END']
    if data.get('endOfGameResult') != 'GameComplete' or len(ends) != 1 or ends[0].get('gameId') != stats.get('gameId'):
        raise ValueError('Incomplete or mismatched timeline')
    if abs(ends[0].get('timestamp', 0) / 1000 - stats.get('gameDuration', 0)) > 10:
        raise ValueError('Timeline duration mismatch')
    result = []
    plates = {side: {'total': 0, 'TOP_LANE': 0, 'MID_LANE': 0, 'BOT_LANE': 0} for side in ('A', 'B')}
    souls = {'A': None, 'B': None}
    for e in events:
        kind = e.get('type')
        if kind in ('TURRET_PLATE_DESTROYED', 'BUILDING_KILL'):
            # teamId is the destroyed structure owner, including minion last-hits.
            owner = e.get('teamId')
            if owner not in mapping: raise ValueError('Unknown structure owner')
            side = mapping[300 - owner]
            label = 'plate' if kind == 'TURRET_PLATE_DESTROYED' else e.get('buildingType')
            if label == 'plate':
                lane = e.get('laneType')
                if lane not in plates[side]: raise ValueError('Unknown plate lane')
                plates[side]['total'] += 1; plates[side][lane] += 1
        elif kind == 'ELITE_MONSTER_KILL':
            team = e.get('killerTeamId')
            if team not in mapping: raise ValueError('Unknown monster killer team')
            side = mapping[team]
            label = e.get('monsterSubType') or e.get('monsterType')
        elif kind == 'DRAGON_SOUL_GIVEN':
            if e.get('teamId') == 0: continue  # rift transformation, not a team's soul acquisition
            if e.get('teamId') not in mapping: raise ValueError('Unknown soul team')
            side = mapping[e['teamId']]; label = 'soul'
            souls[side] = e.get('name')
        else: continue
        result.append({'timestampMs': e['timestamp'], 'team': match[f'team_{side}'], 'kind': label,
                       'lane': e.get('laneType'), 'subtype': e.get('name') if label == 'soul' else e.get('towerType')})
    return {'status': 'available', 'events': sorted(result, key=lambda e: e['timestampMs'])}, plates, souls


def player_build(participant, game_version):
    perks = participant.get('perks') or {}
    return {
        'gameVersion': game_version,
        'finalItemIds': [participant.get(f'item{i}') for i in range(7)],
        'spellIds': [participant.get('summoner1Id', participant.get('spell1Id')), participant.get('summoner2Id', participant.get('spell2Id'))],
        'runeStyles': [{'style': style.get('style'), 'description': style.get('description'),
                        'selectedIds': [selection.get('perk') for selection in style.get('selections', [])]}
                       for style in perks.get('styles', [])],
        'statShards': {slot: perks.get('statPerks', {}).get(slot) for slot in ('offense', 'flex', 'defense')},
        'timelineStatus': 'unavailable', 'itemEvents': [],
    }


def player_item_events(data, participant_ids):
    """Preserve order and undo events; do not mistake component destruction for a sale."""
    result = {pid: [] for pid in participant_ids}
    for frame in data.get('frames', []):
        for event in frame.get('events', []):
            pid, kind = event.get('participantId'), event.get('type')
            if pid not in result or kind not in ('ITEM_PURCHASED', 'ITEM_SOLD', 'ITEM_UNDO'):
                continue
            record = {'type': kind, 'timestampMs': event['timestamp']}
            if kind == 'ITEM_UNDO':
                record.update(beforeId=event.get('beforeId'), afterId=event.get('afterId'))
            else:
                record['itemId'] = event.get('itemId')
            result[pid].append(record)
    return {pid: sorted(events, key=lambda e: e['timestampMs']) for pid, events in result.items()}


def player_skill_events(data, participant_ids):
    result = {pid: [] for pid in participant_ids}
    for frame in data.get('frames', []):
        for event in frame.get('events', []):
            pid = event.get('participantId')
            if pid not in result or event.get('type') != 'SKILL_LEVEL_UP' or event.get('skillSlot') not in (1, 2, 3, 4):
                continue
            result[pid].append({'skillSlot': event['skillSlot'], 'timestampMs': event['timestamp']})
    return {pid: sorted(events, key=lambda e: e['timestampMs']) for pid, events in result.items()}


def enrich_matches(reader, matches, games):
    from leaguepedia import quote
    by_id = {g['GameId']: g for g in games}
    for match in matches:
        match['detailCoverage'] = {'stats': 'unavailable', 'timeline': 'unavailable'}
        match['timeline'] = {'status': 'unavailable', 'events': []}
        for side in ('A', 'B'):
            match['objects'][f'team{side}'].update(plates=None, soul=None)
        rpgid = by_id[match['sourceGameId']].get('RiotPlatformGameId')
        if not rpgid: continue
        try:
            rows = reader.query(tables='PostgameJsonMetadata', fields='GameId,StatsPage,TimelinePage,RiotVersion',
                                where=f'RiotPlatformGameId={quote(rpgid)}', limit=2)
            if len(rows) != 1 or rows[0].get('GameId') != match['sourceGameId'] or str(rows[0].get('RiotVersion')) != '5':
                continue
            metadata = rows[0]
            stats = read_json(reader, metadata.get('StatsPage'))
            if not stats: continue
            if f"{stats.get('platformId')}_{stats.get('gameId')}" != rpgid or stats.get('endOfGameResult') != 'GameComplete':
                raise ValueError('Wrong game JSON')
            mapping = verified_teams(stats, match)
            additions = []
            player_by_id = {}
            for participant in stats['participants']:
                side = mapping[participant['teamId']]
                player = next(p for p in match[f'team_{side}_players'] if champion_key(p['champion']) == champion_key(participant['championName']))
                if any(player[k] != participant.get(k) for k in ('kills', 'deaths', 'assists')):
                    raise ValueError('Scoreboard and JSON disagree')
                additions.append((player, {key: participant.get(key) for key in PLAYER_STATS}, player_build(participant, stats.get('gameVersion'))))
                player_by_id[participant['participantId']] = player
            for player, details, build in additions:
                player['details'] = details
                player['build'] = build
            match['teamSides'] = verified_sides(stats, match)
            match['detailCoverage']['stats'] = 'available'
            data = read_json(reader, metadata.get('TimelinePage'))
            if not data: continue
            timeline, plates, souls = parse_timeline(data, stats, match, mapping)
            item_events = player_item_events(data, player_by_id)
            skill_events = player_skill_events(data, player_by_id)
            for pid, player in player_by_id.items():
                player['build'].update(timelineStatus='available', itemEvents=item_events[pid], skillEvents=skill_events[pid])
            match['timeline'] = timeline
            match['detailCoverage']['timeline'] = 'available'
            for side in ('A', 'B'):
                match['objects'][f'team{side}'].update(plates=plates[side], soul=souls[side])
        except Exception as exc:
            # Optional JSON failure must not invent zero counts or prevent base scoreboard collection.
            match['detailCoverage']['error'] = type(exc).__name__
            print(f"Supplementary data unavailable: {match['sourceGameId']} ({type(exc).__name__})", flush=True)
