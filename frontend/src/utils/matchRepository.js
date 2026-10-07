import { collection, doc, getDoc, getDocs, query, orderBy, limit, startAfter, where } from 'firebase/firestore';
import { db } from '../firebase.js';
import { groupMatches } from './groupMatches.js';
const PAGE_SIZE = 10;
export function createMatchRepository(readMany = getDocs, readOne = getDoc) {
async function fetchSeriesPage(date, cursor, competition = '', season = '2026') {
  const field = competition ? 'catalogSortKey' : 'sortKey';
  const prefix = competition ? `${season}:${competition}|` : '';
  const filters = date ? [where(field, '>=', `${prefix}${date}T00:00`), where(field, '<=', `${prefix}${date}T23:59`)] : competition ? [where(field, '>=', prefix), where(field, '<', `${prefix}\uf8ff`)] : [];
  const result = await readMany(query(collection(db, 'matchSeries'), ...filters, orderBy(field, 'desc'), ...(cursor ? [startAfter(cursor)] : []), limit(PAGE_SIZE)));
  return { items: result.docs.map(d => ({ ...d.data(), id: d.id })), cursor: result.docs.at(-1), hasMore: result.size === PAGE_SIZE };
}
async function fetchSeriesDetails(summary) {
  if (!Array.isArray(summary.setIds) || !summary.setIds.length || new Set(summary.setIds).size !== summary.setIds.length || summary.setIds.length !== summary.setCount) throw new Error('경기 요약을 확인할 수 없습니다.');
  const sets = await Promise.all(summary.setIds.map(id => readOne(doc(db, 'matches', id))));
  if (sets.some(s => !s.exists())) throw new Error('경기 기록 일부가 없습니다. 목록을 새로고침해 주세요.');
  const documents = sets.map(d => ({ ...d.data(), id: d.id }));
  if (documents.some(d => d.seriesId !== summary.seriesId || d.tournament !== summary.tournament)) throw new Error('경기 원본 정보가 일치하지 않습니다.');
  const groups = groupMatches(documents);
  if (groups.length !== 1) throw new Error('경기 상세 기록을 확인할 수 없습니다.');
  return groups[0];
}

return { fetchSeriesPage, fetchSeriesDetails };
}
export const { fetchSeriesPage, fetchSeriesDetails } = createMatchRepository();
