import React from 'react';
import { getChampionImageUrl, getRoleNameKr } from '../utils/riot';

function MatchCard({ matchData }) {
  if (!matchData) return null;

  // 밴 챔피언 목록 렌더링
  const renderBans = (bans, isRight = false) => (
    <div className={`flex items-center gap-1 my-2 ${isRight ? 'justify-end' : 'justify-start'}`}>
      <span className="text-[10px] text-red-400 font-bold mr-1">BAN</span>
      {bans?.map((champ, idx) => (
        <div key={idx} className="relative group">
          {champ ? (
            <img
              src={getChampionImageUrl(champ)}
              alt={champ}
              className="w-6 h-6 rounded-full border border-red-500/60 grayscale object-cover"
              title={`Ban: ${champ}`}
            />
          ) : (
            <div className="w-6 h-6 rounded-full bg-slate-800 border border-slate-700" />
          )}
        </div>
      ))}
    </div>
  );

  // 10명 선수 1v1 라이너 대결 표 렌더링
  const renderPlayerMatchups = () => {
    const teamAPlayers = matchData.players?.teamA || [];
    const teamBPlayers = matchData.players?.teamB || [];

    // 💡 1. 10명 중 최대 딜량을 구하는 로직 (이 위치에 들어갑니다!)
    const allPlayers = [...teamAPlayers, ...teamBPlayers];
    const maxDamage = Math.max(...allPlayers.map(p => p.damage || 0), 1); // 1은 0으로 나누기 방지용

    return (
      <div className="bg-slate-900/90 rounded-lg p-3 border border-slate-700/80 mb-5">
        <div className="grid grid-cols-12 text-[11px] font-bold text-slate-400 border-b border-slate-800 pb-2 mb-2 px-1 text-center">
          <div className="col-span-5 text-left">{matchData.teamA} 라인업</div>
          <div className="col-span-2">포지션</div>
          <div className="col-span-5 text-right">{matchData.teamB} 라인업</div>
        </div>

        {teamAPlayers.map((playerA, idx) => {
          const playerB = teamBPlayers[idx] || {};
          return (
            <div key={idx} className="grid grid-cols-12 items-center py-1.5 border-b border-slate-800/40 last:border-0 hover:bg-slate-800/40 px-1 rounded transition-colors">
              
              {/* Team A 선수 영역 */}
              <div className="col-span-5 flex items-center justify-between pr-2">
                <div className="flex items-center gap-2">
                  <img
                    src={getChampionImageUrl(playerA.champion)}
                    alt={playerA.champion}
                    className="w-8 h-8 rounded-full border-2 border-blue-400/80 object-cover shadow-sm"
                    title={playerA.champion}
                  />
                  <div className="flex flex-col min-w-0">
                    <span className="text-xs font-bold text-slate-100 truncate">{playerA.name}</span>
                    <span className="text-[10px] text-slate-400">
                      {playerA.kills}/{playerA.deaths}/{playerA.assists}
                    </span>
                  </div>
                </div>
                
                {/* 💡 2. Team A 딜량 바 그래프 (우측 정렬) */}
                <div className="flex flex-col w-16 md:w-20 items-end">
                  <span className="text-[9px] text-slate-400">{playerA.damage?.toLocaleString() || 0}</span>
                  <div className="w-full bg-slate-700 h-1.5 rounded-full mt-0.5 overflow-hidden flex justify-end">
                    <div 
                      className="bg-red-500 h-full rounded-full" 
                      style={{ width: `${((playerA.damage || 0) / maxDamage) * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>

              {/* 포지션 라벨 */}
              <div className="col-span-2 text-center">
                <span className="bg-slate-800 text-amber-400 text-[10px] font-bold px-2 py-0.5 rounded border border-slate-700">
                  {getRoleNameKr(playerA.role || playerB.role)}
                </span>
              </div>

              {/* Team B 선수 영역 */}
              <div className="col-span-5 flex items-center justify-between pl-2">
                
                {/* 💡 3. Team B 딜량 바 그래프 (좌측 정렬) */}
                <div className="flex flex-col w-16 md:w-20 items-start">
                  <span className="text-[9px] text-slate-400">{playerB.damage?.toLocaleString() || 0}</span>
                  <div className="w-full bg-slate-700 h-1.5 rounded-full mt-0.5 overflow-hidden">
                    <div 
                      className="bg-red-500 h-full rounded-full" 
                      style={{ width: `${((playerB.damage || 0) / maxDamage) * 100}%` }}
                    ></div>
                  </div>
                </div>

                <div className="flex items-center gap-2 text-right">
                  <div className="flex flex-col min-w-0">
                    <span className="text-xs font-bold text-slate-100 truncate">{playerB.name}</span>
                    <span className="text-[10px] text-slate-400">
                      {playerB.kills}/{playerB.deaths}/{playerB.assists}
                    </span>
                  </div>
                  <img
                    src={getChampionImageUrl(playerB.champion)}
                    alt={playerB.champion}
                    className="w-8 h-8 rounded-full border-2 border-red-400/80 object-cover shadow-sm"
                    title={playerB.champion}
                  />
                </div>
              </div>

            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="bg-slate-800 rounded-xl p-5 border border-slate-700 shadow-2xl hover:border-amber-400/40 transition-all">
      {/* 상단 타이틀 */}
      <div className="flex justify-between items-center mb-4 pb-3 border-b border-slate-700/60">
        <div className="flex items-center gap-2">
          <span className="bg-amber-400/10 text-amber-400 text-xs font-bold px-2.5 py-1 rounded-md border border-amber-400/20">
            {matchData.week || 'LCK'}
          </span>
          <span className="text-slate-300 text-xs font-medium">
            {matchData.dateKST} {matchData.timeKST} KST
          </span>
        </div>
        <span className="text-slate-400 text-xs font-semibold bg-slate-900 px-2.5 py-1 rounded-md">
          Patch {matchData.aiReview?.patchVersion || '26.1'}
        </span>
      </div>

      {/* 매치 스코어 대진 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex flex-col items-center flex-1">
          <img
            src={`/teams/${matchData.teamA}.png`}
            alt={matchData.teamA}
            className="w-12 h-12 md:w-14 md:h-14 object-contain mb-1 drop-shadow-md"
            onError={(e) => { e.target.src = 'https://via.placeholder.com/56?text=TEAM'; }}
          />
          <span className="text-base md:text-lg font-black text-slate-100">{matchData.teamA}</span>
          {renderBans(matchData.bans?.teamA, false)}
        </div>

        <div className="flex flex-col items-center px-2">
          <span className="text-xs font-bold text-amber-400 mb-1">
            {matchData.setNumber ? `${matchData.setNumber}세트` : 'Match'}
          </span>
          <div className="flex items-center gap-3 bg-slate-900/90 px-4 py-2 rounded-lg border border-slate-700">
            <span className="text-2xl font-black text-white">{matchData.score?.teamA ?? 0}</span>
            <span className="text-slate-500 font-bold text-sm">:</span>
            <span className="text-2xl font-black text-white">{matchData.score?.teamB ?? 0}</span>
          </div>
        </div>

        <div className="flex flex-col items-center flex-1">
          <img
            src={`/teams/${matchData.teamB}.png`}
            alt={matchData.teamB}
            className="w-12 h-12 md:w-14 md:h-14 object-contain mb-1 drop-shadow-md"
            onError={(e) => { e.target.src = 'https://via.placeholder.com/56?text=TEAM'; }}
          />
          <span className="text-base md:text-lg font-black text-slate-100">{matchData.teamB}</span>
          {renderBans(matchData.bans?.teamB, true)}
        </div>
      </div>

      {/* 10명 라이너 Matchup 스코어보드 */}
      {renderPlayerMatchups()}

      {/* AI 리포트 */}
      <div className="bg-slate-900/60 rounded-lg p-4 border border-slate-700/60">
        <h4 className="text-sm font-bold text-amber-400 mb-2 flex items-center gap-1.5">
          <span>🤖</span> AI 밴픽 분석 리포트
        </h4>
        <div className="text-xs md:text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
          {matchData.aiReview?.summary}
        </div>
      </div>
    </div>
  );
}

export default MatchCard;