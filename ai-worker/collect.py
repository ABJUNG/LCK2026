"""Discover every completed set in one supported competition, then collect per series."""
import argparse
import json
import sys
import uuid
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone
from collection_job import checkpoint, now, run_job, worker_lock

ROOT = Path(__file__).resolve().parent
RUNS = ROOT / '.collection-runs'


def discover(reader, competition, year, date=None):
    from competition import source_names, competition_info
    from leaguepedia import quote, kst_bounds, is_lck, text
    names = source_names(competition, year)
    where = 'Tournament IN (' + ','.join(quote(name) for name in names) + ') AND Winner IN (1,2)'
    if date:
        start, end = kst_bounds(date)
        where += f' AND DateTime_UTC >= {quote(start)} AND DateTime_UTC < {quote(end)}'
    rows = reader.pages(tables='ScoreboardGames', fields='GameId,MatchId,Tournament,Team1,Team2',
                        where=where, order_by='DateTime_UTC ASC,GameId ASC')
    series = defaultdict(list)
    seen = set()
    for row in rows:
        tournament = text(row.get('Tournament'))
        if tournament not in names or (competition_info(tournament).get('league') == 'LCK' and not is_lck(row)):
            continue
        gid, sid = text(row.get('GameId')), text(row.get('MatchId'))
        if not gid or not sid or gid in seen:
            raise ValueError('원본 경기 ID 누락 또는 중복')
        seen.add(gid)
        series[(tournament, sid)].append(gid)
    return [dict(tournament=t, seriesId=s, expectedGameIds=sorted(ids), status='pending', attempts=0)
            for (t, s), ids in series.items()]


def saved_series(db, entry):
    from google.cloud.firestore_v1.base_query import FieldFilter
    rows = [dict(s.to_dict(), id=s.id) for s in db.collection('matches').where(
        filter=FieldFilter('seriesId', '==', entry['seriesId'])).stream()]
    rows = [d for d in rows if d.get('tournament') == entry['tournament']]
    ids = [d.get('sourceGameId') for d in rows]
    if not all(ids) or len(ids) != len(set(ids)):
        raise ValueError('저장된 시리즈의 원본 ID 누락 또는 중복')
    return rows


def verified_summary(db, rows):
    from series_summary import build_summaries
    for key, expected in build_summaries(rows).items():
        actual = db.collection('matchSeries').document(key).get().to_dict() or {}
        if any(actual.get(field) != value for field, value in expected.items()):
            return False
    return bool(rows)


