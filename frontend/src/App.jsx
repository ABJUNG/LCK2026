import { ArrowDownRight, ArrowUpRight, Sparkles } from 'lucide-react';
import SourceFooter from './components/SourceFooter';
import MatchList from './components/MatchList';
import TeamDirectory from './components/TeamDirectory';

export default function App() {
  return <div className="site-shell min-h-screen font-sans text-zinc-100">
    <header className="site-header">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-5 sm:px-8">
        <a href="#main" className="brand-link flex items-center gap-3" aria-label="엘식혜 경기 기록으로 이동">
          <img src="/favicon.svg" width="43" height="43" className="brand-symbol" alt="" />
          <div><h1 className="text-lg font-black tracking-tight">L-SIKHYE<span className="brand-dot">.</span></h1><p className="mt-1 text-[10px] tracking-[.16em] text-zinc-400">엘식혜 · 경기 아카이브</p></div>
        </a>
        <nav aria-label="주요 메뉴" className="flex flex-wrap justify-end gap-2"><a href="#matches" className="archive-link">경기 아카이브 <ArrowUpRight size={15} aria-hidden="true" /></a><a href="#teams" className="archive-link">팀과 멤버</a></nav>
      </div>
    </header>
    <main id="main" className="mx-auto max-w-6xl px-4 pb-10 sm:px-8">
      <section className="hero-section" aria-labelledby="hero-title">
        <div className="hero-copy">
          <p className="eyebrow"><span className="season-dot" /> 2026 시즌 · LCK와 국제대회</p>
          <h2 id="hero-title">경기는 끝나도,<br /><span>이야기는 남는다.</span></h2>
          <p className="hero-description">밴픽부터 승부를 가른 순간까지.<br className="sm:hidden" /> 경기 기록과 AI 해석으로 다시 읽는 리그.</p>
          <a href="#matches" className="hero-cta">경기 살펴보기 <ArrowDownRight size={19} aria-hidden="true" /></a>
          <p className="mt-5 text-xs text-zinc-500">수집된 완료 경기만 제공하며, 실시간 중계가 아닙니다.</p>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="art-grid" /><div className="art-orbit orbit-one" /><div className="art-orbit orbit-two" />
          <span className="art-caption">밥알까지 세는 경기 분석</span>
          <img src="/favicon.svg" width="140" height="140" className="art-symbol" alt="" />
          <span className="art-sticker"><Sparkles size={15} /> 기록에 이야기를 더하다</span>
          <span className="art-coordinate">SEOUL, KR / 2026</span>
        </div>
      </section>
      <section id="matches" className="scroll-mt-6" aria-label="경기 아카이브"><MatchList /></section>
      <TeamDirectory />
      <SourceFooter />
    </main>
  </div>;
}
