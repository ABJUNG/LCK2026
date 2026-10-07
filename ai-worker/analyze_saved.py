"""Analyze a bounded, explicit saved series without collecting or replacing stats."""
import argparse
import os
import sys
from analyzer import ROOT, connect_firestore
from collection_job import now, worker_lock
from review import evidence_for, fingerprint, generate_review, VERSION, DEFAULT_MODEL


class RemoteReviewError(RuntimeError):
    def __init__(self, failure):
        self.error_type = failure.get('type', 'RuntimeError')
        self.code = failure.get('code')
        super().__init__(self.error_type)


def _review_child(doc, model, connection):
    try:
        from google import genai
        client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'), http_options={
            'timeout': 30000, 'retry_options': {'attempts': 1}})
        connection.send(('ok', generate_review(doc, client, model)))
    except BaseException as exc:
        code = getattr(exc, 'code', None) or getattr(exc, 'status_code', None)
        connection.send(('error', {'type': type(exc).__name__, 'code': code if isinstance(code, int) else None}))
    finally:
        connection.close()


def bounded_review(doc, model, deadline=120):
    """A separate process guarantees a wall-clock bound even if the SDK stalls."""
    import multiprocessing
    context = multiprocessing.get_context('spawn')
    receiving, sending = context.Pipe(duplex=False)
    process = context.Process(target=_review_child, args=(doc, model, sending))
    try:
        process.start()
        sending.close()
        if not receiving.poll(deadline):
            raise TimeoutError('분석 응답 제한 시간 초과')
        state, result = receiving.recv()
        if state != 'ok': raise RemoteReviewError(result)
        return result
    finally:
        receiving.close()
        sending.close()
        if process.pid:
            process.join(timeout=1)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)


def store_review(db, ref, expected, review):
    from google.cloud import firestore
    @firestore.transactional
    def update(transaction):
        snapshot = ref.get(transaction=transaction)
        current = snapshot.to_dict()
        if not current or fingerprint(evidence_for(current)) != expected:
            raise ValueError('분석 중 경기 데이터가 변경되었습니다.')
        transaction.update(ref, {'aiReview': review})
    update(db.transaction())


def process_set(doc, generate, persist, force=False):
    expected = fingerprint(evidence_for(doc))
    old = doc.get('aiReview') or {}
    if not force and old.get('status') == 'generated' and old.get('formatVersion') == VERSION and old.get('evidenceFingerprint') == expected:
        return 'skipped'
    base = dict(formatVersion=VERSION, evidenceFingerprint=expected, requestedAt=now(), status='pending')
    persist(base)
    persist(dict(base, status='running'))
    try:
        result = generate(doc)
    except KeyboardInterrupt:
        persist(dict(base, status='pending', interruptedAt=now()))
        raise
    except Exception as exc:
        failure = dict(base, status='failed', errorType=getattr(exc, 'error_type', type(exc).__name__))
        code = getattr(exc, 'code', None) or getattr(exc, 'status_code', None)
        if isinstance(code, int): failure['errorCode'] = code
        persist(failure)
        return 'failed'
    result['generatedAt'] = now()
    persist(result)
    return 'generated'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--series-id', required=True)
    parser.add_argument('--model', help='미지정 시 GEMINI_MODEL, 없으면 gemini-3.1-flash-lite')
    parser.add_argument('--limit', type=int, default=4, help='호출할 세트 수 상한 (1~5)')
    parser.add_argument('--save', action='store_true', help='AI 호출 및 상태 저장; 기본은 대상 미리보기')
    parser.add_argument('--force', action='store_true', help='동일 근거로 생성된 분석도 다시 호출')
    args = parser.parse_args()
    if not 1 <= args.limit <= 5: parser.error('limit은 1~5입니다.')
    from dotenv import load_dotenv
    load_dotenv(ROOT / '.env')
    from google.cloud.firestore_v1.base_query import FieldFilter
    with worker_lock(ROOT / '.collection-runs' / 'worker.lock'):
        db = connect_firestore()
        snapshots = list(db.collection('matches').where(filter=FieldFilter('seriesId', '==', args.series_id)).stream())
        snapshots.sort(key=lambda s: int(s.to_dict()['setNumber']))
        snapshots = snapshots[:args.limit]
        print(f'분석 대상: {len(snapshots)}세트', flush=True)
        if not args.save:
            print('미리보기: AI 호출·DB 변경 없음', flush=True)
            return 0
        if not snapshots: return 0
        if not os.getenv('GEMINI_API_KEY'): raise ValueError('GEMINI_API_KEY가 필요합니다.')
        model = args.model or os.getenv('GEMINI_MODEL') or DEFAULT_MODEL
        counts = {'generated': 0, 'skipped': 0, 'failed': 0}
        for snapshot in snapshots:
            doc = snapshot.to_dict()
            expected = fingerprint(evidence_for(doc))
            try:
                state = process_set(doc, lambda d: bounded_review(d, model),
                                    lambda r: store_review(db, snapshot.reference, expected, r), args.force)
            except Exception:
                state = 'failed'
            counts[state] += 1
            print(f"SET{doc['setNumber']}: {state}", flush=True)
        print(counts, flush=True)
        return 1 if counts['failed'] else 0


if __name__ == '__main__':
    try: sys.exit(main())
    except KeyboardInterrupt: sys.exit(130)
    except Exception as exc:
        print(f'분석 작업 실패: {type(exc).__name__}', file=sys.stderr)
        sys.exit(1)
