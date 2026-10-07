import { useEffect, useId, useRef, useState } from 'react';
import { loadChampionDetails } from '../utils/championDetails';
import { descriptionText } from '../utils/gameDescription';
const keys = ['', 'Q', 'W', 'E', 'R'];
const time = ms => Number.isFinite(ms) && ms >= 0 ? `${Math.floor(ms / 60000)}:${String(Math.floor(ms / 1000) % 60).padStart(2, '0')}` : '시각 미제공';
export default function SkillTimeline({ events, champion, assets, unavailable }) {
  const [state, setState] = useState({ loading: true });
  const [retry, setRetry] = useState(0);
  const [selected, setSelected] = useState(null);
  const closeTimer = useRef(null);
  const [position, setPosition] = useState(null);
  const detailId = useId();
  useEffect(() => {
    if (!assets) return;
    let active = true;
    loadChampionDetails(assets, champion).then(data => { if (active) setState({ data }); })
      .catch(() => { if (active) setState({ error: true }); });
    return () => { active = false; };
  }, [assets, champion, retry]);
  function cancelClose() { clearTimeout(closeTimer.current); }
  function hide() { cancelClose(); setSelected(null); }
  function scheduleClose() { cancelClose(); closeTimer.current = setTimeout(() => setSelected(null), 100); }
  function show(index, target) {
    cancelClose();
    const rect = target.getBoundingClientRect();
    setPosition({ left: Math.max(8, Math.min(rect.left, window.innerWidth - 368)),
      top: rect.bottom < window.innerHeight / 2 ? rect.bottom + 6 : undefined,
      bottom: rect.bottom >= window.innerHeight / 2 ? window.innerHeight - rect.top + 6 : undefined });
    setSelected(index);
  }
  useEffect(() => {
    const close = e => {
      if (e.target instanceof Element && e.target.closest('[role="tooltip"]')) return;
      clearTimeout(closeTimer.current);
      setSelected(null);
    };
    window.addEventListener('resize', close);
    window.addEventListener('scroll', close, true);
    return () => { clearTimeout(closeTimer.current); window.removeEventListener('resize', close); window.removeEventListener('scroll', close, true); };
  }, []);
  const event = selected === null ? null : events[selected];
  const spell = event && state.data?.spells?.[event.skillSlot - 1];
  return <section>
    <h3 className="mb-3 text-sm font-bold build-section-title">스킬 습득 순서</h3>
    <p className="mb-3 text-xs text-slate-400">숫자는 습득 순서입니다. 스킬에 마우스를 올리면 설명이 나타납니다. 터치 화면에서는 눌러 확인할 수 있습니다.</p>
    {assets && state.error && <p role="alert" className="mb-3 text-xs text-amber-300">스킬 설명을 불러오지 못했습니다. 습득 기록은 계속 볼 수 있습니다. <button className="filter-reset" onClick={() => { setState({ loading: true }); setRetry(n => n + 1); }}>설명 다시 불러오기</button></p>}
    <div className="flex flex-wrap gap-2">{events.map((entry, index) => {
      const skill = state.data?.spells?.[entry.skillSlot - 1];
      return <div key={index} className="skill-step text-center">
        <span className="block text-[10px] text-slate-400">{index + 1}</span>
        <button type="button" aria-describedby={selected === index ? detailId : undefined}
          aria-label={`${index + 1}번째, ${keys[entry.skillSlot] || '미확인'} ${skill?.name || '스킬'}, ${time(entry.timestampMs)} 상세 보기`}
          onPointerEnter={e => { if (e.pointerType !== 'touch') show(index, e.currentTarget); }}
          onPointerLeave={e => { if (e.pointerType !== 'touch') scheduleClose(); }}
          onFocus={e => { if (e.currentTarget.matches(':focus-visible')) show(index, e.currentTarget); }}
          onBlur={hide}
          onClick={e => { if (window.matchMedia('(hover: none)').matches) { if (selected === index) hide(); else show(index, e.currentTarget); } }}
          onKeyDown={e => { if (e.key === 'Escape' && selected !== null) { e.preventDefault(); e.stopPropagation(); hide(); } }}
          data-active={selected === index}
          className={`skill-timeline-button ${entry.skillSlot === 4 ? 'skill-ultimate' : ''}`}>
          {skill?.image && <img src={`${assets.base}/img/spell/${skill.image.full}`} width="40" height="40" alt="" onError={e => { e.currentTarget.style.visibility = 'hidden'; }} />}
          <span>{keys[entry.skillSlot] || '?'}</span>
        </button>
        <span className="mt-1 block text-[10px] text-slate-400">{time(entry.timestampMs)}</span>
      </div>;
    })}</div>
    {event && <div id={detailId} role="tooltip" style={position} onPointerEnter={cancelClose} onPointerLeave={scheduleClose} className="skill-hover-tooltip">
      <h4 className="mb-2 font-semibold text-sm text-lime-200">{keys[event.skillSlot] || '미확인'} · {spell?.name || '스킬 정보'}</h4>
      <p className="text-xs text-zinc-400">{selected + 1}번째 습득 · {time(event.timestampMs)} · 이 스킬의 {events.slice(0, selected + 1).filter(e => e.skillSlot === event.skillSlot).length}번째 습득 기록</p>
      {spell ? <>
        <p className="game-description">{descriptionText(spell.description) || '설명 미제공'}</p>
        {spell.cooldownBurn && <p className="mt-3 text-xs text-zinc-300">레벨별 기본 재사용 대기시간: {spell.cooldownBurn}초</p>}
        <p className="mt-2 text-xs text-zinc-400">자료 패치 {assets.version} · 기본 스킬 설명입니다. 습득 횟수는 수집 기록 기준이며 실제 스킬 레벨과 다를 수 있습니다. 아이템과 스킬 가속은 반영하지 않습니다.</p>
      </> : <p role="status" className="game-description">{!assets ? unavailable ? '경기 패치 자료가 없어 설명을 제공하지 않습니다.' : '경기 패치 자료를 준비하고 있습니다…' : state.loading ? '스킬 설명을 불러오는 중입니다…' : '해당 패치의 스킬 설명을 확인할 수 없습니다.'}</p>}
    </div>}
  </section>;
}
