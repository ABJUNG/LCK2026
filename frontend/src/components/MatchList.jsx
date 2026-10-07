import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import SeriesPreview from './SeriesPreview';
import { ListFilter, RotateCcw, SearchX, WifiOff, X } from 'lucide-react';
import MatchLoading from './MatchLoading';
import { fetchSeriesPage } from '../utils/matchRepository';
const DemoList = import.meta.env.DEV ? lazy(() => import('../dev/LegacyDemoMatchList')) : null;
function SeriesList() {
  const [competition, setCompetition] = useState('');
  const [catalog, setCatalog] = useState([]);
  useEffect(() => {
    let active = true;
    fetch('/competitions.json').then(r => { if (!r.ok) throw Error(); return r.json(); }).then(data => { if (active) setCatalog(data); }).catch(() => {});
    return () => { active = false; };
  }, []);
  const [date, setDate] = useState('');
  const [revision, setRevision] = useState(0);
  const [state, setState] = useState({ items: [], loading: true, error: '', hasMore: false, cursor: null });
  const generation = useRef(0);
  const pending = useRef(false);
  useEffect(() => {
    const token = ++generation.current;
    pending.current = false;
    fetchSeriesPage(date, null, competition).then(page => {
      if (token === generation.current) setState({ ...page, loading: false, error: '' });
    }).catch(() => {
      if (token === generation.current) setState({ items: [], loading: false, error: '경기 목록을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.', hasMore: false });
    });
    return () => { generation.current = token + 1; };
  }, [date, revision, competition]);
  function refresh(nextDate = date) {
    generation.current++; pending.current = false;
    setState({ items: [], loading: true, error: '', hasMore: false, cursor: null });
    setDate(nextDate); setRevision(n => n + 1);
  }
  function resetFilters() {
    setCompetition('');
    refresh('');
  }
  const filtered = Boolean(competition || date);
  const competitionLabel = catalog.find(entry => entry.id === competition)?.label || competition;
  async function more() {
    if (pending.current || state.loading || !state.hasMore) return;
    pending.current = true;
    const token = generation.current;
    setState(s => ({ ...s, loading: true, error: '' }));
    try {
      const page = await fetchSeriesPage(date, state.cursor, competition);
      if (token === generation.current) setState(s => ({ ...page, items: [...s.items, ...page.items.filter(item => !s.items.some(old => old.id === item.id))], loading: false, error: '' }));
    } catch {
      if (token === generation.current) setState(s => ({ ...s, loading: false, error: '추가 경기를 불러오지 못했습니다. 더 보기를 다시 눌러 주세요.' }));
    } finally { if (token === generation.current) pending.current = false; }
  }
  return <div className="space-y-5">
    <div className="archive-heading"><div><p className="eyebrow">경기 아카이브</p><h3 className="mt-2 text-2xl font-bold tracking-tight">다시 보는 경기</h3></div><p className="hidden text-xs text-zinc-400 sm:block">선수 이름을 누르면 빌드까지 자세히.</p></div>
    <div className="filter-bar flex flex-wrap items-center gap-3 text-sm">
      <label>시즌 <select className="rounded bg-slate-800 p-2" aria-label="시즌" value="2026" onChange={() => {}}><option value="2026">2026</option></select></label>
      <label>대회 <select className="rounded bg-slate-800 p-2" value={competition} onChange={e => { setCompetition(e.target.value); refresh(''); }}><option value="">전체 지원 대회</option>{catalog.map(entry => <option key={entry.id} value={entry.id}>{entry.label}</option>)}</select></label>
      <label>경기 날짜 (KST) <input type="date" value={date} onChange={e => refresh(e.target.value)} className="rounded bg-slate-800 p-2 [color-scheme:dark]" /></label>
      <button onClick={() => refresh()} disabled={state.loading} className="refresh-button inline-flex items-center gap-2"><RotateCcw size={14} aria-hidden="true" />목록 새로고침</button>
    </div>
    <div className="filter-summary" aria-label="현재 조회 조건">
      <span className="filter-summary-label"><ListFilter size={14} aria-hidden="true" />조회 조건</span>
      {competition && <button className="filter-chip" onClick={() => { setCompetition(''); refresh(); }} aria-label={`${competitionLabel} 대회 필터 해제`}>{competitionLabel}<X size={13} aria-hidden="true" /></button>}
      {date && <button className="filter-chip" onClick={() => refresh('')} aria-label={`${date} 날짜 필터 해제`}>{date} · 한국 시간<X size={13} aria-hidden="true" /></button>}
      {!filtered && <span className="text-xs text-zinc-400">2026 시즌 · 전체 지원 대회 · 전체 날짜</span>}
      {filtered && <button onClick={resetFilters} className="filter-reset">필터 초기화</button>}
    </div>
    {state.error && <div role="alert" className="archive-state archive-error">
      <WifiOff size={24} aria-hidden="true" /><div><h4>{state.items.length ? '추가 경기를 가져오지 못했어요' : '경기 목록에 연결하지 못했어요'}</h4>
      <p>{state.items.length ? '이미 불러온 경기는 계속 볼 수 있습니다. 이어서 다시 불러와 주세요.' : '선택한 조건은 유지됩니다. 잠시 후 다시 시도해 주세요.'}</p>
      <button onClick={state.items.length ? more : () => refresh()} className="state-action">다시 시도</button></div>
    </div>}
    {!state.loading && !state.error && !state.items.length && <div className="archive-state archive-empty">
      <SearchX size={30} aria-hidden="true" /><h4>{filtered ? '이 조건에 수집된 경기가 없어요' : '아직 수집된 경기가 없어요'}</h4>
      <p>{filtered ? '다른 대회나 날짜를 선택해 보세요. 아직 수집하지 않은 경기는 표시되지 않습니다.' : '수집이 완료된 경기가 이곳에 표시됩니다. 잠시 후 목록을 새로고침해 주세요.'}</p>
      <button onClick={filtered ? resetFilters : () => refresh()} className="state-action">{filtered ? '필터 초기화하고 전체 보기' : '목록 새로고침'}</button>
    </div>}
    {state.items.map(summary => <SeriesPreview key={`${revision}-${summary.id}`} summary={summary} />)}
    {state.loading && <MatchLoading count={state.items.length ? 1 : 3} label={state.items.length ? '추가 경기를 불러오는 중입니다' : '경기 목록을 불러오는 중입니다'} />}
    {state.hasMore && !state.error && <button disabled={state.loading} onClick={more} className="load-more-button">{state.loading ? '불러오는 중…' : '경기 더 보기'}</button>}
    <p role="status" aria-live="polite" className="text-xs text-zinc-400">{!state.loading && !state.error && (state.items.length > 0 ? `현재 ${state.items.length}경기 표시${state.hasMore ? '' : ' · 수집된 목록의 마지막입니다'} · 경기를 펼치면 선수 기록을 확인할 수 있습니다.` : '표시할 경기 0건')}</p>
  </div>;
}
export default function MatchList() {
  const demo = import.meta.env.DEV && new URLSearchParams(window.location.search).get('demo');
  return demo ? <Suspense fallback={<p>예제 준비 중…</p>}><DemoList /></Suspense> : <SeriesList />;
}
