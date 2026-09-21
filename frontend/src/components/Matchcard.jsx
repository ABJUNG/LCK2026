import { useState } from 'react';
import { getChampionImageUrl, getRoleNameKr } from '../utils/riot';

function MatchCard({ seriesData }) {
  // 현재 선택된 탭을 관리 (0 = 1세트, 1 = 2세트...)
  const [activeTabIndex, setActiveTabIndex] = useState(0);

  if (!seriesData || !seriesData.sets || seriesData.sets.length === 0) return null;

  // 현재 탭에 해당하는 세트 데이터
  const currentSet = seriesData.sets[activeTabIndex];
  
  // 최종 매치 스코어 (가장 마지막 세트에 기록된 스코어 기준)
  const finalScoreA = seriesData.sets[seriesData.sets.length - 1].score?.teamA ?? 0;
  const finalScoreB = seriesData.sets[seriesData.sets.length - 1].score?.teamB ?? 0;

  const renderBans = (bans, isRight = false) => (
    <div className={`flex items-center gap-1 my-2 ${isRight ? 'justify-end' : 'justify-start'}`}>
      <span className="text-[10px] text-red-400 font-bold mr-1">BAN</span>
      {bans?.map((champ, idx) => (
        <div key={idx} className="relative group">
          {champ ? (
            <img src={getChampionImageUrl(champ)} alt={champ} className="w-6 h-6 rounded-full border border-red-500/60 grayscale object-cover" />
          ) : (
            <div className="w-6 h-6 rounded-full bg-slate-800 border border-slate-700" />
          )}
        </div>
      ))}
    </div>
  );

  const renderPlayerMatchups = (setMatchData) => {
    const teamAPlayers = setMatchData.players?.teamA || [];
    const teamBPlayers = setMatchData.players?.teamB || [];
    const allPlayers = [...teamAPlayers, ...teamBPlayers];
    const maxDamage = Math.max(...allPlayers.map(p => p.damage || 0), 1);

    return (
      <div className="bg-slate-900/90 rounded-lg p-3 border border-slate-700/80 mb-5">
        <div className="grid grid-cols-12 text-[11px] font-bold text-slate-400 border-b border-slate-800 pb-2 mb-2 px-1 text-center">
          <div className="col-span-5 text-left">{seriesData.teamA} 라인업</div>
          <div className="col-span-2">포지션</div>
          <div className="col-span-5 text-right">{seriesData.teamB} 라인업</div>
        </div>

        {teamAPlayers.map((playerA, idx) => {
          const playerB = teamBPlayers[idx] || {};
          return (
            <div key={idx} className="grid grid-cols-12 items-center py-1.5 border-b border-slate-800/40 last:border-0 hover:bg-slate-800/40 px-1 rounded transition-colors">
              {/* Team A */}
              <div className="col-span-5 flex items-center justify-between pr-2">
                <div className="flex items-center gap-2">
                  <img src={getChampionImageUrl(playerA.champion)} alt={playerA.champion} className="w-8 h-8 rounded-full border-2 border-blue-400/80 object-cover" />
                  <div className="flex flex-col min-w-0">
                    <span className="text-xs font-bold text-slate-100 truncate">{playerA.name}</span>
                    <span className="text-[10px] text-slate-400">{playerA.kills}/{playerA.deaths}/{playerA.assists}</span>
                  </div>
                </div>
                <div className="flex flex-col w-16 md:w-20 items-end">
                  <span className="text-[9px] text-slate-400">{playerA.damage?.toLocaleString() || 0}</span>
                  <div className="w-full bg-slate-700 h-1.5 rounded-full mt-0.5 overflow-hidden flex justify-end">
                    <div className="bg-red-500 h-full rounded-full" style={{ width: `${((playerA.damage || 0) / maxDamage) * 100}%` }}></div>
                  </div>
                </div>
              </div>
              {/* Position */}
              <div className="col-span-2 text-center">
                <span className="bg-slate-800 text-amber-400 text-[10px] font-bold px-2 py-0.5 rounded border border-slate-700">
                  {getRoleNameKr(playerA.role || playerB.role)}
                </span>
              </div>
              {/* Team B */}
              <div className="col-span-5 flex items-center justify-between pl-2">
                <div className="flex flex-col w-16 md:w-20 items-start">
                  <span className="text-[9px] text-slate-400">{playerB.damage?.toLocaleString() || 0}</span>
                  <div className="w-full bg-slate-700 h-1.5 rounded-full mt-0.5 overflow-hidden">
                    <div className="bg-red-500 h-full rounded-full" style={{ width: `${((playerB.damage || 0) / maxDamage) * 100}%` }}></div>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-right">
                  <div className="flex flex-col min-w-0">
                    <span className="text-xs font-bold text-slate-100 truncate">{playerB.name}</span>
                    <span className="text-[10px] text-slate-400">{playerB.kills}/{playerB.deaths}/{playerB.assists}</span>
                  </div>
                  <img src={getChampionImageUrl(playerB.champion)} alt={playerB.champion} className="w-8 h-8 rounded-full border-2 border-red-400/80 object-cover" />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="bg-slate-800 rounded-xl p-5 border border-slate-700 shadow-2xl hover:border-amber-400/30 transition-all">
      {/* 1. 상단 정보 (매치 기준) */}
      <div className="flex justify-between items-center mb-5 pb-3 border-b border-slate-700/60">
        <div className="flex items-center gap-2">
          <span className="bg-amber-400/10 text-amber-400 text-xs font-bold px-2.5 py-1 rounded-md border border-amber-400/20">
            {seriesData.week || 'LCK'}
          </span>
          <span className="text-slate-300 text-xs font-medium">
            {seriesData.dateKST} {seriesData.timeKST} KST
          </span>
        </div>
      </div>

      {/* 2. 매치 스코어 보드 (팀 로고 및 최종 스코어) */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex flex-col items-center flex-1">
          <img src={`/teams/${seriesData.teamA}.png`} alt={seriesData.teamA} className="w-14 h-14 object-contain mb-1 drop-shadow-md" onError={(e) => { e.target.src = 'https://via.placeholder.com/56?text=TEAM'; }} />
          <span className="text-lg font-black text-slate-100">{seriesData.teamA}</span>
          {renderBans(currentSet?.bans?.teamA, false)}
        </div>

        <div className="flex flex-col items-center px-4">
          <span className="text-xs font-bold text-slate-400 mb-2">매치 스코어</span>
          <div className="flex items-center gap-4 bg-slate-900/90 px-5 py-2.5 rounded-lg border border-slate-700 shadow-inner">
            <span className="text-3xl font-black text-white">{finalScoreA}</span>
            <span className="text-slate-500 font-bold text-lg">:</span>
            <span className="text-3xl font-black text-white">{finalScoreB}</span>
          </div>
        </div>

        <div className="flex flex-col items-center flex-1">
          <img src={`/teams/${seriesData.teamB}.png`} alt={seriesData.teamB} className="w-14 h-14 object-contain mb-1 drop-shadow-md" onError={(e) => { e.target.src = 'https://via.placeholder.com/56?text=TEAM'; }} />
          <span className="text-lg font-black text-slate-100">{seriesData.teamB}</span>
          {renderBans(currentSet?.bans?.teamB, true)}
        </div>
      </div>

      {/* 💡 3. 세트 전환 탭 (1세트, 2세트, 3세트, 총평) */}
      <div className="flex gap-2 mb-4 border-b border-slate-700/60 pb-3">
        {seriesData.sets.map((set, index) => (
          <button
            key={index}
            onClick={() => setActiveTabIndex(index)}
            className={`px-4 py-1.5 text-xs font-bold rounded-full transition-all ${
              activeTabIndex === index 
              ? 'bg-amber-400 text-slate-900 shadow-md' 
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            {set.setNumber}세트
          </button>
        ))}
        {/* 총평 탭 (미래 확장용 UI) */}
        <button className="px-4 py-1.5 text-xs font-bold rounded-full bg-slate-800 border border-slate-600 text-slate-400 opacity-50 cursor-not-allowed" title="곧 추가될 예정입니다.">
          총평 (예정)
        </button>
      </div>

      {/* 4. 선택된 세트의 상세 정보 */}
      {currentSet && (
        <div className="animate-fade-in">
          {/* 패치 버전 및 현재 세트 스코어 */}
          <div className="flex justify-between items-center mb-3">
            <span className="text-amber-400 font-bold text-sm">{currentSet.setNumber}세트 상세 스탯</span>
            <span className="text-slate-400 text-xs font-semibold bg-slate-900 px-2 py-1 rounded-md">
              Patch {currentSet.aiReview?.patchVersion || '26.1'}
            </span>
          </div>

          {/* 선수 10명 스탯 및 딜량 그래프 표 */}
          {renderPlayerMatchups(currentSet)}

          {/* AI 리포트 */}
          <div className="bg-slate-900/60 rounded-lg p-4 border border-slate-700/60">
            <h4 className="text-sm font-bold text-amber-400 mb-2 flex items-center gap-1.5">
              <span>🤖</span> AI {currentSet.setNumber}세트 분석 리포트
            </h4>
            <div className="text-xs md:text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
              {currentSet.aiReview?.summary}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default MatchCard;