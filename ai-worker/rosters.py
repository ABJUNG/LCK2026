"""Public Leaguepedia roster snapshot. No match documents or Firestore writes."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote as urlquote
from leaguepedia import quote, text

TEAMS = {
    'T1': ['T1'], 'Gen.G': ['Gen.G'], 'Hanwha Life Esports': ['Hanwha Life Esports'],
    'KT Rolster': ['KT Rolster'], 'Dplus KIA': ['Dplus KIA'], 'BNK FEARX': ['BNK FEARX', 'FearX'],
    'DN SOOPers': ['DN SOOPers', 'Kwangdong Freecs'], 'Nongshim RedForce': ['Nongshim RedForce'],
    'KIWOOM DRX': ['KIWOOM DRX', 'DRX'], 'HANJIN BRION': ['HANJIN BRION', 'OKSavingsBank BRION'],
}
POSITIONS = ['Top', 'Jungle', 'Mid', 'Bot', 'Support']
def link(page):
    return 'https://lol.fandom.com/wiki/' + urlquote(page.replace(' ', '_'), safe='')
def assemble(profiles, tenures, fetched_at):
    aliases = {alias.casefold(): name for name, names in TEAMS.items() for alias in names}
    latest = {}
    for row in tenures:
        key = (text(row.get('sourcePage')), aliases.get(text(row.get('Team')).casefold()))
        if not all(key) or text(row.get('IsCurrent')) != '1':
            continue
        date = text(row.get('roleDate'))
        if not date:
            continue
        old = latest.get(key)
        if old is None or date > text(old.get('roleDate')):
            latest[key] = row.copy()
        elif date == text(old.get('roleDate')) and any(text(row.get(k)) != text(old.get(k)) for k in ('Roles', 'Status', 'RoleModifier')):
            old['ambiguous'] = True
    teams = {name: {'name': name, 'sourceUrl': link(name), 'members': []} for name in TEAMS}
    seen = set()
    for p in profiles:
        team = aliases.get(text(p.get('Team')).casefold())
        page = text(p.get('sourcePage'))
        if not team or not page:
            raise ValueError('Unexpected team or missing profile page')
        if page in seen:
            raise ValueError('Duplicate profile page')
        seen.add(page)
        tenure = latest.get((page, team), {})
        roles = [v.strip() for v in text(tenure.get('Roles')).split(';') if v.strip()]
        if tenure.get('ambiguous') or not roles:
            roles = [text(p.get('Role'))] if text(p.get('Role')) else []
        group = 'players' if any(v in POSITIONS for v in roles) else 'staff' if any('coach' in v.lower() or v.lower() in ('analyst', 'manager') for v in roles) else 'other'
        # Only the public competitive roster and coaching staff are in scope.
        if group == 'other':
            continue
        verified = bool(tenure) and not tenure.get('ambiguous')
        teams[team]['members'].append({'id': page, 'profileKey': hashlib.sha256(page.encode()).hexdigest()[:24], 'nickname': text(p.get('ID')) or page,
            'name': text(p.get('NativeName')) or text(p.get('Name')) or None,
            'country': text(p.get('Country')) or None, 'roles': roles, 'group': group,
            'status': text(tenure.get('Status')) if verified else None,
            'roleModifier': text(tenure.get('RoleModifier')) if verified else None,
            'joinedAt': text(tenure.get('DateJoin')) if verified else None,
            'joinedPrecision': text(tenure.get('DateJoin__precision')) if verified else None,
            'roleRecordAt': text(tenure.get('roleDate')) if verified else None,
            'roleVerified': verified, 'sourceUrl': link(page)})
    for team in teams.values():
        team['members'].sort(key=lambda m: (0 if m['group'] == 'players' else 1,
            min((POSITIONS.index(v) for v in m['roles'] if v in POSITIONS), default=9), m['nickname'].casefold()))
        if not any(m['group'] == 'players' for m in team['members']):
            raise ValueError(f"No players for {team['name']}; keep the previous snapshot")
    return {'schemaVersion': 1, 'fetchedAt': fetched_at, 'scope': 'current-source-roster',
        'source': 'Leaguepedia', 'license': 'CC BY-SA 3.0', 'teams': list(teams.values())}

def collect(reader):
    names = ','.join(quote(v) for values in TEAMS.values() for v in values)
    profiles = reader.pages(tables='Players', fields='_pageName=sourcePage,ID,Name,NativeName,Country,Team,Role',
        where=f'Team IN ({names})', order_by='_pageName ASC')
    tenures = reader.pages(tables='TenuresUnbroken=T,TenuresUnbroken__RosterChangeIds=I,RosterChanges=R,NewsItems=N,PlayerRedirects=P',
        join_on='T._ID=I._rowID,I._value=R.RosterChangeId,R.NewsId=N.NewsId,T.Player=P.AllName',
        fields='P._pageName=sourcePage,T.Team,T.DateJoin,T.IsCurrent,R.RoleModifier,R.Roles__full=Roles,R.Status,N.Date_Sort=roleDate',
        where=f'T.Team IN ({names}) AND T.IsCurrent=1', order_by='N.Date_Sort ASC,P._pageName ASC,R.RosterChangeId ASC')
    return assemble(profiles, tenures, datetime.now(timezone.utc).isoformat())

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Save validated public snapshot for the frontend')
    args = parser.parse_args()
    from analyzer import connect_source
    data = collect(connect_source())
    if args.write:
        target = Path(__file__).resolve().parents[1] / 'frontend/public/team-rosters.json'
        temp = target.with_suffix('.tmp')
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        temp.replace(target)
    print(json.dumps({'saved': args.write, 'fetchedAt': data['fetchedAt'],
        'teams': [{'name': t['name'], 'players': sum(m['group'] == 'players' for m in t['members']),
                   'staff': sum(m['group'] == 'staff' for m in t['members'])} for t in data['teams']]}, ensure_ascii=False))
if __name__ == '__main__':
    main()
