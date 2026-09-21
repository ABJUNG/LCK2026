import { useState, useEffect } from 'react';
import { db } from '../firebase';
import { collection, getDocs } from 'firebase/firestore';
import MatchCard from './Matchcard.jsx';

function MatchList() {
  const [groupedMatches, setGroupedMatches] = useState([]);
  const [loading, setLoading] = useState(true);

  const [error, setError] = useState(null);
  const [requestId, setRequestId] = useState(0);

  useEffect(() => {
    // 이전 요청의 응답이 현재 화면의 상태를 덮어쓰지 않도록 합니다.
    let cancelled = false;
    const fetchAllMatches = async () => {
      try {
        const matchesRef = collection(db, 'matches');
        const querySnapshot = await getDocs(matchesRef);

        const matchArray = [];
        querySnapshot.forEach((doc) => {
          matchArray.push({ id: doc.id, ...doc.data() });
        });

        // 💡 1. 시리즈(매치) 단위로 데이터 그룹화
        const groups = {};
        matchArray.forEach(match => {
          // 고유 키 생성 (예: "2026-08-16_Gen.G_T1")
          const seriesKey = `${match.dateKST}_${match.teamA}_${match.teamB}`;
          
          if (!groups[seriesKey]) {
            groups[seriesKey] = {
              seriesKey,
              dateKST: match.dateKST,
              timeKST: match.timeKST,
              teamA: match.teamA,
              teamB: match.teamB,
              tournament: match.tournament,
              week: match.week,
              sets: [] // 세트 데이터들이 담길 배열
            };
          }
          groups[seriesKey].sets.push(match);
        });

        // 💡 2. 각 시리즈 내에서 1세트 -> 2세트 순서로 정렬
        Object.values(groups).forEach(group => {
          group.sets.sort((a, b) => parseInt(a.setNumber) - parseInt(b.setNumber));
        });

        // 💡 3. 전체 시리즈를 최신 날짜순으로 정렬
        const sortedGroups = Object.values(groups).sort((a, b) => {
          const timeA = new Date(`${a.dateKST}T${a.timeKST}`);
          const timeB = new Date(`${b.dateKST}T${b.timeKST}`);
          return timeB - timeA;
        });

        if (!cancelled) setGroupedMatches(sortedGroups);
      } catch (error) {
        console.error("Firestore 경기 목록 로딩 실패:", error);
        if (!cancelled) setError("경기 목록을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchAllMatches();
    return () => { cancelled = true; };
  }, [requestId]);

  const retry = () => {
    setLoading(true);
    setError(null);
    setRequestId(previous => previous + 1);
  };

  if (loading) {
    return (
      <div role="status" className="flex flex-col items-center justify-center p-12 bg-slate-800/50 rounded-xl border border-slate-700">
        <div className="w-8 h-8 border-4 border-amber-400 border-t-transparent rounded-full animate-spin mb-3"></div>
        <p className="text-amber-400 font-bold text-sm">🍚 경기 데이터를 묶어서 불러오는 중입니다...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div role="alert" className="p-8 text-center bg-slate-800/40 rounded-xl border border-red-400/40">
        <p className="text-slate-200">{error}</p>
        <button type="button" onClick={retry}
          className="mt-4 rounded-lg bg-amber-400 px-4 py-2 font-bold text-slate-950 hover:bg-amber-300 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-amber-400">
          다시 시도
        </button>
      </div>
    );
  }

  if (groupedMatches.length === 0) {
    return (
      <div className="p-8 text-center bg-slate-800/40 rounded-xl border border-slate-700/60">
        <p className="text-slate-400">저장된 경기 데이터가 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <span>🔥</span> 최근 분석된 LCK 매치 ({groupedMatches.length}경기)
        </h3>
      </div>

      <div className="grid grid-cols-1 gap-8">
        {groupedMatches.map((series) => (
          <MatchCard key={series.seriesKey} seriesData={series} />
        ))}
      </div>
    </div>
  );
}

export default MatchList;