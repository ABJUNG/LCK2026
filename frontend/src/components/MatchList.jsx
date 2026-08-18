import React, { useState, useEffect } from 'react';
import { db } from '../firebase';
import { collection, getDocs, query, orderBy } from 'firebase/firestore';
import MatchCard from './MatchCard';

function MatchList() {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAllMatches = async () => {
      try {
        // Firestore의 'matches' 컬렉션에서 전체 경기 데이터 가져오기
        const matchesRef = collection(db, 'matches');
        const querySnapshot = await getDocs(matchesRef);

        const matchArray = [];
        querySnapshot.forEach((doc) => {
          matchArray.push({
            id: doc.id,
            ...doc.data()
          });
        });

        // 최신 날짜/세트 순으로 정렬 (필요시)
        setMatches(matchArray);
      } catch (error) {
        console.error("Firestore 경기 목록 로딩 실패:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchAllMatches();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-slate-800/50 rounded-xl border border-slate-700">
        <div className="w-8 h-8 border-4 border-amber-400 border-t-transparent rounded-full animate-spin mb-3"></div>
        <p className="text-amber-400 font-bold text-sm">🍚 Firebase에서 LCK 경기 데이터를 가져오는 중입니다...</p>
      </div>
    );
  }

  if (matches.length === 0) {
    return (
      <div className="p-8 text-center bg-slate-800/40 rounded-xl border border-slate-700/60">
        <p className="text-slate-400">저장된 경기 데이터가 없습니다.</p>
        <p className="text-xs text-slate-500 mt-1">Python 파이프라인(analyzer.py)을 실행해 데이터를 추가해 보세요!</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <span>🔥</span> 최근 분석된 LCK 경기 목록 ({matches.length}개)
        </h3>
      </div>

      {/* 수집된 모든 경기를 카드로 출력 */}
      <div className="grid grid-cols-1 gap-6">
        {matches.map((match) => (
          <MatchCard key={match.id} matchData={match} />
        ))}
      </div>
    </div>
  );
}

export default MatchList;