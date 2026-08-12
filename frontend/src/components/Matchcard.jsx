import React from 'react';

function MatchCard() {
  // 백엔드가 완성되기 전 화면을 그리기 위한 가짜(Dummy) 데이터입니다. [cite: 348]
  const dummyMatch = {
    id: '24SUM-T1-GEN-0812',
    date: '2026. 08. 12 (수) 17:00',
    teamA: 'T1',
    teamB: 'GEN',
    score: { teamA: 1, teamB: 2 },
    status: 'COMPLETED',
    aiReview: {
      patchVersion: '14.12',
      teamADraftScore: 78,
      teamBDraftScore: 92,
      summary: "GEN이 14.12 패치에서 상향된 밸류 픽을 완벽하게 소화하며 후반 한타 집중력으로 승리를 가져갔습니다. T1은 초반 스노우볼을 굴리지 못한 것이 패인입니다."
    }
  };

  return (
    <div className="bg-slate-800 rounded-xl p-5 border border-slate-700 hover:border-amber-400/50 transition-colors">
      {/* 경기 날짜 및 패치 정보 */}
      <div className="flex justify-between items-center mb-4">
        <span className="text-slate-400 text-sm font-medium">{dummyMatch.date}</span>
        <span className="bg-slate-900 text-amber-400 text-xs px-2 py-1 rounded-md border border-slate-700">
          Patch {dummyMatch.aiReview.patchVersion}
        </span>
      </div>

      {/* 경기 결과 스코어 보드 */}
      <div className="flex items-center justify-center gap-6 mb-6">
        <div className="text-2xl font-black text-slate-100">{dummyMatch.teamA}</div>
        <div className="flex items-center gap-3">
          <span className="text-3xl font-bold text-slate-300">{dummyMatch.score.teamA}</span>
          <span className="text-slate-500">vs</span>
          <span className="text-3xl font-bold text-slate-300">{dummyMatch.score.teamB}</span>
        </div>
        <div className="text-2xl font-black text-slate-100">{dummyMatch.teamB}</div>
      </div>

      {/* AI 융합 분석 리포트 */}
      <div className="bg-slate-900/50 rounded-lg p-4">
        <h4 className="text-sm font-bold text-amber-400 mb-2 flex items-center gap-2">
          <span>🤖</span> AI 융합 분석 리포트
        </h4>
        <div className="flex gap-4 mb-3 text-xs text-slate-300">
          <div><span className="text-slate-500 mr-1">{dummyMatch.teamA} 밴픽 평점:</span> {dummyMatch.aiReview.teamADraftScore}점</div>
          <div><span className="text-slate-500 mr-1">{dummyMatch.teamB} 밴픽 평점:</span> {dummyMatch.aiReview.teamBDraftScore}점</div>
        </div>
        <p className="text-sm text-slate-300 leading-relaxed">
          {dummyMatch.aiReview.summary}
        </p>
      </div>
    </div>
  );
}

export default MatchCard;