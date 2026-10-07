"""Public series summaries; existing match documents are preserved."""
import hashlib
import json
from collections import defaultdict

def build_summaries(documents):
    groups, seen = defaultdict(list), set()
    for doc in documents:
        if not doc.get('seriesId') or not doc.get('sourceGameId'): continue
        if doc['sourceGameId'] in seen: raise ValueError('Duplicate sourceGameId')
        seen.add(doc['sourceGameId'])
        groups[(doc['tournament'], doc['seriesId'])].append(doc)
    summaries = {}
    for (tournament, sid), sets in groups.items():
        sets.sort(key=lambda d: int(d['setNumber']))
        if len({int(d['setNumber']) for d in sets}) != len(sets): raise ValueError('Duplicate set number')
        first, last = sets[0], sets[-1]
        teams = {first['teamA'], first['teamB']}
        if len(teams) != 2 or any({d['teamA'], d['teamB']} != teams for d in sets): raise ValueError('Team mismatch')
        score = last.get('score', {})
        if last['teamA'] != first['teamA']: score = {'teamA': score.get('teamB'), 'teamB': score.get('teamA')}
        key = hashlib.sha256(json.dumps([tournament, sid], ensure_ascii=False).encode()).hexdigest()
        summaries[key] = dict(schemaVersion=1, seriesId=sid, tournament=tournament,
            teamA=first['teamA'], teamB=first['teamB'], dateKST=first['dateKST'], timeKST=first['timeKST'],
            sortKey=first['dateKST']+'T'+first['timeKST'], score=score,
            setIds=[d['id'] for d in sets], setCount=len(sets))
        from competition import competition_info
        info = competition_info(tournament, sid)
        summaries[key].update(info)
        if info:
            summaries[key]['catalogSortKey'] = f"{info['season']}:{info['competitionId']}|{summaries[key]['sortKey']}"
    return summaries

def migrate(save=False):
    from analyzer import connect_firestore
    db = connect_firestore()
    documents = [dict(s.to_dict(), id=s.id) for s in db.collection('matches').stream()]
    summaries = build_summaries(documents)
    print(f'Summaries: {len(summaries)}, sets: {sum(s["setCount"] for s in summaries.values())}')
    print('JSON bytes: details=', len(json.dumps(documents, default=str).encode()), 'summaries=', len(json.dumps(summaries).encode()))
    if save:
        for key, summary in summaries.items(): db.collection('matchSeries').document(key).set(summary)
        print('Summary migration saved; originals preserved.')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--save', action='store_true')
    migrate(parser.parse_args().save)
