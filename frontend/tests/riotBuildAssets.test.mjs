import test from 'node:test';
import assert from 'node:assert/strict';
import { groupItemEvents, loadBuildAssets } from '../src/utils/riotBuildAssets.js';
test('구매 취소를 포함해 시간순·같은 분 단위로 묶고 입력은 보존한다', () => {
  const events = [{ timestampMs: 60001, type: 'ITEM_SOLD' }, { timestampMs: 0, type: 'ITEM_PURCHASED' }, { timestampMs: 0, type: 'ITEM_UNDO' }];
  const before = structuredClone(events);
  const groups = groupItemEvents(events);
  assert.deepEqual(groups.map(g => g.minute), [0, 1]);
  assert.deepEqual(groups[0].events.map(e => e.type), ['ITEM_PURCHASED', 'ITEM_UNDO']);
  assert.deepEqual(events, before);
});
test('패치 누락을 최신 패치로 추측하지 않는다', async () => {
  await assert.rejects(loadBuildAssets(null));
});
