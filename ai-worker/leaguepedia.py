"""Leaguepedia 수집: KST 날짜, 페이지 처리, 전체 시리즈, 데이터 검증."""
import html
import re
import time
from datetime import datetime, timedelta, timezone
from match_document import extract_source_identity

KST = timezone(timedelta(hours=9))
ROLES = ('Top', 'Jungle', 'Mid', 'Bot', 'Support')
TEAMS = frozenset(('Gen.G', 'T1', 'Dplus KIA', 'FearX', 'BNK FEARX', 'OKSavingsBank BRION',
    'HANJIN BRION', 'Hanwha Life Esports', 'KT Rolster', 'Kwangdong Freecs', 'DN SOOPers',
    'Nongshim RedForce', 'DRX', 'KIWOOM DRX', 'Kiwoom DRX'))
GAME_FIELDS = 'GameId,MatchId,Tournament,DateTime_UTC=utcDateTime,Team1,Team2,Team1Score,Team2Score,Winner,N_GameInMatch=setNumber,Patch,Team1Dragons,Team2Dragons,Team1Barons,Team2Barons,Team1Towers,Team2Towers'
OBJECT_FIELDS = {'Dragons': 'dragons', 'Clouds': 'clouds', 'Infernals': 'infernals',
    'Mountains': 'mountains', 'Oceans': 'oceans', 'Hextechs': 'hextechs', 'Chemtechs': 'chemtechs',
    'Elders': 'elders', 'Barons': 'barons', 'Towers': 'towers', 'RiftHeralds': 'heralds',
    'VoidGrubs': 'grubs', 'Atakhans': 'atakhans', 'Inhibitors': 'inhibitors', 'Kills': 'kills'}
GAME_FIELDS += ',Gamelength,RiotPlatformGameId,' + ','.join(f'Team{t}{f}' for t in (1, 2)
    for f in (*OBJECT_FIELDS, 'Gold') if f not in ('Dragons', 'Barons', 'Towers'))
PLAYER_FIELDS = 'GameId,Link,Team,Champion,Role,Kills,Deaths,Assists,Gold,DamageToChampions,CS,VisionScore,Items,SummonerSpells,KeystoneRune,PrimaryTree,SecondaryTree,Runes'


class SourceError(RuntimeError):
    pass


def text(value):
    return html.unescape(str(value or '')).strip()


def quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def kst_bounds(date):
    start = datetime.strptime(date, '%Y-%m-%d').replace(tzinfo=KST)
    return tuple(t.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S') for t in (start, start + timedelta(days=1)))


def convert_utc_to_kst(value):
    dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc).astimezone(KST)
    return dt.strftime('%Y-%m-%d'), dt.strftime('%H:%M')


def extract_week_info(match_id, tournament):
    combined = f'{match_id} {tournament}'
    found = re.search(r'Week\s*(\d+)|(?:^|[_ /])W(\d+)(?:$|[_ /])', combined, re.I)
    if found:
        week = next(value for value in found.groups() if value)
        return f'{week}주차', f'Week {week}'
    if 'Playoffs' in combined:
        return '플레이오프', 'Playoffs'
    if 'Finals' in combined:
        return '결승전', 'Finals'
    return '정규시즌', 'Regular Season'


def number(value, required=False):
    if value is None or value == '':
        if required:
            raise ValueError('필수 숫자 누락')
        return None
    parsed = int(value)
    if parsed < 0:
        raise ValueError('음수 스탯')
    return parsed


