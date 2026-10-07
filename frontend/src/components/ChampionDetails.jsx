import { useEffect, useState } from 'react';
import { loadChampionDetails } from '../utils/championDetails';
import { descriptionText } from '../utils/gameDescription';
function ChampionContent({ champion, assets }) {
  const [state, setState] = useState({ loading: true });
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    loadChampionDetails(assets, champion).then(data => { if (active) setState({ data }); })
      .catch(() => { if (active) setState({ error: true }); });
    return () => { active = false; };
  }, [champion, assets, retry]);
  if (state.loading) return <p role="status">챔피언 정보를 불러오는 중입니다…</p>;
  if (state.error) return <p role="alert">해당 패치의 챔피언 정보를 불러오지 못했습니다. <button className="state-action" onClick={() => { setState({ loading: true }); setRetry(n => n + 1); }}>다시 시도</button></p>;
  const data = state.data;
  return <div className="space-y-4">
    <div className="flex items-center gap-3"><img width="48" height="48" src={`${assets.base}/img/champion/${data.image.full}`} alt="" /><div><h4 className="font-bold">{data.name}</h4><p className="text-xs text-zinc-400">{data.title} · 자료 패치 {assets.version}</p></div></div>
    <p className="text-xs text-zinc-400">기본 스킬 설명입니다. 레벨·아이템에 따른 실시간 수치는 계산하지 않습니다.</p>
    {[{ ...data.passive, slot: '패시브', folder: 'passive' }, ...data.spells.map((spell, i) => ({ ...spell, slot: ['Q', 'W', 'E', 'R'][i], folder: 'spell' }))].map(skill => <article key={skill.slot} className="game-skill">
      <img src={`${assets.base}/img/${skill.folder}/${skill.image.full}`} alt="" width="40" height="40" />
      <div><h5 className="font-semibold"><span className="skill-key">{skill.slot}</span>{skill.name}</h5><p className="game-description">{descriptionText(skill.description)}</p>
      {skill.cooldownBurn && <p className="mt-2 text-xs text-zinc-400">기본 재사용 대기시간 {skill.cooldownBurn}초</p>}</div>
    </article>)}
  </div>;
}
export default function ChampionDetails({ champion, assets, unavailable }) {
  const [open, setOpen] = useState(false);
  return <section><details onToggle={event => setOpen(event.currentTarget.open)}>
    <summary className="champion-summary build-section-title font-bold text-sm">{champion} · 챔피언과 스킬 알아보기</summary>
    <div className="mt-4 text-sm">{assets ? open && <ChampionContent key={`${assets.version}:${champion}`} champion={champion} assets={assets} /> : <p>{unavailable ? '경기 패치 자료가 없어 설명을 제공하지 않습니다.' : '경기 패치 자료를 준비하고 있습니다…'}</p>}</div>
  </details></section>;
}
