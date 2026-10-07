import test from 'node:test';
import assert from 'node:assert/strict';
import { groupMatches, orientBySide } from '../src/utils/groupMatches.js';
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

// 과거 문서를 새 시리즈에 추측으로 병합하지 않는 이전 정책.
test('원본 ID 없는 과거 세트와 새 세트는 추측으로 병합하지 않는다', () => {
  const legacy = { ...demoMatches[1] };
  delete legacy.seriesId;
  const groups = groupMatches([legacy, demoMatches[0]]);
  assert.equal(groups.length, 2);
  assert.equal(groups.reduce((count, group) => count + group.sets.length, 0), 2);
});
test('동일 대진 재대결 중 ID 없는 문서를 어느 시리즈에도 임의 편입하지 않는다', () => {
  const legacy = { ...demoMatches[1] };
  delete legacy.seriesId;
  assert.equal(groupMatches([legacy, demoMatches[0], { ...demoMatches[0], seriesId: 'rematch' }]).length, 3);
});

test('진영 변경 시 오브젝트도 해당 팀으로 이동한다', () => {
  const input = structuredClone(demoMatches);
  input[0].objects = { teamA: { dragons: 3 }, teamB: { dragons: 0 } };
  const [series] = groupMatches(input);
  assert.equal(series.sets[1].objects.teamA.dragons, 0);
  assert.equal(series.sets[1].objects.teamB.dragons, 3);
});

test('세트 진영 변경 시 선수·밴·오브젝트·스코어를 함께 이동하고 시리즈 스코어는 유지한다', () => {
  const input = structuredClone(demoMatches);
  input[0].teamSides = { teamA: 'BLUE', teamB: 'RED' };
  input[0].objects = { teamA: { towers: 9 }, teamB: { towers: 2 } };
  input[0].score = { teamA: 1, teamB: 2 };
  input[1].teamSides = { teamA: 'BLUE', teamB: 'RED' };
  const before = structuredClone(input);
  const [series] = groupMatches(input);
  const set = series.sets[1];
  assert.deepEqual(set.teamSides, { teamA: 'RED', teamB: 'BLUE' });
  assert.deepEqual(set.score, { teamA: 2, teamB: 1 });
  const displayed = orientBySide(set);
  assert.equal(displayed.teamA, 'T1');
  assert.deepEqual(displayed.teamSides, { teamA: 'BLUE', teamB: 'RED' });
  assert.equal(displayed.players.teamA[0].name, 'T1 예제 2');
  assert.deepEqual(displayed.bans.teamA, ['Garen']);
  assert.equal(displayed.objects.teamA.towers, 9);
  assert.deepEqual(displayed.score, { teamA: 1, teamB: 2 });
  assert.deepEqual(series.sets[1], set);
  assert.deepEqual(input, before);
});
test('진영 미확인 데이터는 팀 순서를 추측해서 바꾸지 않는다', () => {
  const set = demoMatches[0];
  assert.equal(orientBySide(set), set);
  assert.equal(orientBySide({ ...set, teamSides: { teamA: 'RED' } }).teamA, set.teamA);
});
