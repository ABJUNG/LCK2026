import React, { useState, useEffect } from 'react';
import { db } from '../firebase'; // 아까 만든 설정 파일 불러오기
import { doc, getDoc } from 'firebase/firestore';

function MatchCard({ matchId }) {
  const [matchData, setMatchData] = useState(null);
  const [loading, setLoading] = useState(true);

  // 컴포넌트가 화면에 뜰 때 Firebase에서 데이터 가져오기
  useEffect(() => {
    const fetchMatchData = async () => {
      try {
        // 'matches' 컬렉션에서 '24SUM-T1-GEN-0812' 문서 가져오기
        const docRef = doc(db, 'matches', matchId);
        const docSnap = await getDoc(docRef);

        if (docSnap.exists()) {
          setMatchData(docSnap.data());
        } else {
          console.log("No such document!");
        }
      } catch (error) {
        console.error("Error fetching document:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchMatchData();
  }, [matchId]);

  // 데이터를 불러오는 중일 때 보여줄 로딩 화면
  if (loading) {
    return (
      <div className="bg-slate-800 rounded-xl p-8 border border-slate-700 flex justify-center items-center h-64 animate-pulse">
        <span className="text-amber-400 font-bold">🍚 식혜 밥알을 분석 중입니다...</span>
      </div>
    );
  }

  // 데이터가 없을 때
  if (!matchData) {
    return <div className="text-slate-400 p-4">경기 데이터를 찾을 수 없습니다.</div>;
  }

  // Firebase에서 가져온 진짜 데이터를 화면에 렌더링!
  return (
    <div className="bg-slate-800 rounded-xl p-5 border border-slate-700 hover:border-amber-400/50 transition-colors">
      <div className="flex justify-between items-center mb-4">
        <span className="text-slate-400 text-sm font-medium">{matchData.date}</span>
        <span className="bg-slate-900 text-amber-400 text-xs px-2 py-1 rounded-md border border-slate-700">
          Patch {matchData.aiReview?.patchVersion}
        </span>
      </div>

      <div className="flex items-center justify-center gap-6 mb-6">
        <div className="text-2xl font-black text-slate-100">{matchData.teamA}</div>
        <div className="flex items-center gap-3">
          <span className="text-3xl font-bold text-slate-300">{matchData.score?.teamA}</span>
          <span className="text-slate-500">vs</span>
          <span className="text-3xl font-bold text-slate-300">{matchData.score?.teamB}</span>
        </div>
        <div className="text-2xl font-black text-slate-100">{matchData.teamB}</div>
      </div>

      <div className="bg-slate-900/50 rounded-lg p-4">
        <h4 className="text-sm font-bold text-amber-400 mb-3 flex items-center gap-2">
          <span>🤖</span> AI 융합 분석 리포트
        </h4>
        <div className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
          {/* AI가 작성한 긴 텍스트를 그대로 예쁘게 출력합니다 */}
          {matchData.aiReview?.summary}
        </div>
      </div>
    </div>
  );
}

export default MatchCard;