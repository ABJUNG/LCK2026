import ReviewText from './ReviewText';

const messages = {
  not_generated: '아직 분석이 없습니다.', pending: '분석을 준비하고 있습니다.',
  running: '경기 기록을 분석하고 있습니다.', failed: '분석을 완료하지 못했습니다. 경기 기록은 계속 확인할 수 있습니다.',
  stale: '경기 기록이 변경되어 재분석이 필요합니다.',
};

function Claim({ claim, facts }) {
  const usesCommentary = claim.factIds.some(id => facts.some(f => f.id === id && f.type === 'community_opinion'));
  return <div className="review-claim space-y-2">
    <p className="leading-relaxed text-slate-200">{claim.text}</p>
    {usesCommentary && <span className="inline-block text-[11px] text-sky-300">관전평 참고</span>}
    <details className="review-evidence text-xs text-slate-400"><summary className="cursor-pointer hover:text-slate-200">해석에 사용한 근거</summary>
      <ul className="mt-2 space-y-1 border-l-2 border-slate-600 pl-3">{claim.factIds.map(id => <li key={id}>{facts.find(f => f.id === id)?.text || '근거 기록 미확인'}</li>)}</ul>
    </details>
  </div>;
}

export default function ReviewPanel({ review, setNumber, commentary }) {
  const available = review?.status === 'generated';
  const report = available && review.report;
  const facts = review?.facts || [];
  const source = review?.commentarySource || commentary;
  const sourceUrl = typeof source?.url === 'string' && source.url.startsWith('https://namu.wiki/w/') ? source.url : null;
  return <section aria-label={`${setNumber}세트 AI 분석`} className="review-panel space-y-4 px-4 py-5 text-sm">
    <div className="flex flex-wrap items-center gap-2"><h5 className="review-title font-bold">경기 요약 · {setNumber}세트</h5><span className="review-badge px-2 py-1 text-[10px]">{available ? 'AI 추정' : '분석 상태'}</span></div>
    {report ? <>
      <Claim claim={report.summary} facts={facts} />
      <details className="review-expansion p-4"><summary className="cursor-pointer font-semibold review-expansion-title">밴픽과 경기 흐름</summary>
        <div className="review-columns mt-4">{[['draft', '밴픽 포인트'], ['turningPoints', '경기 흐름']].map(([key, title]) => <div key={key} className="review-topic space-y-3">
          <h6 className="review-topic-title"><span aria-hidden="true">{key === 'draft' ? '01' : '02'}</span>{title}</h6>
          {report[key].map((claim, index) => <Claim key={index} claim={claim} facts={facts} />)}
        </div>)}</div>
      </details>
      <p className="review-limitation text-xs leading-relaxed">{review.limitation}</p>
    </> : available && review.summary ? <ReviewText text={review.summary} /> : <p className="text-xs text-slate-400">{messages[review?.status] || messages.not_generated}</p>}
    {sourceUrl && <aside className="space-y-2 border-t border-slate-700 pt-3 text-xs leading-relaxed text-slate-400">
      {commentary?.paragraphs?.length > 0 && <details><summary className="cursor-pointer text-sky-300">사용자 제공 관전평 · 요약본</summary>
        <ul className="mt-2 list-disc space-y-2 pl-4">{commentary.paragraphs.map((text, index) => <li key={index}>{text}</li>)}</ul>
      </details>}
      <p>관전평 출처: <a className="text-sky-300 underline" href={sourceUrl} target="_blank" rel="noreferrer">{source.title}</a></p>
      <p>{source.attribution} · <a className="underline" href="https://creativecommons.org/licenses/by-nc-sa/2.0/kr/" target="_blank" rel="noreferrer">{source.license}</a> · 사용자 제공 {source.providedAt}</p>
      <p>사용자가 전달한 내용을 요약·재구성했습니다. 원문 및 영상과 독립 대조하지 않았습니다. 관전평을 반영한 해석은 동일한 비영리·동일조건변경허락 조건으로 제공합니다.</p>
    </aside>}
  </section>;
}
