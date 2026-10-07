import { lazy, Suspense, useId, useRef, useState } from 'react';
import TeamLogo from './TeamLogo';
import MatchLoading from './MatchLoading';
import { ArrowUpRight, ChevronUp } from 'lucide-react';
import { fetchSeriesDetails } from '../utils/matchRepository';
const MatchCard = lazy(() => import('./Matchcard.jsx'));
export default function SeriesPreview({ summary }) {
  const [open, setOpen] = useState(false);
  const [details, setDetails] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const pending = useRef(false);
  const id = useId();
  async function load() {
    if (pending.current) return;
    pending.current = true; setLoading(true); setError('');
    try { setDetails(await fetchSeriesDetails(summary)); }
    catch { setError('경기 상세 기록을 불러오지 못했습니다. 다시 시도하거나 목록을 새로고침해 주세요.'); }
    finally { pending.current = false; setLoading(false); }
  }
  function toggle() {
    setOpen(!open);
    if (!open && !details && !loading) load();
  }
  return <section className="space-y-3">
    <button type="button" onClick={toggle} aria-expanded={open} aria-controls={id} className="series-preview" data-open={open}>
      <span className="series-meta">
        <span className="competition-tag">{summary.competitionLabel || summary.tournament}</span>
        <span>{summary.stage ? ({PLAY_IN: '플레이인', PLAYOFFS: '플레이오프', FINALS: '결승', ROUNDS_1_2: '1~2라운드', ROUNDS_3_4: '3~4라운드'}[summary.stage] || summary.stage) : '경기 기록'}</span>
        <span className="series-date">{summary.dateKST} · {summary.timeKST} KST</span>
      </span>
      <span className="series-matchup">
        <span className="series-team"><TeamLogo team={summary.teamA} className="h-11 w-11 sm:h-12 sm:w-12" /><strong>{summary.teamA}</strong></span>
        <span className="series-score"><span>{summary.score?.teamA ?? '—'}</span><span className="score-divider">:</span><span>{summary.score?.teamB ?? '—'}</span></span>
        <span className="series-team team-right"><TeamLogo team={summary.teamB} className="h-11 w-11 sm:h-12 sm:w-12" /><strong>{summary.teamB}</strong></span>
        <span className="series-action" aria-hidden="true">{open ? <ChevronUp size={21} /> : <ArrowUpRight size={21} />}</span>
      </span>
      <span className="series-bottom"><span>수집된 {summary.setCount}세트 · 마지막 수집 세트 기준 점수</span><span className="series-open-label">{open ? '접기' : '경기 펼치기'}</span></span>
    </button>
    {open && <div id={id}>{loading && <MatchLoading />}{error && <p role="alert" className="archive-state archive-detail-error">{error} <button onClick={load} className="state-action">다시 시도</button></p>}{details && <Suspense fallback={<MatchLoading label="경기 화면을 준비하는 중입니다" />}><MatchCard seriesData={details} /></Suspense>}</div>}
  </section>;
}