def processor(reader, db, scope, save, refresh=False):
    from analyzer import save_documents
    from leaguepedia import fetch_matches
    from match_document import build_match_document
    def process(entry):
        entry['phase'] = 'compare_saved'
        rows = saved_series(db, entry)
        expected = set(entry['expectedGameIds'])
        existing = {d['sourceGameId'] for d in rows}
        entry['missingGameIds'] = sorted(expected - existing)
        entry['unexpectedGameIds'] = sorted(existing - expected) if not scope.get('date') else []
        # A date discovers affected series, not all sets of cross-midnight series.
        if not refresh and not scope.get('date') and existing == expected and verified_summary(db, rows):
            print(f"이미 저장됨: {entry['seriesId']} ({len(rows)}세트)", flush=True)
            return dict(status='skipped', verifiedSets=len(rows), detailUnavailableGameIds=[d['sourceGameId'] for d in rows
                if (d.get('detailCoverage') or {}).get('stats') != 'available' or (d.get('detailCoverage') or {}).get('timeline') != 'available'])
        if not save:
            print(f"수집 필요: {entry['seriesId']} (발견 {len(expected)}, 저장 {len(existing)})", flush=True)
            return dict(status='skipped', verifiedSets=len(existing), needsCollection=True)
        entry['phase'] = 'fetch_validate'
        matches = fetch_matches(reader, competition=scope['competition'], year=scope['year'], series_id=entry['seriesId'])
        actual = {m['sourceGameId'] for m in matches}
        if len(actual) != len(matches) or not expected.issubset(actual) or not existing.issubset(actual):
            raise ValueError('탐색·수집·기존 저장 세트 불일치')
        if any(m['tournament'] != entry['tournament'] for m in matches):
            raise ValueError('시리즈 대회 불일치')
        if sorted(int(m['set_number']) for m in matches) != list(range(1, len(matches) + 1)):
            raise ValueError('세트 번호 누락 또는 중복')
        documents = [build_match_document(m) for m in matches]
        for d in documents:
            d['fetchedAt'] = now()
        entry['phase'] = 'save'
        save_documents(documents, matches)
        entry['phase'] = 'verify_saved'
        saved = saved_series(db, entry)
        if {d['sourceGameId'] for d in saved} != actual or not verified_summary(db, saved):
            raise ValueError('저장 후 원본 ID 또는 요약 대조 실패')
        missing_details = [d['sourceGameId'] for d in saved if (d.get('detailCoverage') or {}).get('stats') != 'available'
                           or (d.get('detailCoverage') or {}).get('timeline') != 'available']
        return dict(status='saved', expectedGameIds=sorted(actual), verifiedSets=len(saved),
                    missingGameIds=[], unexpectedGameIds=[], detailUnavailableGameIds=missing_details)
    return process


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--competition', default='LCK')
    parser.add_argument('--year', type=int, default=2026)
    parser.add_argument('--date', help='한국 날짜; 이 날짜에 열린 시리즈의 모든 완료 세트 수집')
    parser.add_argument('--save', action='store_true')
    parser.add_argument('--refresh', action='store_true', help='기존 세트도 다시 조회하여 원본 수정 반영')
    parser.add_argument('--resume', help='.collection-runs 안의 실행 파일명; 미완료·실패 항목 재개')
    args = parser.parse_args(argv)
    if args.resume and not args.save:
        parser.error('재개에는 --save가 필요합니다.')
    from competition import source_names
    from leaguepedia import kst_bounds
    if not args.resume:
        source_names(args.competition, args.year)
        if args.date: kst_bounds(args.date)
    from analyzer import connect_firestore, connect_source
    with worker_lock(RUNS / 'worker.lock'):
        if args.resume:
            path = (RUNS / args.resume).resolve()
            if path.parent != RUNS.resolve() or path.suffix != '.json':
                raise ValueError('실행 기록 폴더 안의 JSON 파일명을 지정하세요.')
            job = json.loads(path.read_text(encoding='utf-8'))
            if job.get('schemaVersion') != 1 or job.get('mode') != 'save':
                raise ValueError('저장 작업 기록만 재개할 수 있습니다.')
            scope = job['scope']
            source_names(scope['competition'], scope['year'])
            if scope.get('date'): kst_bounds(scope['date'])
        else:
            scope = dict(competition=args.competition, year=args.year, date=args.date, refresh=args.refresh)
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
            path = RUNS / f'{stamp}-{uuid.uuid4().hex[:8]}.json'
            job = dict(schemaVersion=1, mode='save' if args.save else 'preview', scope=scope,
                       createdAt=now(), status='discovering', series=[])
            checkpoint(path, job)
        print(f'실행 기록: {path.name}', flush=True)
        try:
            reader, db = connect_source(), connect_firestore()
            if not args.resume or job['status'] in ('discovering', 'discovery_failed'):
                job['series'] = discover(reader, scope['competition'], scope['year'], scope.get('date'))
                checkpoint(path, job)
            code = run_job(path, job, processor(reader, db, scope, args.save, scope.get('refresh', False)))
        except Exception as exc:
            job.update(status='discovery_failed' if not job['series'] else 'interrupted', errorType=type(exc).__name__)
            checkpoint(path, job)
            raise
        totals = {state: sum(e['status'] == state for e in job['series']) for state in ('saved', 'skipped', 'failed')}
        job['totals'] = dict(totals, discoveredSets=sum(len(e['expectedGameIds']) for e in job['series']),
                             verifiedSets=sum(e.get('verifiedSets', 0) for e in job['series'] if e['status'] in ('saved', 'skipped')),
                             detailUnavailableSets=sum(len(e.get('detailUnavailableGameIds', [])) for e in job['series']))
        checkpoint(path, job)
        print(f"완료: {job['status']} · {totals} · {len(job['series'])}시리즈", flush=True)
        if not args.save: print('미리보기: Firestore는 변경하지 않았습니다.', flush=True)
        return code


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print('중단됨: 실행 기록 파일명으로 --resume 하세요.', file=sys.stderr)
        sys.exit(130)
    except Exception as exc:
        print(f'수집 실패: {type(exc).__name__}. 실행 기록과 인증·네트워크 설정을 확인하세요.', file=sys.stderr)
        sys.exit(1)
