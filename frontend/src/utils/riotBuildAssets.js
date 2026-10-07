// Match the real game version; never silently replace historical items with latest ones.
const cache = new Map();
async function json(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error('게임 자료를 불러오지 못했습니다.');
  return response.json();
}
export function loadBuildAssets(gameVersion) {
  const patch = String(gameVersion || '').split('.').slice(0, 2).join('.');
  if (!/^\d+\.\d+$/.test(patch)) return Promise.reject(new Error('경기 패치 정보가 없습니다.'));
  if (!cache.has(patch)) {
    const pending = (async () => {
      const versions = await json('https://ddragon.leagueoflegends.com/api/versions.json');
      const version = versions.find(v => v.startsWith(`${patch}.`));
      if (!version) throw new Error('경기 패치에 맞는 한글 자료가 없습니다.');
      const base = `https://ddragon.leagueoflegends.com/cdn/${version}`;
      const [items, spells, runes, perks] = await Promise.all([
        json(`${base}/data/ko_KR/item.json`), json(`${base}/data/ko_KR/summoner.json`),
        json(`${base}/data/ko_KR/runesReforged.json`),
        json(`https://raw.communitydragon.org/${patch}/plugins/rcp-be-lol-game-data/global/ko_kr/v1/perks.json`).catch(() => []),
      ]);
      return { version, base, items: items.data,
        spells: Object.fromEntries(Object.values(spells.data).map(s => [s.key, s])), runes,
        perks: Object.fromEntries(perks.map(p => [p.id, { ...p, image: `https://raw.communitydragon.org/${patch}/plugins/rcp-be-lol-game-data/global/default/${p.iconPath.replace('/lol-game-data/assets/', '').toLowerCase()}` }])) };
    })();
    cache.set(patch, pending);
    pending.catch(() => cache.delete(patch));
  }
  return cache.get(patch);
}
export function groupItemEvents(events = []) {
  const groups = [];
  for (const event of [...events].sort((a, b) => a.timestampMs - b.timestampMs)) {
    const minute = Math.floor(event.timestampMs / 60000);
    if (groups.at(-1)?.minute !== minute) groups.push({ minute, events: [] });
    groups.at(-1).events.push(event);
  }
  return groups;
}
