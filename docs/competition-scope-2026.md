# 지원 대회와 우선 수집 · 2026-10-07

지원 범위: 한국 LCK 1군 대회와 한국 팀이 참가하는 Riot 주요 국제대회. 해외 지역 리그·아카데미·이벤트 쇼매치는 제외한다. 국제대회에서는 대회 흐름을 확인할 수 있도록 해외 팀끼리의 경기도 포함한다.

분류: LCK 정규시즌, LCK 포스트시즌(플레이인/플레이오프/결승), LCK Cup, LCK Road to MSI, First Stand, MSI, Worlds. 시즌은 현재 2026만 등록한다. MSI 등은 분류만 등록하며 이번에 과거 경기를 수집하지 않는다.

Leaguepedia Tournaments에서 확인한 정확한 Name을 config/competitions.json에 등록했다. Worlds 2026, Worlds 2026 Main Event, Worlds 2026 Play-In은 월즈로 분류하고 Esports World Cup/World Star Challengers를 이름 유사성으로 혼합하지 않는다. Finals 단계는 원본 시리즈 ID에 Finals가 명시된 경우만 설정한다.

이번 우선 수집은 LCK 2026 Season Play-In 14세트와 LCK 2026 Season Playoffs 41세트. 기존 2경기 5세트는 보존한다. 월즈는 2026-10-07 기준 완료 기록이 없으며 예정 경기를 완료 기록으로 생성하지 않는다.

수집 명령:

```powershell
ai-worker/venv/Scripts/python.exe ai-worker/analyzer.py --competition LCK_POSTSEASON --limit 20 --save
ai-worker/venv/Scripts/python.exe ai-worker/analyzer.py --competition WORLDS --date 2026-10-16 --save
```

월즈 명령의 날짜는 한국 날짜이며, 실행 시 완료된 원본 세트가 있는 경우에만 저장한다. 완료된 시리즈 전체임을 자동 보장하는 명령은 아니며 수집 후 세트 수 대조가 필요하다. 자동 실행·실패 작업 재개는 아직 별도 구현이 필요하다.

요약 문서의 catalogSortKey는 시즌:대회|날짜시각이다. 같은 필드의 범위 조건과 정렬을 사용하여 기존 최대 10개 목록 보안 규칙과 기본 단일 필드 인덱스로 대회 필터를 지원한다. 원본 tournament는 그대로 보존한다. 화면 메뉴용 competitions.json은 config 원본과 같은 내용으로 유지한다.

[한국어 공식 월즈 일정](https://lolesports.com/ko-KR/news/worlds-2026-primer): 한국 날짜 10월 16일~11월 15일.

## 수집 완료와 검증

LCK 포스트시즌 13경기·55세트(플레이인 3경기·14세트, 플레이오프 10경기·41세트)를 저장했다. 원본 GameId 55개와 저장된 sourceGameId 55개가 정확히 일치하며 중복이 없다. 55세트 모두 상세 스탯과 타임라인을 포함한다. 기존 2경기·5세트를 보존해 전체 저장량은 15경기·60세트다.

원본 팀 이름 Dplus Kia와 화이트리스트 Dplus KIA의 대소문자 차이로 누락되던 16세트를 확인하고, 대소문자를 무시하는 비교로 수정해 재수집했다. 원본 팀 이름은 저장 시 그대로 유지한다. 특정 시리즈를 다시 수집할 때는 --series-id로 원본 MatchId를 지정할 수 있다.

익명 클라이언트에서 포스트시즌 목록을 10개와 3개로 나눠 조회하여 13개 고유 시리즈를 확인했다. Python 25개·프론트엔드 16개 테스트, 린트·빌드를 통과했다. 빌드에는 기존 초기 번들 크기 경고가 남아 있다. 신규 경기의 AI 분석은 이번 수집에서 생성하지 않았다.

경기 요약과 상세 카드에 기존 public/teams 팀 이미지를 표시한다. 팀 이름의 대소문자 차이를 처리하고 파일이 없거나 로드에 실패하면 기본 마크를 표시한다. 다른 국제대회 참가 팀의 로고는 추후 추가할 수 있다.
