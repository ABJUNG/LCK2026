import test from 'node:test';
import assert from 'node:assert/strict';
import { groupMatches } from '../src/utils/groupMatches.js';
import { demoMatches } from '../src/dev/demoMatches.js';

test('팀 진영이 바뀌어도 한 경기로 묶고 선수·밴·스코어를 같은 팀에 대응한다', () => {
  const input = structuredClone(demoMatches);
  input[0].score = { teamA: 1, teamB: 2 };
  const before = structuredClone(input);
  const [series] = groupMatches(input);
  assert.equal(groupMatches(input).length, 1);
  assert.equal(series.teamA, 'Gen.G');
  assert.equal(series.timeKST, '17:00');
  assert.deepEqual(series.sets.map(set => set.setNumber), ['1', '2']);
  assert.equal(series.sets[1].players.teamA[0].name, 'GEN 예제 2');
  assert.deepEqual(series.sets[1].bans.teamA, ['Lux']);
  assert.deepEqual(series.sets[1].score, { teamA: 2, teamB: 1 });
  assert.deepEqual(input, before);
});
test('기존 데이터도 팀 순서와 조회 순서에 영향받지 않는다', () => {
  const input = demoMatches.map(({ seriesId, ...rest }) => { assert.ok(seriesId); return rest; });
  assert.equal(groupMatches(input).length, 1);
  assert.deepEqual(groupMatches(input), groupMatches([...input].reverse()));
});
test('같은 날짜·대진이어도 대회 또는 시리즈 ID가 다르면 분리한다', () => {
  const match = demoMatches[1];
  assert.equal(groupMatches([match, { ...match, seriesId: 'another' }]).length, 2);
  assert.equal(groupMatches([match, { ...match, tournament: '다른 대회' }]).length, 2);
});
test('시리즈 ID가 있으면 자정을 넘어도 같은 경기로 묶는다', () => {
  assert.equal(groupMatches([demoMatches[1], { ...demoMatches[0], dateKST: '2026-09-22' }]).length, 1);
});
test('빈 목록과 최신 경기순 정렬', () => {
  assert.deepEqual(groupMatches([]), []);
  const newer = { ...demoMatches[1], seriesId: 'new', dateKST: '2026-09-22' };
  assert.equal(groupMatches([...demoMatches, newer])[0].dateKST, '2026-09-22');
});
