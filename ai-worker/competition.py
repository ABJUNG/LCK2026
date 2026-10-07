"""Exact source names: exclude academy leagues and unrelated World Cup events."""
import json
from pathlib import Path
CATALOG = json.loads((Path(__file__).resolve().parent.parent / 'config/competitions.json').read_text(encoding='utf-8'))

def competition_info(tournament, series_id=''):
    for entry in CATALOG:
        for source in entry['sources']:
            if source['name'] == tournament:
                stage = source['stage']
                if stage == 'PLAYOFFS' and '_Finals_' in series_id: stage = 'FINALS'
                return dict(league=entry['league'], season=entry['season'], competitionId=entry['id'], competitionLabel=entry['label'], stage=stage)
    return {}

def source_names(competition, year):
    entries = [e for e in CATALOG if e['season'] == year and e['id'] == competition]
    if len(entries) != 1: raise ValueError('지원하지 않는 대회 또는 시즌입니다.')
    return [s['name'] for s in entries[0]['sources']]
