"""Collect careers and explicitly linked tournament results for the roster snapshot."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from leaguepedia import quote, text
from rosters import link
ROOT = Path(__file__).resolve().parents[1]

def normalize(page, careers, results, fetched_at):
    history = {}
    for row in careers:
        if text(row.get('sourcePage')) != page: continue
        team, start, end = (text(row.get(k)) for k in ('Team', 'DateJoin', 'DateLeave'))
        if not team: raise ValueError('Career team missing')
        key = (team, start, end)
        history[key] = dict(team=team, joinedAt=start or None, leftAt=end or None,
            current=text(row.get('IsCurrent')) == '1', joinedPrecision=text(row.get('DateJoin__precision')),
            leftPrecision=text(row.get('DateLeave__precision')), sourceUrl=link(page))
    records = {}
    for row in results:
        if text(row.get('sourcePage')) != page: continue
        unique, event = text(row.get('UniqueLine')), text(row.get('OverviewPage'))
        if not unique or not event: raise ValueError('Result identity missing')
        record = dict(id=unique, tournament=text(row.get('Tournament')) or event, team=text(row.get('Team')),
            date=text(row.get('Date')), place=text(row.get('Place')), phase=text(row.get('Phase')), sourceUrl=link(event))
        if unique in records and records[unique] != record: raise ValueError('Conflicting tournament result')
        records[unique] = record
    return dict(schemaVersion=1, id=page, fetchedAt=fetched_at, sourceUrl=link(page),
        careerStatus='fetched', resultsStatus='fetched', awardsStatus='not_collected', awards=[],
        careers=sorted(history.values(), key=lambda x: x['joinedAt'] or '', reverse=True),
        results=sorted(records.values(), key=lambda x: (x['date'], x['id']), reverse=True))

def collect(reader, members):
    pages = list(dict.fromkeys(m['id'] for m in members))
    careers, results = [], []
    for offset in range(0, len(pages), 10):
        subset = pages[offset:offset+10]
        predicate = 'P._pageName IN (' + ','.join(quote(p) for p in subset) + ')'
        careers.extend(reader.pages(tables='TenuresUnbroken=T,PlayerRedirects=P', join_on='T.Player=P.AllName',
            fields='P._pageName=sourcePage,T.Team,T.DateJoin,T.DateLeave,T.IsCurrent', where=predicate,
            order_by='P._pageName ASC,T.DateJoin DESC,T._ID ASC'))
        results.extend(reader.pages(tables='TournamentPlayers=TP,TournamentResults=R,PlayerRedirects=P,Tournaments=T',
            join_on='TP.PageAndTeam=R.PageAndTeam,TP.Player=P.AllName,R.OverviewPage=T.OverviewPage',
            fields='P._pageName=sourcePage,T.Name=Tournament,R.OverviewPage,R.Team,R.Date,R.Place,R.UniqueLine,R.Phase',
            where=predicate + ' AND R.Showmatch=0', order_by='P._pageName ASC,R.Date DESC,R.UniqueLine ASC'))
        print(f'Profiles queried: {min(offset+10,len(pages))}/{len(pages)}', flush=True)
    now = datetime.now(timezone.utc).isoformat()
    return {page: normalize(page, careers, results, now) for page in pages}

def atomic(path, data):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args=parser.parse_args()
    roster_path=ROOT/'frontend/public/team-rosters.json'
    roster=json.loads(roster_path.read_text(encoding='utf-8'))
    members=[m for t in roster['teams'] for m in t['members']]
    from analyzer import connect_source
    data=collect(connect_source(),members)
    if args.write:
        folder=ROOT/'frontend/public/profiles'
        folder.mkdir(exist_ok=True)
        for member in members:
            key=hashlib.sha256(member['id'].encode()).hexdigest()[:24]
            atomic(folder/f'{key}.json', data[member['id']])
            member['profileKey']=key
        atomic(roster_path, roster)
    print(json.dumps(dict(saved=args.write, profiles=len(data), careers=sum(len(d['careers']) for d in data.values()), results=sum(len(d['results']) for d in data.values()))))
if __name__=='__main__': main()
