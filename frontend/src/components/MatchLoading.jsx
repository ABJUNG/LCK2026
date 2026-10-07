export default function MatchLoading({ count = 1, label = '경기 상세 정보를 불러오는 중입니다' }) {
  return <div role="status" aria-live="polite" className="match-loading">
    <p className="mb-3 flex items-center gap-2 text-xs text-zinc-400"><img src="/favicon.svg" width="20" height="20" alt="" />{label}…</p>
    <div aria-hidden="true" className="space-y-3">{Array.from({ length: count }, (_, index) => <div key={index} className="match-skeleton">
      <div className="skeleton-line skeleton-short" />
      <div className="skeleton-matchup"><span className="skeleton-logo" /><span className="skeleton-line" /><span className="skeleton-score" /><span className="skeleton-line" /><span className="skeleton-logo" /></div>
      <div className="skeleton-line skeleton-footer" />
    </div>)}</div>
  </div>;
}
