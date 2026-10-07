import { createContext, useContext, useEffect, useId, useRef, useState } from 'react';
import { X } from 'lucide-react';
import { loadBuildAssets, groupItemEvents } from '../utils/riotBuildAssets';

import { descriptionText } from '../utils/gameDescription';
import ChampionDetails from './ChampionDetails';
import SkillTimeline from './SkillTimeline';
import ItemDetails from './ItemDetails';
const ItemSelection = createContext(null);

const clock = ms => `${Math.floor(ms / 60000)}:${String(Math.floor(ms / 1000) % 60).padStart(2, '0')}`;
function Asset({ src, name, description, extra, selected = true, small = false, onInspect }) {
  const [failed, setFailed] = useState(false);
  const [position, setPosition] = useState(null);
  const id = useId();
  function open(event) {
    const rect = event.currentTarget.getBoundingClientRect();
    setPosition({ left: Math.max(8, Math.min(rect.left, window.innerWidth - 328)),
      top: rect.bottom < window.innerHeight / 2 ? rect.bottom + 8 : undefined,
      bottom: rect.bottom >= window.innerHeight / 2 ? window.innerHeight - rect.top + 8 : undefined });
  }
  return <span className="inline-flex" onMouseLeave={() => setPosition(null)}>
    <button type="button" aria-label={`${name} ${onInspect ? '상세 보기' : '설명'}`} aria-describedby={position ? id : undefined}
      onMouseEnter={open} onFocus={open} onBlur={() => setPosition(null)} onClick={onInspect ? () => { setPosition(null); onInspect(); } : open}
      onKeyDown={event => { if (event.key === 'Escape' && position) { event.preventDefault(); event.stopPropagation(); setPosition(null); } }}
      className={`build-asset-button rounded focus-visible:outline-2 focus-visible:outline-sky-300 ${selected ? '' : 'opacity-25 grayscale'}`}>
      {src && !failed ? <img src={src} alt={name} onError={() => setFailed(true)} className={`${small ? 'h-7 w-7' : 'h-10 w-10'} rounded border ${selected ? 'border-lime-200/60' : 'border-slate-600'} object-contain bg-slate-950`} />
        : <span className="flex h-10 w-10 items-center justify-center rounded border border-slate-600 text-[9px]">{name}</span>}
    </button>
    {position && <span id={id} role="tooltip" style={position} className="fixed z-50 block max-h-[40dvh] w-80 max-w-[calc(100vw-16px)] overflow-y-auto rounded-lg border border-slate-500 bg-slate-950 p-3 text-left text-xs leading-relaxed text-slate-200 shadow-xl">
      <strong className="mb-2 block text-sm text-lime-200">{name}</strong>
      <span className="block whitespace-pre-line">{descriptionText(description) || '이 패치의 설명이 제공되지 않습니다.'}</span>
      {extra && <span className="mt-2 block border-t border-slate-700 pt-2 text-sky-200">{extra}</span>}
    </span>}
  </span>;
}
function Item({ id, assets }) {
  const selectItem = useContext(ItemSelection);
  const item = assets?.items?.[id];
  const name = id ? item?.name || `아이템 #${id}` : '빈 슬롯';
  return <div className="flex w-14 flex-col items-center gap-1 text-center text-[10px] leading-tight">
    <Asset onInspect={() => selectItem(id)} src={item ? `${assets.base}/img/item/${item.image.full}` : null} name={name} description={item?.description || item?.plaintext} extra={item?.gold ? `가격 ${item.gold.total}골드 · 판매 ${item.gold.sell}골드` : null} /><span>{name}</span>
  </div>;
}
export default function PlayerBuildDialog({ player, team, onClose }) {
  const dialog = useRef(null);
  const [assets, setAssets] = useState(null);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const [selectedItem, setSelectedItem] = useState(null);
  const build = player.build;
  useEffect(() => {
    const element = dialog.current;
    element.showModal();
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => { element.close(); document.body.style.overflow = originalOverflow; };
  }, []);
  useEffect(() => {
    if (!build?.gameVersion) return;
    let cancelled = false;
    loadBuildAssets(build.gameVersion).then(data => { if (!cancelled) { setAssets(data); setError(''); } })
      .catch(() => { if (!cancelled) setError('한글 게임 자료를 불러오지 못했습니다. 원본 ID로 표시합니다.'); });
    return () => { cancelled = true; };
  }, [build?.gameVersion, retry]);
  return <dialog ref={dialog} onCancel={event => { event.preventDefault(); onClose(); }} aria-labelledby="player-build-title" className="player-dialog m-auto max-h-[90dvh] w-[min(960px,94vw)] overflow-y-auto p-0 text-slate-200 shadow-2xl">
    <header className="player-dialog-header sticky top-0 z-10 flex items-center justify-between gap-4 p-4 sm:px-6">
      <div className="min-w-0"><h2 id="player-build-title" className="text-lg font-bold">{player.name} <span className="text-sm text-slate-400">· {team} · {player.champion}</span></h2><p className="text-xs text-slate-400">경기 빌드 · {build?.gameVersion ? `게임 ${build.gameVersion}` : '패치 미확인'}{assets ? ` · 한글 자료 ${assets.version}` : ''}</p></div>
      <button autoFocus onClick={onClose} aria-label="선수 상세 닫기" className="dialog-close shrink-0 p-2"><X size={22} /></button>
    </header>
    <ItemSelection.Provider value={setSelectedItem}><div className="player-dialog-body space-y-4 p-3 sm:p-5">
      {!build ? <p>이 경기의 선수 빌드가 아직 수집되지 않았습니다.</p> : <>
        <ChampionDetails champion={player.champion} assets={assets} unavailable={!build.gameVersion || Boolean(error)} />
        {error ? <p role="alert" className="text-sm text-amber-300">{error} <button className="underline" onClick={() => setRetry(n => n + 1)}>다시 시도</button></p> : !build.gameVersion ? <p className="text-xs text-slate-400">경기 패치가 없어 게임 설명을 제공하지 않습니다.</p> : !assets && <p role="status" className="text-sm text-slate-400">경기 패치의 한글 자료를 불러오는 중입니다.</p>}
        <section><h3 className="mb-3 text-sm font-bold build-section-title">최종 아이템 · 소환사 주문</h3><p className="mb-3 text-xs text-slate-400">아이템을 누르면 효과와 조합 정보를 자세히 볼 수 있습니다.</p><div className="flex flex-wrap items-start gap-2">
          {build.finalItemIds.filter(id => id > 0).map((id, i) => <Item key={i} id={id} assets={assets} />)}
          <div className="build-spells ml-2 flex gap-2 border-l border-slate-700 pl-3">{build.spellIds.filter(id => id > 0).map((id, i) => { const spell = assets?.spells?.[id]; return <div key={i} className="text-center text-xs"><Asset src={spell ? `${assets.base}/img/spell/${spell.image.full}` : null} name={spell?.name || `스펠 #${id ?? '?'}`} description={spell?.description} extra={spell?.cooldownBurn ? `재사용 대기시간 ${spell.cooldownBurn}초` : null} /><p className="mt-1">{spell?.name || '미확인'}</p></div>; })}</div>
        </div></section>
        {selectedItem !== null && <ItemDetails id={selectedItem} assets={assets} onSelect={setSelectedItem} onClose={() => setSelectedItem(null)} />}
        <section><h3 className="mb-1 text-sm font-bold build-section-title">아이템 구매 순서</h3><p className="mb-3 text-xs text-slate-400">같은 분의 기록을 묶었습니다. 구매·판매 기록을 시간순으로 표시하며, 실제 귀환 횟수를 뜻하지 않습니다. 아이콘에 마우스를 올리면 설명을, 누르면 가격과 조합 정보를 확인할 수 있습니다. 되돌리기 기록은 생략합니다.</p>
          {build.timelineStatus !== 'available' ? <p className="text-sm">구매 타임라인 미제공</p> : !build.itemEvents.length ? <p>기록된 구매 이벤트가 없습니다.</p> : <div className="flex flex-wrap gap-3">{groupItemEvents(build.itemEvents.filter(event => ['ITEM_PURCHASED', 'ITEM_SOLD'].includes(event.type) && event.itemId > 0)).map(group => <div key={group.minute} className="build-purchase-group p-3">
            <p className="mb-2 text-xs font-bold text-sky-300">{group.minute}분</p><div className="flex flex-wrap gap-2">{group.events.map((event, i) => <div key={i} className="flex flex-col items-center gap-1">
              <span className={`text-[10px] ${event.type === 'ITEM_PURCHASED' ? 'text-slate-400' : 'text-amber-300'}`}>{clock(event.timestampMs)} · {event.type === 'ITEM_PURCHASED' ? '구매' : event.type === 'ITEM_SOLD' ? '판매' : '되돌리기'}</span>
              {event.type === 'ITEM_UNDO' ? <div className="flex items-center"><Item id={event.beforeId} assets={assets} /><span>→</span><Item id={event.afterId} assets={assets} /></div> : <Item id={event.itemId} assets={assets} />}
            </div>)}</div>
          </div>)}</div>}
        </section>
        {build.skillEvents?.length > 0 && <SkillTimeline key={`${player.champion}-${assets?.version || 'pending'}`} events={build.skillEvents} champion={player.champion} assets={assets} unavailable={!build.gameVersion || Boolean(error)} />}
        <section><h3 className="mb-3 text-sm font-bold build-section-title">룬</h3><div className="flex flex-wrap gap-6">
          {build.runeStyles.map((style, index) => { const tree = assets?.runes.find(r => r.id === style.style); return <div key={index} className="build-rune-group p-3">
            <h4 className="mb-3 text-sm font-semibold">{index === 0 ? '핵심' : '보조'} · {tree?.name || `룬 계열 #${style.style}`}</h4>
            {tree ? tree.slots.map((slot, i) => <div key={i} className="rune-slot mb-3" style={{ gridTemplateColumns: `repeat(${slot.runes.length}, minmax(0, 1fr))` }}>{slot.runes.map(rune => <div key={rune.id} className="rune-option text-center text-[10px]">
              <Asset src={`https://ddragon.leagueoflegends.com/cdn/img/${rune.icon}`} name={rune.name} description={rune.longDesc || rune.shortDesc} selected={style.selectedIds.includes(rune.id)} /><p className={style.selectedIds.includes(rune.id) ? 'mt-1 text-lime-200' : 'mt-1 text-slate-500'}>{rune.name}</p>
            </div>)}</div>) : <p className="text-xs">선택 ID: {style.selectedIds.join(', ')}</p>}
          </div>; })}
          <div className="build-rune-group p-3"><h4 className="mb-3 text-sm font-semibold">능력치 파편</h4>{['offense', 'flex', 'defense'].filter(slot => build.statShards[slot] > 0).map(slot => { const id = build.statShards[slot]; const perk = assets?.perks?.[id]; return <div key={slot} className="mb-3 flex items-center gap-2 text-xs"><Asset src={perk?.image} name={perk?.name || `파편 #${id ?? '?'}`} description={perk?.longDesc || perk?.shortDesc} small /><div><p className="text-slate-500">{{offense:'공격',flex:'유연',defense:'방어'}[slot]}</p><p>{perk?.name || `#${id ?? '?'}`}</p></div></div>; })}</div>
        </div></section>
      </>}
    </div></ItemSelection.Provider>
  </dialog>;
}
