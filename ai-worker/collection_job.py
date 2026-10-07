"""Durable local checkpoints. No credentials or raw API responses in the journal."""
import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone


def now():
    return datetime.now(timezone.utc).isoformat()


def checkpoint(path, job):
    job['updatedAt'] = now()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    with temporary.open('w', encoding='utf-8') as handle:
        handle.write(json.dumps(job, ensure_ascii=False, indent=2))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


@contextmanager
def worker_lock(path):
    """OS releases the lock even after a crash; the file itself may remain."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b'0')
            handle.flush()
        handle.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise ValueError('다른 수집 작업이 실행 중입니다.') from None
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == 'nt':
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def run_job(path, job, process):
    job['status'] = 'running'
    checkpoint(path, job)
    try:
        for entry in job['series']:
            if entry['status'] in ('saved', 'skipped'):
                continue
            entry.update(status='running', attempts=entry.get('attempts', 0) + 1)
            checkpoint(path, job)
            try:
                result = process(entry)
                if result.get('status') not in ('saved', 'skipped'):
                    raise ValueError('Invalid processing result')
                entry.update(result)
                entry.pop('errorType', None)
            except Exception as exc:
                # Exception text can contain HTTP credentials; store the type only.
                entry.update(status='failed', errorType=type(exc).__name__)
            checkpoint(path, job)
        job['status'] = 'partial_failure' if any(e['status'] == 'failed' for e in job['series']) else 'completed'
        checkpoint(path, job)
    except BaseException:
        job['status'] = 'interrupted'
        checkpoint(path, job)
        raise
    return 1 if job['status'] == 'partial_failure' else 0
