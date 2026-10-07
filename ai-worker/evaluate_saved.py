"""Read-only quality screening: no Gemini calls, no Firestore writes."""
import argparse
import json
from analyzer import ROOT, connect_firestore
from review_quality import evaluate_document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--series-id', required=True)
    args = parser.parse_args()
    from dotenv import load_dotenv
    from google.cloud.firestore_v1.base_query import FieldFilter
    load_dotenv(ROOT / '.env')
    rows = list(connect_firestore().collection('matches').where(filter=FieldFilter('seriesId', '==', args.series_id)).stream())
    rows.sort(key=lambda row: int(row.to_dict()['setNumber']))
    if not rows:
        print('평가할 경기 없음')
        return 1
    results = [evaluate_document(row.to_dict()) for row in rows]
    print(json.dumps({'seriesId': args.series_id, 'results': results, 'semanticVerification': 'not_performed'}, ensure_ascii=True, indent=2))
    return int(any(r['status'] != 'screened' for r in results))


if __name__ == '__main__':
    import sys
    try: sys.exit(main())
    except Exception as exc:
        print('평가 실패: ' + type(exc).__name__, file=sys.stderr)
        sys.exit(1)