class CargoReader:
    def __init__(self, client, sleep=time.sleep):
        self.client = client
        self.sleep = sleep

    def query(self, **kwargs):
        for attempt in range(3):
            try:
                self.sleep(1)
                return self.client.query(**kwargs)
            except Exception as exc:
                code = str(getattr(exc, 'code', '')).lower()
                status = getattr(getattr(exc, 'response', None), 'status_code', None)
                if code not in ('ratelimited', 'maxlag') and status != 429:
                    raise SourceError(f'Leaguepedia 조회 실패 ({type(exc).__name__}, {code or status or "unknown"})') from None
                if attempt == 2:
                    raise SourceError('Leaguepedia 호출 제한: 3회 시도 후 중단. DB는 변경하지 않았습니다.') from None
                delay = 30 * (attempt + 1)
                print(f'Leaguepedia 호출 제한: {delay}초 후 재시도 ({attempt + 2}/3)', flush=True)
                self.sleep(delay)

    def pages(self, **kwargs):
        # 100행씩 최대 20페이지. 초과 시 잘린 데이터를 정상으로 취급하지 않습니다.
        result = []
        for offset in range(0, 2000, 100):
            rows = self.query(**kwargs, limit=100, offset=offset)
            result.extend(rows)
            if len(rows) < 100:
                return result
        raise SourceError('조회 상한 초과: 날짜 범위를 좁혀 주세요.')


def is_lck(row):
    allowed = {team.casefold() for team in TEAMS}
    return text(row.get('Team1')).casefold() in allowed and text(row.get('Team2')).casefold() in allowed


def fetch_matches(reader, date=None, limit=3, year=2026, competition='LCK', series_id=None):
    from competition import source_names, competition_info
    names = source_names(competition, year)
    tournament_predicate = 'Tournament IN (' + ','.join(quote(name) for name in names) + ')'
    where = tournament_predicate + ' AND Winner IN (1,2)'
    if series_id:
        where += f' AND MatchId={quote(series_id)}'
    def eligible(row):
        info = competition_info(text(row.get('Tournament')))
        return text(row.get('Tournament')) in names and (info.get('league') != 'LCK' or is_lck(row))
    if date:
        start, end = kst_bounds(date)
        where += f' AND DateTime_UTC >= {quote(start)} AND DateTime_UTC < {quote(end)}'
    series = []
    for offset in range(0, 2000, 100):
        rows = reader.query(tables='ScoreboardGames', fields=GAME_FIELDS, where=where,
                            order_by='DateTime_UTC DESC,GameId ASC', limit=100, offset=offset)
        for row in rows:
            sid = text(row.get('MatchId'))
            if eligible(row):
                if not sid:
                    raise SourceError('원본 MatchId 누락: 시리즈를 식별할 수 없습니다.')
                if sid not in series:
                    series.append(sid)
            if not date and len(series) >= limit:
                break
        if len(rows) < 100 or (not date and len(series) >= limit):
            break
    else:
        raise SourceError('경기 탐색 상한 초과: 날짜를 지정해 주세요.')
    matches = []
    for index, sid in enumerate(series, 1):
        print(f'시리즈 수집 {index}/{len(series)}: {sid}', flush=True)
        # 날짜/limit 때문에 시리즈의 마지막 세트만 가져오는 것을 방지합니다.
        games = reader.pages(tables='ScoreboardGames', fields=GAME_FIELDS,
                             where=f'MatchId={quote(sid)} AND {tournament_predicate} AND Winner IN (1,2)', order_by='N_GameInMatch ASC,GameId ASC')
        if not games or any(not eligible(row) for row in games):
            raise SourceError('시리즈 팀 정보 불일치')
        ids = [text(row.get('GameId')) for row in games]
        if not all(ids) or len(ids) != len(set(ids)):
            raise SourceError('GameId 누락 또는 중복')
        predicate = 'GameId IN (' + ','.join(quote(gid) for gid in ids) + ')'
        bans = reader.pages(tables='PicksAndBansS7', fields='GameId,' + ','.join(f'Team{team}Ban{i}' for team in (1, 2) for i in range(1, 6)), where=predicate, order_by='GameId ASC')
        players = reader.pages(tables='ScoreboardPlayers', fields=PLAYER_FIELDS, where=predicate, order_by='GameId ASC,Team ASC,Role ASC')
        assembled = assemble_matches(games, bans, players)
        from postgame import enrich_matches
        enrich_matches(reader, assembled, games)
        matches.extend(assembled)
    return matches


