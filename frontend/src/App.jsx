import React, { useState } from 'react';
import MatchCard from './components/MatchCard';
import { Home, BarChart2, BookOpen, Trophy, User, ChevronRight } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState('match');

  return (
    // 전체 배경을 완전한 다크 톤(zinc-950)으로 설정
    <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans flex">
      
      {/* 1. 좌측 사이드바 (Left Navigation) */}
      <aside className="w-64 border-r border-zinc-800/60 bg-zinc-950 flex flex-col hidden md:flex sticky top-0 h-screen">
        <div className="p-6">
          <div className="flex items-center gap-3 cursor-pointer mb-10" onClick={() => setActiveTab('match')}>
            <span className="text-3xl">🍚</span>
            <div>
              <h1 className="font-extrabold text-2xl tracking-wider text-amber-500">
                L-Sikhye
              </h1>
              <p className="text-[10px] text-zinc-500 tracking-widest mt-1 uppercase">LCK Data Analytics</p>
            </div>
          </div>

          <nav className="flex flex-col gap-2">
            <p className="text-xs font-bold text-zinc-500 mb-2 px-3">메뉴</p>
            
            <button onClick={() => setActiveTab('match')}
              className={`flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'match' ? 'bg-zinc-800/50 text-amber-500 border-l-2 border-amber-500' : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
              }`}>
              <Home size={18} />
              밥알 파헤치기
            </button>
            
            <button onClick={() => setActiveTab('meta')}
              className={`flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'meta' ? 'bg-zinc-800/50 text-amber-500 border-l-2 border-amber-500' : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
              }`}>
              <BarChart2 size={18} />
              메타 양조장
            </button>

            <button onClick={() => setActiveTab('wiki')}
              className={`flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'wiki' ? 'bg-zinc-800/50 text-amber-500 border-l-2 border-amber-500' : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
              }`}>
              <BookOpen size={18} />
              LCK 도감
            </button>

            <button onClick={() => setActiveTab('predict')}
              className={`flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'predict' ? 'bg-zinc-800/50 text-amber-500 border-l-2 border-amber-500' : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
              }`}>
              <Trophy size={18} />
              승부 예측
            </button>
          </nav>
        </div>
        
        {/* 하단 유저 프로필 영역 */}
        <div className="mt-auto p-6 border-t border-zinc-800/60">
          <div className="flex items-center gap-3 bg-zinc-900 p-3 rounded-xl cursor-pointer hover:bg-zinc-800 transition">
            <div className="bg-zinc-800 p-2 rounded-full"><User size={16} className="text-zinc-400"/></div>
            <div>
              <p className="text-sm font-bold text-zinc-200">로그인 필요</p>
              <p className="text-xs text-amber-500 font-medium">포인트 획득하기</p>
            </div>
          </div>
        </div>
      </aside>

      {/* 2. 중앙 메인 컨텐츠 영역 */}
      <main className="flex-1 min-h-screen">
        <div className="max-w-4xl mx-auto p-8">
          
          {/* 상단 날짜 및 필터 헤더 (사진 참고) */}
          <div className="flex items-center justify-between mb-8 pb-4 border-b border-zinc-800">
            <div>
              <p className="text-sm text-zinc-400 font-medium mb-1">수요일</p>
              <h2 className="text-3xl font-extrabold text-white tracking-tight">8월 12일</h2>
            </div>
            <div className="flex items-center bg-zinc-900 rounded-lg p-1 border border-zinc-800">
              <button className="px-4 py-2 text-sm text-zinc-400 hover:text-white transition">이전</button>
              <div className="w-px h-4 bg-zinc-800 mx-1"></div>
              <button className="px-4 py-2 text-sm text-white font-bold bg-zinc-800 rounded-md">오늘</button>
              <div className="w-px h-4 bg-zinc-800 mx-1"></div>
              <button className="px-4 py-2 text-sm text-zinc-400 hover:text-white transition">다음</button>
            </div>
          </div>

          {/* 탭별 내용 변경 */}
          {activeTab === 'match' && (
            <div className="space-y-6 animate-fade-in">
              <h3 className="text-xl font-bold text-white mb-4">오늘 예정된 경기 (AI 분석 리포트)</h3>
              <MatchCard />
              <MatchCard />
            </div>
          )}
          {activeTab === 'meta' && (
            <div className="p-8 bg-zinc-900/50 rounded-2xl border border-zinc-800/50">
              <h2 className="text-2xl font-bold text-amber-500 mb-2">🧪 메타 양조장</h2>
              <p className="text-zinc-400">최신 패치노트와 메타 트렌드를 분석하는 공간입니다.</p>
            </div>
          )}
        </div>
      </main>

      {/* 3. 우측 정보 사이드바 (Global Power Rankings & News 영역) */}
      <aside className="w-80 border-l border-zinc-800/60 bg-zinc-950/50 hidden xl:block p-8">
        
        {/* 파워 랭킹 섹션 */}
        <div className="mb-10">
          <h3 className="text-sm font-bold text-white mb-4 flex items-center justify-between">
            팀 파워 랭킹
            <span className="text-[10px] text-zinc-500 font-normal">Powered by AI</span>
          </h3>
          <div className="space-y-4">
            <div className="flex items-center gap-4 pb-4 border-b border-zinc-800/50">
              <span className="text-xl font-black text-amber-500 w-4">1</span>
              <span className="font-bold text-zinc-200">GEN</span>
            </div>
            <div className="flex items-center gap-4 pb-4 border-b border-zinc-800/50">
              <span className="text-xl font-black text-zinc-400 w-4">2</span>
              <span className="font-bold text-zinc-200">HLE</span>
            </div>
            <div className="flex items-center gap-4 pb-4 border-b border-zinc-800/50">
              <span className="text-xl font-black text-zinc-400 w-4">3</span>
              <span className="font-bold text-zinc-200">T1</span>
            </div>
          </div>
          <button className="mt-4 flex items-center justify-between w-full text-sm text-cyan-500 hover:text-cyan-400 transition font-medium">
            전체 순위 보기
            <ChevronRight size={16} />
          </button>
        </div>

        {/* L-Sikhye 소식 섹션 */}
        <div>
          <h3 className="text-sm font-bold text-white mb-4">AI 메타 리포트</h3>
          <div className="space-y-4">
            <div className="group cursor-pointer">
              <div className="aspect-video bg-zinc-800 rounded-lg mb-2 overflow-hidden flex items-center justify-center">
                <span className="text-zinc-600 text-xs">Thumbnail</span>
              </div>
              <p className="text-sm font-bold text-zinc-200 group-hover:text-amber-500 transition line-clamp-2">14.12 패치 분석: 밸류 픽의 귀환과 바텀 메타의 변화</p>
              <p className="text-xs text-zinc-500 mt-1">2026년 8월 12일</p>
            </div>
          </div>
        </div>

      </aside>
    </div>
  );
}

export default App;