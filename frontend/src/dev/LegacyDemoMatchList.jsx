import { useState, useEffect } from 'react';
import { db } from '../firebase';
import { collection, getDocs } from 'firebase/firestore';
import MatchCard from '../components/Matchcard.jsx';
import { groupMatches } from '../utils/groupMatches';

const demoMode = import.meta.env.DEV
  ? new URLSearchParams(window.location.search).get('demo')
  : null;

function MatchList() {
  const [groupedMatches, setGroupedMatches] = useState([]);
  const [selectedDate, setSelectedDate] = useState('');
  const [loading, setLoading] = useState(true);

  const [error, setError] = useState(null);
  const [requestId, setRequestId] = useState(0);

  useEffect(() => {
    // 이전 요청의 응답이 현재 화면의 상태를 덮어쓰지 않도록 합니다.
    let cancelled = false;
    const fetchAllMatches = async () => {
      try {
        let matchArray;
        if (demoMode) {
          const { loadDemoMatches } = await import('../dev/demoMatches');
          matchArray = await loadDemoMatches(demoMode, requestId);
        } else {
          const querySnapshot = await getDocs(collection(db, 'matches'));
          matchArray = querySnapshot.docs.map(doc => ({ ...doc.data(), id: doc.id }));
        }
        const sortedGroups = groupMatches(matchArray);

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

  const demoNotice = demoMode && (
    <p className="mb-4 rounded-lg border border-amber-400 p-3 text-sm text-amber-300">
      개발 확인용 예제 데이터입니다. 실제 경기 결과가 아닙니다. ({demoMode})
    </p>
  );

  if (loading) {
    return (
      <div role="status" className="flex flex-col items-center justify-center p-12 bg-slate-800/50 rounded-xl border border-slate-700">
        {demoNotice}
        <div className="w-8 h-8 border-4 border-amber-400 border-t-transparent rounded-full animate-spin mb-3"></div>
        <p className="text-amber-400 font-bold text-sm">🍚 경기 데이터를 묶어서 불러오는 중입니다...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div role="alert" className="p-8 text-center bg-slate-800/40 rounded-xl border border-red-400/40">
        {demoNotice}
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
        {demoNotice}
        <p className="text-slate-400">저장된 경기 데이터가 없습니다.</p><button onClick={retry} className="mt-4 text-amber-400">목록 새로고침</button>
      </div>
    );
  }

  const hasSource = groupedMatches.some(series => series.sets.some(set => set.sourceGameId));
  const visibleGroups = groupedMatches.filter(series => !hasSource || series.sets.every(set => set.sourceGameId));
  const dates = [...new Set(visibleGroups.map(series => series.dateKST))].sort().reverse();
  const filtered = visibleGroups.filter(series => !selectedDate || series.dateKST === selectedDate);

  return (
    <div className="space-y-6 animate-fade-in">
      {demoNotice}
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <span>📅</span> 경기 기록 ({filtered.length}경기)
        </h3>
      </div>

      <div className="flex flex-wrap items-center gap-3 text-sm text-slate-300">
        <label>경기 날짜 (KST)
          <select className="ml-2 rounded bg-slate-800 p-2" value={selectedDate} onChange={event => setSelectedDate(event.target.value)}>
            <option value="">전체 날짜</option>
            {dates.map(date => <option key={date} value={date}>{date}</option>)}
          </select>
        </label>
        <button onClick={retry} className="rounded bg-amber-400 px-3 py-2 font-bold text-slate-950">목록 새로고침</button>
      </div>
      {filtered.length === 0 && <p className="text-slate-400">선택한 날짜의 수집 데이터가 없습니다.</p>}
      <div className="grid grid-cols-1 gap-8">
        {filtered.map((series) => (
          <MatchCard key={series.seriesKey} seriesData={series} />
        ))}
      </div>
    </div>
  );
}

export default MatchList;