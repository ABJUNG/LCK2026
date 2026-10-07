const cache = new Map();
const normalize = value => String(value || '').toLowerCase().replace(/[^a-z0-9가-힣]/g, '');
async function read(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error('이 패치의 챔피언 자료를 불러오지 못했습니다.');
  return response.json();
}
export function loadChampionDetails(assets, name) {
  if (!assets?.version || !assets?.base || !name) return Promise.reject(new Error('챔피언 또는 경기 패치가 없습니다.'));
  const key = `${assets.version}:${name}`;
  if (!cache.has(key)) {
    const pending = (async () => {
      const index = await read(`${assets.base}/data/en_US/champion.json`);
      const entry = Object.values(index.data).find(c => normalize(c.id) === normalize(name) || normalize(c.name) === normalize(name));
      if (!entry) throw new Error('이 패치에서 챔피언을 찾지 못했습니다.');
      const detail = await read(`${assets.base}/data/ko_KR/champion/${encodeURIComponent(entry.id)}.json`);
      if (!detail.data?.[entry.id]) throw new Error('챔피언 상세 자료가 없습니다.');
      return detail.data[entry.id];
    })();
    cache.set(key, pending);
    pending.catch(() => cache.delete(key));
  }
  return cache.get(key);
}
