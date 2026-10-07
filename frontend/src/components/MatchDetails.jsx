import { Shield, TowerControl, Bug, Coins, Swords, Gem, Circle } from 'lucide-react';

const rows = [
  ['kills', '팀 킬', Swords], ['gold', '팀 골드', Coins],
  ['dragons', '드래곤 합계 · 장로 포함'], ['infernals', '화염 드래곤'], ['mountains', '대지 드래곤'],
  ['chemtechs', '화학공학 드래곤'], ['clouds', '바람 드래곤'], ['oceans', '바다 드래곤'],
  ['hextechs', '마법공학 드래곤'], ['elders', '장로 드래곤'], ['barons', '바론'], ['heralds', '협곡의 전령'],
  ['grubs', '공허 유충', Bug], ['towers', '포탑 파괴', TowerControl],
  ['inhibitors', '억제기 파괴', Gem], ['plates', '포탑 방패 파괴 기록', Shield], ['soul', '드래곤 영혼', Circle],
];
const names = { FIRE_DRAGON: '화염 드래곤', EARTH_DRAGON: '대지 드래곤', CHEMTECH_DRAGON: '화학공학 드래곤',
  AIR_DRAGON: '바람 드래곤', WATER_DRAGON: '바다 드래곤', HEXTECH_DRAGON: '마법공학 드래곤',
  ELDER_DRAGON: '장로 드래곤', BARON_NASHOR: '바론', RIFTHERALD: '협곡의 전령', HORDE: '공허 유충',
  ATAKHAN: '아타칸', TOWER_BUILDING: '포탑', INHIBITOR_BUILDING: '억제기', plate: '포탑 방패', soul: '드래곤 영혼',
  Infernal: '화염', Mountain: '대지', Chemtech: '화학공학', Cloud: '바람', Ocean: '바다', Hextech: '마법공학',
  TOP_LANE: '탑', MID_LANE: '미드', BOT_LANE: '바텀' };
