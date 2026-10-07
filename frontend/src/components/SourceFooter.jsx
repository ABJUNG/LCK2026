export default function SourceFooter() {
  return <footer className="source-footer mt-12 text-xs leading-6 text-zinc-400">
    <div className="footer-intro">
      <div className="flex items-center gap-3"><img src="/favicon.svg" alt="" width="32" height="32" /><div><h2 className="font-bold text-zinc-200">엘식혜 · L-SIKHYE</h2><p>밥알까지 세는 경기 분석</p></div></div>
      <a href="#main" className="footer-top-link">맨 위로 ↑</a>
    </div>
    <nav aria-label="데이터와 이미지 출처" className="source-links">
      <a href="https://lol.fandom.com/wiki/League_of_Legends_Esports_Wiki"><span>경기 기록</span>Leaguepedia 및 기여자 ↗</a>
      <a href="https://developer.riotgames.com/docs/lol/#data-dragon"><span>게임 이미지 · 한글 자료</span>Riot Games Data Dragon ↗</a>
      <a href="https://www.communitydragon.org/"><span>오브젝트 · 능력치 파편</span>CommunityDragon ↗</a>
      <a href="https://lucide.dev/license"><span>화면 아이콘</span>Lucide ↗</a>
    </nav>
    <p className="footer-disclaimer">비공식 팬 프로젝트입니다. Riot Games의 보증·후원 또는 공식 견해를 나타내지 않습니다. AI 분석은 원본 데이터 제공자의 공식 평가가 아닙니다.</p>
    <details className="source-details"><summary>출처 · 저작권 · 가공 방식 자세히 보기</summary><div className="space-y-3 pt-3">
    <p>경기 데이터: <a className="underline" href="https://lol.fandom.com/wiki/League_of_Legends_Esports_Wiki">Leaguepedia 및 기여자</a>의 Cargo 경기 기록·V5 경기 JSON을 수집·정리했습니다. 원본 문서의 별도 표기가 없는 위키 콘텐츠는 <a className="underline" href="https://creativecommons.org/licenses/by-sa/3.0/">CC BY-SA 3.0</a>에 따릅니다. Leaguepedia 위키 텍스트 기반 가공 콘텐츠에도 동일 조건이 적용되며, 게임 이미지와 제3자 상표는 별도 권리를 따릅니다.</p>
    <p>챔피언 초상화·아이템·룬·스펠 이미지와 한글 이름: <a className="underline" href="https://developer.riotgames.com/docs/lol/#data-dragon">Riot Games Data Dragon</a>. 오브젝트 이미지·능력치 파편 자료: Riot Games 게임 에셋, <a className="underline" href="https://www.communitydragon.org/">CommunityDragon</a> 제공. 원본 이미지의 비율을 유지하여 축소 표시했습니다. <a className="underline" href="/objectives/sources.json">아이콘별 원본 주소</a>.</p>
    <p>UI 기호: <a className="underline" href="https://lucide.dev/license">Lucide · ISC 라이선스</a>. 팀 로고·명칭의 권리는 각 권리자에게 있습니다. 기존 팀 로고 파일의 개별 취득 출처는 확인 중입니다.</p>
    <p className="mt-2">엘식혜는 비공식 팬 프로젝트로, Riot Games의 보증·후원 또는 공식 견해를 나타내지 않습니다. League of Legends, Riot Games 및 관련 자산·상표의 권리는 Riot Games, Inc.에 있습니다. <a className="underline" href="https://www.riotgames.com/en/legal">Riot Games 이용 정책</a> · <a className="underline" href="https://developer.riotgames.com/policies/general">개발자 정책</a></p>
    <p>AI 분석은 엘식혜에서 생성한 해석이며 원본 데이터 제공자의 공식 평가가 아닙니다. 데이터 출처와 AI 해석을 구분해 이용해 주세요.</p>
  <p>나무위키 관전평은 해당 경기의 분석 하단에 문서 링크·기여자·사용자 제공일을 따로 표시합니다. 제공된 텍스트를 요약·재구성한 자료와 이를 반영한 해석에는 CC BY-NC-SA 2.0 KR 조건을 표시하며, Leaguepedia 자료와 출처를 구분합니다.</p>
    </div></details>
  </footer>;
}
