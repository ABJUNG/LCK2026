const player = (name, champion, damage) => ({ name, role: 'Mid', champion, damage, kills: 2, deaths: 1, assists: 3 });
const base = { tournament: '개발 예제', dateKST: '2026-09-21', week: '예제', seriesId: 'demo-series' };
export const demoMatches = [
  { ...base, id: 'demo-2', setNumber: '2', timeKST: '18:00', teamA: 'T1', teamB: 'Gen.G',
    score: { teamA: 1, teamB: 1 }, players: { teamA: [player('T1 예제 2', 'Ahri', 20000)], teamB: [player('GEN 예제 2', 'Azir', 15000)] },
    bans: { teamA: ['Garen'], teamB: ['Lux'] }, aiReview: { patchVersion: '예제', summary: '2세트 전환 확인용 문장입니다. AI가 생성한 실제 분석이 아닙니다.' } },
  { ...base, id: 'demo-1', setNumber: '1', timeKST: '17:00', teamA: 'Gen.G', teamB: 'T1',
    score: { teamA: 1, teamB: 0 }, players: { teamA: [player('GEN 예제 1', 'Azir', 12000)], teamB: [player('T1 예제 1', 'Ahri', 10000)] },
    bans: { teamA: ['Lux'], teamB: ['Garen'] }, aiReview: { patchVersion: '예제', summary: '1세트 전환 확인용 문장입니다. 실제 경기 데이터가 아닙니다.' } },
];
export async function loadDemoMatches(mode, attempt) {
  await new Promise(resolve => setTimeout(resolve, 1200));
  if (mode === 'error' || (mode === 'retry' && attempt === 0)) throw new Error('예제 조회 실패');
  return mode === 'empty' ? [] : demoMatches;
}