const playerFields = {
  champLevel: '레벨', physicalDamageDealtToChampions: '물리 챔피언 피해', magicDamageDealtToChampions: '마법 챔피언 피해',
  trueDamageDealtToChampions: '고정 챔피언 피해', totalDamageTaken: '받은 피해', damageSelfMitigated: '경감한 피해',
  damageDealtToTurrets: '포탑 피해', damageDealtToObjectives: '오브젝트 피해', totalHeal: '총 회복',
  totalHealsOnTeammates: '아군 회복', totalDamageShieldedOnTeammates: '아군 보호막', wardsPlaced: '와드 설치',
  wardsKilled: '와드 제거', detectorWardsPlaced: '제어 와드 설치', timeCCingOthers: '적 CC 시간 (초)',
  totalTimeSpentDead: '사망 시간 (초)', neutralMinionsKilled: '정글 몬스터 처치', totalMinionsKilled: '미니언 처치',
  objectivesStolen: '오브젝트 스틸', doubleKills: '더블킬', tripleKills: '트리플킬', quadraKills: '쿼드라킬', pentaKills: '펜타킬',
};
const value = v => v == null ? '미제공' : typeof v === 'number' ? v.toLocaleString('ko-KR') : (names[v] || v);
const clock = ms => `${Math.floor(ms / 60000)}:${String(Math.floor(ms / 1000) % 60).padStart(2, '0')}`;
function Icon({ field, fallback: Fallback }) {
  return Fallback ? <Fallback size={20} aria-hidden="true" className="text-amber-300" />
    : <img src={`/objectives/${field}.png`} alt="" className="h-7 w-7 object-contain" onError={e => { e.currentTarget.style.visibility = 'hidden'; }} />;
}
function objectValue(match, side, field) {
  const v = match.objects?.[side]?.[field];
  if (field === 'plates') return value(v?.total);
  if (field === 'soul' && match.detailCoverage?.timeline === 'available' && !v) return '획득 기록 없음';
  return value(v);
}
export default function MatchDetails({ match }) {
  return <section className="mb-5 rounded-xl border border-slate-700 bg-slate-950/40 p-4 text-sm text-slate-200">
    <h4 className="font-bold text-amber-300">오브젝트 · 경기 상세</h4>
    <p className="my-2 text-xs text-slate-400">경기 시간 {match.gameLength || '미제공'} · 세트 승리 {match.winnerTeam || '미확인'}</p>
    <table className="w-full text-xs"><caption className="sr-only">팀별 오브젝트 획득과 경기 스탯</caption>
      <thead><tr className="border-b border-slate-700"><th className="py-3 text-left">{match.teamA}</th><th>항목</th><th className="text-right">{match.teamB}</th></tr></thead>
      <tbody>{rows.map(([field, label, fallback]) => <tr key={field} className="border-b border-slate-800">
        <td className="py-2 font-mono">{objectValue(match, 'teamA', field)}</td>
        <th className="py-2 font-normal"><span className="flex items-center justify-center gap-2"><Icon field={field} fallback={fallback} />{label}</span></th>
        <td className="text-right font-mono">{objectValue(match, 'teamB', field)}</td>
      </tr>)}</tbody>
    </table>
    <p className="mt-3 text-xs leading-relaxed text-slate-400">0은 원본에 기록된 0입니다. 미제공은 기록 누락 또는 수집 불가를 뜻하며, 해당 패치에 오브젝트가 없었다는 뜻으로 단정하지 않습니다. 방패 수는 타임라인의 파괴 이벤트 수이며 획득 골드가 아닙니다.</p>
    <details className="mt-4 border-t border-slate-700 pt-3"><summary className="cursor-pointer font-bold">라인별 포탑 방패</summary>
      <table className="mt-3 w-full text-xs"><thead><tr><th>팀</th><th>탑</th><th>미드</th><th>바텀</th></tr></thead>
        <tbody>{['teamA', 'teamB'].map(side => <tr key={side}><th className="py-2">{match[side]}</th>{['TOP_LANE', 'MID_LANE', 'BOT_LANE'].map(lane => <td key={lane} className="text-center">{value(match.objects?.[side]?.plates?.[lane])}</td>)}</tr>)}</tbody>
      </table>
    </details>
    <details className="mt-4 border-t border-slate-700 pt-3"><summary className="cursor-pointer font-bold">선수 상세 스탯 · 아이템 · 룬</summary>
      {['teamA', 'teamB'].map(side => <div key={side} className="mt-4"><h5 className="font-bold text-amber-200">{match[side]}</h5>
        {match.players?.[side]?.map(player => <details key={player.role} className="mt-2 rounded bg-slate-900 p-3">
          <summary className="cursor-pointer">{player.name} · {player.champion} · CS {value(player.cs)} · 골드 {value(player.gold)} · 시야 {value(player.vision)}</summary>
          <p className="mt-3 text-xs">아이템: {player.items?.join(' · ') || '미제공'}</p>
          <p className="mt-2 text-xs">소환사 주문: {player.spells?.join(' · ') || '미제공'}</p>
          <p className="mt-2 text-xs">룬: {player.runes || '미제공'}</p>
          <dl className="mt-3 grid grid-cols-1 gap-2 text-xs sm:grid-cols-2">{Object.entries(playerFields).map(([key, label]) => <div key={key} className="flex justify-between gap-3"><dt className="text-slate-400">{label}</dt><dd>{value(player.details?.[key])}</dd></div>)}</dl>
        </details>)}
      </div>)}
    </details>
    <details className="mt-4 border-t border-slate-700 pt-3"><summary className="cursor-pointer font-bold">오브젝트 타임라인 · {match.timeline?.events?.length || 0}개 기록</summary>
      {match.timeline?.status !== 'available' ? <p className="mt-3 text-slate-400">완전한 타임라인을 확인할 수 없습니다.</p> :
        <ol className="mt-3 max-h-80 space-y-2 overflow-auto text-xs">{match.timeline.events.map((event, index) => <li key={index} className="flex flex-wrap gap-2 border-b border-slate-800 pb-2">
          <time className="font-mono text-amber-300">{clock(event.timestampMs)}</time><span>{event.team}</span>
          <span>{names[event.kind] || event.kind}</span><span className="text-slate-400">{names[event.lane] || ''} {event.kind === 'soul' ? value(event.subtype) : ''}</span>
        </li>)}</ol>}
    </details>
    {match.fetchedAt && <p className="mt-4 text-xs text-slate-500">수집 {new Date(match.fetchedAt).toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' })} KST</p>}
  </section>;
}
