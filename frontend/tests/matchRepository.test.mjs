import test from 'node:test';
import assert from 'node:assert/strict';
import { query, collection, orderBy, where, limit, queryEqual } from 'firebase/firestore';
import { db } from '../src/firebase.js';
import { createMatchRepository } from '../src/utils/matchRepository.js';

test('목록은 상세 조회 없이 요약 10건만 요청하며 날짜 조건은 서버에 전달한다', async () => {
  const repo = createMatchRepository(async actual => {
    const expected = query(collection(db, 'matchSeries'), where('sortKey', '>=', '2026-08-16T00:00'), where('sortKey', '<=', '2026-08-16T23:59'), orderBy('sortKey', 'desc'), limit(10));
    assert.ok(queryEqual(actual, expected));
    return { docs: [], size: 0 };
  }, () => { throw Error('목록에서 상세 조회 금지'); });
  const page = await repo.fetchSeriesPage('2026-08-16');
  assert.deepEqual(page.items, []);
  assert.equal(page.hasMore, false);
});
test('요약에서 지정한 세트만 조회하고 진영이 바뀌어도 팀을 정렬한다', async () => {
  const ids = [];
  const repo = createMatchRepository(() => { throw Error('전체 목록 조회 금지'); }, async ref => {
    ids.push(ref.id);
    const flip = ref.id === 's2';
    return { id: ref.id, exists: () => true, data: () => ({ seriesId: 'series', tournament: 'LCK', setNumber: flip ? 2 : 1, teamA: flip ? 'B' : 'A', teamB: flip ? 'A' : 'B', dateKST: '2026-08-16', timeKST: '17:00', score: {teamA: 0, teamB: 2} }) };
  });
  const result = await repo.fetchSeriesDetails({setIds:['s1','s2'],setCount:2,seriesId:'series',tournament:'LCK'});
  assert.deepEqual(ids,['s1','s2']);
  assert.equal(result.sets[1].teamA,'A');
  assert.equal(result.sets[1].score.teamA,2);
});
test('일부 세트 누락과 다른 시리즈 문서를 정상 경기로 표시하지 않는다', async () => {
  const summary = {setIds:['s1'],setCount:1,seriesId:'series',tournament:'LCK'};
  const missing = createMatchRepository(null, async () => ({exists:()=>false}));
  await assert.rejects(missing.fetchSeriesDetails(summary));
  const wrong = createMatchRepository(null, async () => ({id:'s1',exists:()=>true,data:()=>({seriesId:'other',tournament:'LCK'})}));
  await assert.rejects(wrong.fetchSeriesDetails(summary));
});
test('중복 세트 주소는 읽기 전에 거절한다', async () => {
  const repo = createMatchRepository(null, () => { throw Error('읽으면 안 됨'); });
  await assert.rejects(repo.fetchSeriesDetails({setIds:['s1','s1'],setCount:2}), /요약/);
});

test('대회 필터는 정확한 시즌·대회 접두어로 제한하고 다른 대회를 섞지 않는다', async () => {
  const repo = createMatchRepository(async actual => {
    const expected = query(collection(db, 'matchSeries'), where('catalogSortKey', '>=', '2026:WORLDS|'), where('catalogSortKey', '<', '2026:WORLDS|\uf8ff'), orderBy('catalogSortKey', 'desc'), limit(10));
    assert.ok(queryEqual(actual, expected));
    return { docs: [], size: 0 };
  });
  await repo.fetchSeriesPage('', null, 'WORLDS');
});

test('화면의 대회 목록은 수집기와 같은 등록 정보를 사용한다', async () => {
  const { readFile } = await import('node:fs/promises');
  const source = JSON.parse(await readFile(new URL('../../config/competitions.json', import.meta.url), 'utf8'));
  const display = JSON.parse(await readFile(new URL('../public/competitions.json', import.meta.url), 'utf8'));
  assert.deepEqual(display, source);
});
