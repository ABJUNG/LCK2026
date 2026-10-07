"""Verify existing matches against Leaguepedia JSON; --save adds only teamSides."""
import argparse
import json
from pathlib import Path
from analyzer import connect_firestore, connect_source
from leaguepedia import quote
from postgame import read_json, verified_sides


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--save', action='store_true')
    args = parser.parse_args()
    db, reader = connect_firestore(), connect_source()
    documents = list(db.collection('matches').stream())
    pending = [doc for doc in documents if doc.to_dict().get('sourceGameId') and not doc.to_dict().get('teamSides')]
    if not pending:
        print('No missing side metadata.', flush=True)
        return
    if len(pending) > 200:
        raise ValueError('At most 200 sets per backfill; split the scope before saving.')
    ids = [doc.to_dict()['sourceGameId'] for doc in pending]
    metadata = reader.pages(tables='PostgameJsonMetadata', fields='GameId,StatsPage,RiotVersion',
                            where='GameId IN (' + ','.join(quote(gid) for gid in ids) + ')', order_by='GameId ASC')
    results = []
    for index, snapshot in enumerate(pending, 1):
        doc = snapshot.to_dict()
        rows = [row for row in metadata if row['GameId'] == doc['sourceGameId'] and str(row.get('RiotVersion')) == '5']
        if len(rows) != 1:
            raise ValueError(f"Missing or duplicated metadata: {doc['sourceGameId']}")
        stats = read_json(reader, rows[0].get('StatsPage'))
        if not stats or stats.get('endOfGameResult') != 'GameComplete':
            raise ValueError('Missing completed JSON')
        teams = {'team_A_players': doc['players']['teamA'], 'team_B_players': doc['players']['teamB']}
        sides = verified_sides(stats, teams)
        # Validate each champion's KDA against the saved set before trusting its side.
        from postgame import champion_key
        for participant in stats['participants']:
            team = next(key for key in ('teamA', 'teamB') if sides[key] == ('BLUE' if participant['teamId'] == 100 else 'RED'))
            player = next(p for p in doc['players'][team] if champion_key(p['champion']) == champion_key(participant['championName']))
            if any(player[key] != participant.get(key) for key in ('kills', 'deaths', 'assists')):
                raise ValueError('Saved scoreboard and JSON disagree')
        results.append({'documentId': snapshot.id, 'sourceGameId': doc['sourceGameId'], 'teamA': doc['teamA'], 'teamB': doc['teamB'], 'setNumber': doc['setNumber'], 'teamSides': sides})
        print(f"Verified {index}/{len(pending)}: {doc['teamA']} / {doc['teamB']} SET{doc['setNumber']} {sides}", flush=True)
    report = Path(__file__).resolve().parents[1] / 'docs' / 'team-sides-verification-2026-10-07.json'
    report.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    if args.save:
        batch = db.batch()
        for record in results:
            batch.update(db.collection('matches').document(record['documentId']), {'teamSides': record['teamSides']})
        batch.commit()
        print(f'Saved verified side metadata: {len(results)} sets', flush=True)
    else:
        print(f'Preview only: {len(results)} verified sets', flush=True)


if __name__ == '__main__':
    main()
