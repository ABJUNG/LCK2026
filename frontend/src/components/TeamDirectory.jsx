import { useEffect, useState } from 'react';
import TeamLogo from './TeamLogo';
const labels = { Top: '탑', Jungle: '정글', Mid: '미드', Bot: '원딜', Support: '서포터', Coach: '코치', 'Head Coach': '감독', 'Interim Head Coach': '감독 대행', Analyst: '분석관', Manager: '매니저', 'Part-Owner': '공동 소유주' };
function Member({ member }) {
  return <details className="roster-member">
    <summary><span className="roster-initial" aria-hidden="true">{member.nickname.slice(0, 1)}</span><span className="min-w-0"><strong>{member.nickname}</strong><span className="roster-role">{member.roles.map(role => labels[role] || role).join(' · ')}</span></span>{member.status === 'inactive' && <span className="roster-status">비활동</span>}{member.roleModifier === 'Sub' && <span className="roster-status">후보</span>}<span className="roster-expand" aria-hidden="true">＋</span></summary>
    <div className="roster-profile"><dl>
      <div><dt>공개 이름</dt><dd>{member.name || '미제공'}</dd></div>
      <div><dt>국가</dt><dd>{member.country === 'South Korea' ? '대한민국' : member.country || '미제공'}</dd></div>
      <div><dt>현재 소속 시작</dt><dd>{member.joinedAt ? `${member.joinedAt}${member.joinedPrecision !== '1' ? ' (정확도 미확인)' : ''}` : '미확인'}</dd></div>
      <div><dt>원문 상태</dt><dd>{!member.roleVerified ? '세부 역할 기록 미확인' : member.status === 'inactive' ? '비활동' : member.status || '별도 표기 없음'}{member.roleModifier ? ` · ${member.roleModifier === 'Sub' ? '후보' : member.roleModifier}` : ''}</dd></div>
    </dl><a href={member.sourceUrl} target="_blank" rel="noreferrer" className="roster-source">Leaguepedia 개인 문서 ↗</a></div>
  </details>;
}
function Rosters() {
  const [state, setState] = useState({ loading: true });
  const [retry, setRetry] = useState(0);
  const [selected, setSelected] = useState('T1');
  useEffect(() => {
    const controller = new AbortController();
    fetch('/team-rosters.json', { signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error();
      const data = await response.json();
      if (data.schemaVersion !== 1 || !Array.isArray(data.teams) || !data.teams.length) throw new Error();
      if (!controller.signal.aborted) setState({ data });
    }).catch(() => { if (!controller.signal.aborted) setState({ error: true }); });
    return () => controller.abort();
  }, [retry]);
  if (state.loading) return <p role="status" className="py-5 text-sm text-zinc-400">팀 명단을 불러오는 중입니다…</p>;
  if (state.error) return <div role="alert" className="archive-state"><p>팀 명단을 불러오지 못했습니다.</p><button className="state-action" onClick={() => { setState({ loading: true }); setRetry(n => n + 1); }}>다시 시도</button></div>;
  const { data } = state;
  const team = data.teams.find(t => t.name === selected) || data.teams[0];
  return <div className="mt-5 space-y-5">
    <p className="text-xs leading-relaxed text-zinc-400">Leaguepedia에 현재 소속으로 표시된 선수와 코칭·지원 스태프입니다. 과거 경기의 출전 명단이나 대회 공식 등록 명단과 다를 수 있습니다.<br />수집: {new Date(data.fetchedAt).toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' })} (한국 시간) · 실시간 갱신 아님</p>
    <div className="roster-team-picker" aria-label="로스터를 볼 팀 선택">{data.teams.map(t => <button key={t.name} onClick={() => setSelected(t.name)} aria-pressed={team.name === t.name}><TeamLogo team={t.name} className="h-7 w-7" /><span>{t.name}</span></button>)}</div>
    <div className="roster-team-header"><div className="flex items-center gap-3"><TeamLogo team={team.name} className="h-10 w-10" /><h4 className="font-bold">{team.name}</h4></div><a href={team.sourceUrl} target="_blank" rel="noreferrer" className="roster-source">팀 원문 ↗</a></div>
    <div className="roster-groups">{[['players', '선수'], ['staff', '코칭·지원 스태프']].map(([group, title]) => <section key={`${team.name}-${group}`}><h5 className="mb-3 text-sm font-semibold text-zinc-300">{title} <span className="text-lime-200">{team.members.filter(m => m.group === group).length}</span></h5><div className="space-y-2">{team.members.filter(m => m.group === group).map(member => <Member key={member.id} member={member} />)}{!team.members.some(m => m.group === group) && <p className="text-xs text-zinc-400">수집된 명단이 없습니다.</p>}</div></section>)}</div>
    <p className="text-xs leading-relaxed text-zinc-400">출처: Leaguepedia 및 기여자 · <a className="underline" href="https://creativecommons.org/licenses/by-sa/3.0/">CC BY-SA 3.0</a>. 공개된 구조화 정보를 팀별로 정리하고 역할명을 번역했습니다. 상세 역할은 확인 가능한 최신 소속 변경 기록을 따릅니다. 인물 사진은 포함하지 않았습니다.</p>
  </div>;
}
export default function TeamDirectory() {
  const [open, setOpen] = useState(false);
  return <section id="teams" className="team-directory scroll-mt-6 mt-10" aria-label="LCK 팀과 멤버"><details onToggle={e => setOpen(e.currentTarget.open)}><summary className="team-directory-summary"><span><span className="eyebrow mb-2">팀 디렉터리</span><span className="text-xl font-bold">LCK 팀과 멤버</span></span><span className="text-xs text-zinc-400">{open ? '접기 −' : '10개 팀 살펴보기 ＋'}</span></summary>{open && <Rosters />}</details></section>;
}
