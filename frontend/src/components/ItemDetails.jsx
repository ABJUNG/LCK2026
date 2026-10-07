import { useEffect, useRef } from 'react';
import { descriptionText } from '../utils/gameDescription';
export default function ItemDetails({ id, assets, onSelect, onClose }) {
  const heading = useRef(null);
  useEffect(() => { heading.current?.focus({ preventScroll: true }); heading.current?.scrollIntoView({ block: 'center', behavior: 'instant' }); }, [id]);
  const item = assets?.items?.[id];
  return <section className="item-inspector" aria-label="아이템 상세">
    <div className="flex items-start justify-between gap-3"><h3 ref={heading} tabIndex={-1} className="build-section-title font-bold">{item?.name || `아이템 #${id}`}</h3><button className="inspector-close" onClick={onClose}>상세 닫기</button></div>
    {!item ? <p className="game-description">해당 경기 패치의 아이템 설명이 없습니다.</p> : <>
      <div className="my-3 flex items-center gap-3"><img src={`${assets.base}/img/item/${item.image.full}`} alt="" width="48" height="48" /><p className="text-xs text-zinc-400">자료 패치 {assets.version}<br />{item.gold ? `총 가격 ${item.gold.total} · 조합 비용 ${item.gold.base} · 판매 ${item.gold.sell} 골드` : '가격 미제공'}</p></div>
      <p className="game-description">{descriptionText(item.description || item.plaintext) || '상세 효과 미제공'}</p>
      <p className="mt-3 text-xs text-zinc-400">패치 자료의 조합 관계이며 실제 구매 순서와는 다릅니다. 변신·업그레이드 관계가 포함될 수 있습니다.</p>
      {[['from', '하위 재료'], ['into', '연결 아이템']].map(([field, title]) => <div key={field} className="mt-4"><h4 className="mb-2 text-xs font-semibold text-zinc-300">{title}</h4>
        {item[field]?.length ? <div className="item-relations">{item[field].map((relatedId, i) => { const related = assets.items[relatedId]; return <button key={`${relatedId}-${i}`} onClick={() => onSelect(relatedId)} className="item-relation">
          {related && <img src={`${assets.base}/img/item/${related.image.full}`} alt="" width="32" height="32" />}<span>{related?.name || `아이템 #${relatedId}`}</span>
        </button>; })}</div> : <p className="text-xs text-zinc-400">등록된 {title} 없음</p>}
      </div>)}
    </>}
  </section>;
}
