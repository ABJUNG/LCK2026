// 같은 시리즈에서도 진영에 따라 팀 A/B가 바뀔 수 있습니다.
const timestamp = match => Date.parse(`${match.dateKST}T${match.timeKST || '00:00'}:00+09:00`) || 0;
const setOrder = (a, b) => Number(a.setNumber) - Number(b.setNumber) || timestamp(a) - timestamp(b);

function alignTeams(match, teamA) {
  if (match.teamA === teamA) return { ...match };
  const aligned = { ...match, teamA: match.teamB, teamB: match.teamA };
  for (const field of ['players', 'bans', 'score']) {
    if (match[field]) aligned[field] = { ...match[field], teamA: match[field].teamB, teamB: match[field].teamA };
  }
  return aligned;
}

export function groupMatches(matches) {
  const groups = new Map();
  for (const match of matches) {
    // 원본 시리즈 ID가 없는 기존 문서는 대회·날짜·팀 조합으로 묶습니다.
    // 같은 날 같은 대회에서 같은 팀이 두 번 맞붙는 경우는 원본 ID가 필요합니다.
    const teams = [match.teamA, match.teamB].sort();
    const key = JSON.stringify(match.seriesId
      ? ['series', match.tournament, match.seriesId]
      : ['legacy', match.tournament, match.dateKST, ...teams]);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(match);
  }
  return [...groups].map(([seriesKey, matchesInSeries]) => {
    const sorted = [...matchesInSeries].sort(setOrder);
    const first = sorted[0];
    return {
      seriesKey, dateKST: first.dateKST, timeKST: first.timeKST,
      teamA: first.teamA, teamB: first.teamB,
      tournament: first.tournament, week: first.week,
      sets: sorted.map(match => alignTeams(match, first.teamA)),
    };
  }).sort((a, b) => timestamp(b) - timestamp(a));
}
