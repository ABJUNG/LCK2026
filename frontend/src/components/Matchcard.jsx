import { orientBySide } from '../utils/groupMatches';
import TeamLogo from './TeamLogo';
import PlayerBuildDialog from './PlayerBuildDialog';
import { useState } from 'react';
import { Shield, TowerControl, Bug, Gem } from 'lucide-react';
import ReviewPanel from './ReviewPanel';
import { getChampionImageUrl, getRoleNameKr } from '../utils/riot';

const compact = n => n == null ? '—' : n >= 1000 ? `${(n / 1000).toFixed(1)}K` : n;
const kda = p => ['kills', 'deaths', 'assists'].map(k => p?.[k] ?? '—').join('/');
const drakes = [['infernals', '화염'], ['mountains', '대지'], ['chemtechs', '화학공학'], ['clouds', '바람'], ['oceans', '바다'], ['hextechs', '마법공학'], ['elders', '장로']];
const objectives = [['towers', '포탑', TowerControl], ['barons', '바론'], ['heralds', '전령'], ['grubs', '유충', Bug], ['inhibitors', '억제기', Gem], ['plates', '방패', Shield]];
function Portrait({ champion, small = false }) {
  return <img src={getChampionImageUrl(champion)} alt={champion || '미수집'} title={champion} className={`${small ? 'h-5 w-5 min-[400px]:h-6 min-[400px]:w-6 sm:h-8 sm:w-8' : 'h-10 w-10 sm:h-11 sm:w-11'} shrink-0 border border-slate-600 object-cover`} />;
}
function Player({ player, right, mapSide, maxDamage, onSelect }) {
  return <div className={`player-cell flex min-w-0 items-center gap-2 px-2 py-2 ${right ? '' : 'flex-row-reverse text-right'}`}>
    <Portrait champion={player?.champion} />
    <div className="min-w-0 flex-1">
      <button type="button" disabled={!player} onClick={onSelect} className="player-name max-w-full truncate text-sm font-semibold underline underline-offset-4" aria-label={`${player?.name || '미수집'} 선수 빌드 보기`}>{player?.name || '미수집'}</button>
      <div className={`text-[10px] sm:text-xs ${mapSide === 'BLUE' ? 'text-sky-300' : mapSide === 'RED' ? 'text-red-300' : 'text-slate-300'}`}>{compact(player?.damage)} <span className="text-slate-400">({kda(player)})</span></div>
      <div className={`mt-1 flex h-1 ${right ? '' : 'justify-end'}`}><div className={mapSide === 'BLUE' ? 'bg-sky-400' : mapSide === 'RED' ? 'bg-red-400' : 'bg-slate-400'} style={{ width: `${((player?.damage || 0) / maxDamage) * 100}%` }} /></div>
    </div>
  </div>;
}
function ObjectiveStrip({ match, side }) {
  const data = match.objects?.[side] || {};
  return <div className="flex flex-wrap justify-center gap-x-3 gap-y-3 p-3 sm:gap-x-5">
    {objectives.map(([field, label, Icon]) => <div key={field} title={`${label}: ${field === 'plates' ? data.plates?.total ?? '미제공' : data[field] ?? '미제공'}`} className="flex min-w-7 flex-col items-center gap-1 text-xs text-slate-400">
      {Icon ? <Icon size={20} aria-hidden="true" /> : <img src={`/objectives/${field}.png`} alt="" className="h-5 w-5 object-contain" />}
      <span>{label}</span><span className="font-mono text-sm font-semibold text-slate-100">{field === 'plates' ? data.plates?.total ?? '—' : data[field] ?? '—'}</span>
    </div>)}
  </div>;
}
export default function MatchCard({ seriesData }) {
  const [activeTabIndex, setActiveTabIndex] = useState(0);
  const [selected, setSelected] = useState(null);
  if (!seriesData?.sets?.length) return null;
  const match = orientBySide(seriesData.sets[activeTabIndex] || seriesData.sets[0]);
  const knownSides = match.teamSides?.teamA === 'BLUE' && match.teamSides?.teamB === 'RED';
  const last = seriesData.sets.at(-1);
  const maxDamage = Math.max(1, ...['teamA', 'teamB'].flatMap(side => (match.players?.[side] || []).map(p => p.damage || 0)));
  const totalKda = side => ['kills', 'deaths', 'assists'].map(key => {
    const players = match.players?.[side] || [];
    return players.length === 5 && players.every(p => Number.isFinite(p[key])) ? players.reduce((sum, p) => sum + p[key], 0) : '—';
  }).join(' / ');
  return <article className="match-detail overflow-hidden">
    <header className="match-detail-header flex flex-wrap items-center justify-between gap-2 px-4 py-3">
      <div><h3 className="text-sm font-bold text-white">{seriesData.tournament || 'LCK'} · {match.setNumber}세트</h3><p className="mt-1 text-xs text-slate-400">{match.dateKST} {match.timeKST} KST · 패치 {match.patchVersion || match.aiReview?.patchVersion || '미확인'}</p></div>
      <span className="text-xs text-slate-400" title="마지막 수집 세트 기준">{seriesData.teamA} : {seriesData.teamB} · 매치 스코어 <b className="ml-1 text-lg text-white">{last.score?.teamA ?? '—'} : {last.score?.teamB ?? '—'}</b></span>
    </header>
    <nav aria-label="세트 선택" className="set-tabs flex gap-1 px-3 py-2">{seriesData.sets.map((set, index) => <button key={set.id || set.setNumber} aria-pressed={activeTabIndex === index} onClick={() => { setSelected(null); setActiveTabIndex(index); }} className={`rounded px-4 py-2 text-sm font-bold ${activeTabIndex === index ? 'set-tab-active' : 'set-tab-idle'}`}>{set.setNumber}세트</button>)}</nav>
    <div className="grid grid-cols-2">
      {['teamA', 'teamB'].map((side, index) => <h4 key={side} className={`match-team-heading flex items-center justify-center gap-2 px-2 py-3 text-center text-sm sm:text-base font-bold text-white ${knownSides ? index ? 'bg-red-900/80' : 'bg-sky-800/80' : 'bg-slate-800'}`}><TeamLogo team={match[side]} /><span>{match[side]}<span className="mt-1 block text-[10px] font-medium tracking-wide">{knownSides ? index ? '레드 사이드' : '블루 사이드' : '진영 미확인'}</span></span></h4>)}
    </div>
    <div className="grid grid-cols-[minmax(0,1fr)_30px_minmax(0,1fr)] items-center border-b border-slate-700 py-2">
      <div className="flex justify-center gap-1">{match.bans?.teamA?.map((champion, i) => <Portrait key={i} champion={champion} small />)}</div><span className="text-center text-[10px] text-slate-500">밴</span>
      <div className="flex justify-center gap-1">{match.bans?.teamB?.map((champion, i) => <Portrait key={i} champion={champion} small />)}</div>
    </div>
    <div className="grid grid-cols-[minmax(0,1fr)_54px_minmax(0,1fr)] items-center border-b border-slate-700 bg-slate-800/40 py-2 text-center text-xs">
      <div><span className={knownSides ? 'text-sky-200' : 'text-slate-200'}>{totalKda('teamA')}</span><p className="mt-1 text-slate-400">{compact(match.objects?.teamA?.gold)} G · <b className={knownSides ? 'text-sky-300' : 'text-slate-300'}>{match.winnerTeam ? match.winnerTeam === match.teamA ? 'WIN' : 'LOSS' : '—'}</b></p></div>
      <strong className="match-duration">{match.gameLength || '—'}</strong>
      <div><span className={knownSides ? 'text-red-200' : 'text-slate-200'}>{totalKda('teamB')}</span><p className="mt-1 text-slate-400"><b className={knownSides ? 'text-red-300' : 'text-slate-300'}>{match.winnerTeam ? match.winnerTeam === match.teamB ? 'WIN' : 'LOSS' : '—'}</b> · {compact(match.objects?.teamB?.gold)} G</p></div>
    </div>
    {['Top', 'Jungle', 'Mid', 'Bot', 'Support'].map(role => <div key={role} className="grid grid-cols-[minmax(0,1fr)_30px_minmax(0,1fr)] items-center border-b border-slate-800">
      <Player mapSide={match.teamSides?.teamA} player={match.players?.teamA?.find(p => p.role === role)} maxDamage={maxDamage} onSelect={() => setSelected({ side: 'teamA', role })} />
      <span className="text-center text-[9px] text-slate-500">{getRoleNameKr(role)}</span>
      <Player mapSide={match.teamSides?.teamB} player={match.players?.teamB?.find(p => p.role === role)} maxDamage={maxDamage} right onSelect={() => setSelected({ side: 'teamB', role })} />
    </div>)}
    <div className="grid grid-cols-2 border-t-2 border-slate-600 bg-slate-800/50">
      {['teamA', 'teamB'].map(side => <div key={side} className="border-r border-slate-700 last:border-0">
        <div className="flex flex-wrap justify-center gap-2 border-b border-slate-700 px-2 py-2">{drakes.map(([field, label]) => <div key={field} title={`${label} 드래곤 ${match.objects?.[side]?.[field] ?? '미제공'}회`} className={`flex items-center gap-0.5 ${match.objects?.[side]?.[field] === 0 ? 'opacity-30 grayscale' : ''}`}>
          <img src={`/objectives/${field}.png`} alt={`${label} 드래곤`} className="h-5 w-5 object-contain" /><span className="text-xs font-semibold text-slate-200">{match.objects?.[side]?.[field] ?? '—'}</span>
        </div>)}</div>
        <ObjectiveStrip match={match} side={side} />
      </div>)}
    </div>
    <p className="px-3 py-2 text-xs leading-relaxed text-slate-400">선수 이름 클릭: 빌드 상세 · 피해량 (K/D/A) · 드래곤은 종류별 횟수 · — 미제공 · 세트 결과는 왼쪽 블루 · 오른쪽 레드 기준이며, 진영 미확인 시 회색으로 표시합니다.</p>
    <ReviewPanel key={`review-${match.id || match.setNumber}`} review={match.aiReview} setNumber={match.setNumber} commentary={match.communityReview} />
    {selected && <PlayerBuildDialog key={`${match.id}-${selected.side}-${selected.role}`} player={match.players[selected.side].find(p => p.role === selected.role)} team={match[selected.side]} onClose={() => setSelected(null)} />}
  </article>;
}
