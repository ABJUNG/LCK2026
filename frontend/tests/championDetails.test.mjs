import test from 'node:test';
import assert from 'node:assert/strict';
import { loadChampionDetails } from '../src/utils/championDetails.js';
import { descriptionText } from '../src/utils/gameDescription.js';
test('영문 표시명이 다른 챔피언도 동일 패치의 한글 상세로 조회하고 캐시한다', async t => {
  const urls = [];
  const assets = { version: '16.18.1', base: 'https://ddragon.leagueoflegends.com/cdn/16.18.1' };
  t.mock.method(globalThis, 'fetch', async url => {
    urls.push(url);
    return { ok: true, json: async () => url.endsWith('/en_US/champion.json') ? { data: { MonkeyKing: { id: 'MonkeyKing', name: 'Wukong' } } } : { data: { MonkeyKing: { name: '오공', spells: [] } } } };
  });
  assert.equal((await loadChampionDetails(assets, 'Wukong')).name, '오공');
  await loadChampionDetails(assets, 'Wukong');
  assert.deepEqual(urls, [`${assets.base}/data/en_US/champion.json`, `${assets.base}/data/ko_KR/champion/MonkeyKing.json`]);
});
test('패치가 없으면 요청하지 않고, 조회 실패 후 같은 패치로 재시도한다', async t => {
  let calls = 0;
  t.mock.method(globalThis, 'fetch', async () => { calls++; return { ok: false }; });
  await assert.rejects(loadChampionDetails(null, 'Ahri'));
  assert.equal(calls, 0);
  const assets = { version: '16.17.1', base: 'https://ddragon.leagueoflegends.com/cdn/16.17.1' };
  await assert.rejects(loadChampionDetails(assets, 'Ahri'));
  await assert.rejects(loadChampionDetails(assets, 'Ahri'));
  assert.equal(calls, 2);
});
test('게임 설명은 HTML을 실행하지 않고 미해결 수치를 명시한다', () => {
  assert.equal(descriptionText('<mainText>공격력 10<br />피해 {{ damage }} / @Value@</mainText>'), '공격력 10\n피해 수치 미제공 / 수치 미제공');
});