def assemble_matches(games, bans, players):
    result = []
    for row in games:
        identity = extract_source_identity({key: text(row.get(key)) for key in ('GameId', 'MatchId')})
        if len(identity) != 2:
            raise ValueError('원본 ID 누락')
        gid = identity['sourceGameId']
        date, clock = convert_utc_to_kst(text(row.get('utcDateTime')))
        week, week_en = extract_week_info(identity['seriesId'], text(row.get('Tournament')))
        winner = number(row.get('Winner'), required=True)
        if winner not in (1, 2):
            raise ValueError(f'{gid}: 완료된 세트의 승자 정보가 없습니다.')
        ban_rows = [b for b in bans if text(b.get('GameId')) == gid]
        if len(ban_rows) != 1:
            raise ValueError(f'{gid}: 밴 데이터 누락 또는 중복')
        match = {**identity, 'tournament': text(row.get('Tournament')), 'week_kr': week, 'week_en': week_en,
                 'date_kst': date, 'time_kst': clock, 'patch': text(row.get('Patch')) or None,
                 'team_A': text(row.get('Team1')), 'team_B': text(row.get('Team2')),
                 'team_A_score': number(row.get('Team1Score')), 'team_B_score': number(row.get('Team2Score')),
                 'set_number': str(number(row.get('setNumber'), required=True)),
                 'winnerTeam': text(row.get(f'Team{winner}')), 'gameLength': text(row.get('Gamelength')) or None, 'objects': {}}
        if int(match['set_number']) < 1:
            raise ValueError('세트 번호는 1 이상이어야 합니다.')
        selected = [p for p in players if text(p.get('GameId')) == gid]
        if len(selected) != 10 or any(text(p.get('Team')) not in (match['team_A'], match['team_B']) for p in selected):
            raise ValueError(f'{gid}: 선수 10명 또는 팀 대응 검증 실패')
        for team, side in ((1, 'A'), (2, 'B')):
            roster = [p for p in selected if text(p.get('Team')) == match[f'team_{side}']]
            if sorted(text(p.get('Role')) for p in roster) != sorted(ROLES):
                raise ValueError(f'{gid}: 팀별 5개 포지션 검증 실패')
            match[f'team_{side}_players'] = []
            for p in roster:
                name = re.sub(r'\s*\(.*?\)', '', text(p.get('Link'))).strip()
                if not name or not text(p.get('Champion')):
                    raise ValueError(f'{gid}: 선수명 또는 챔피언 누락')
                match[f'team_{side}_players'].append({'name': name, 'role': text(p.get('Role')), 'champion': text(p.get('Champion')),
                    **{target: number(p.get(source), required=target in ('kills', 'deaths', 'assists')) for source, target in
                       (('Kills', 'kills'), ('Deaths', 'deaths'), ('Assists', 'assists'), ('Gold', 'gold'), ('DamageToChampions', 'damage'), ('CS', 'cs'), ('VisionScore', 'vision'))},
                    'items': [text(x) for x in text(p.get('Items')).split(';') if text(x)],
                    'spells': [text(x) for x in text(p.get('SummonerSpells')).split(',') if text(x)],
                    'runes': text(p.get('Runes')) or None, 'keystone': text(p.get('KeystoneRune')) or None})
            match[f'team_{side}_bans'] = [text(ban_rows[0].get(f'Team{team}Ban{i}')) for i in range(1, 6)]
            match['objects'][f'team{side}'] = {target: number(row.get(f'Team{team}{source}')) for source, target in
                                             OBJECT_FIELDS.items()}
            gold = row.get(f'Team{team}Gold')
            match['objects'][f'team{side}']['gold'] = float(gold) if gold not in (None, '') else None
        result.append(match)
    return result
