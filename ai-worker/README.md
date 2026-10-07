# 엘식혜 데이터 워커

## 동작 흐름

Leaguepedia API → leaguepedia.py 검증 → match_document.py 문서 변환 → analyzer.py Firestore 저장 → React MatchList 조회 → groupMatches 팀 정렬 → Matchcard 표시.

브라우저는 Leaguepedia를 직접 호출하지 않습니다. 목록 새로고침은 Firestore를 다시 조회합니다. API 재수집은 워커를 실행해야 합니다.

## 실행 (저장소 루트)

기존 ai-worker/venv 환경을 사용합니다. .env와 firebase-key.json은 Git에 포함하지 않습니다.
필수 환경변수: FANDOM_USERNAME, FANDOM_BOT_PASSWORD (기존 BOT_PASSWORD_SECRET도 지원).
AI 분석을 요청할 때 GEMINI_API_KEY와 모델 지정(--model 또는 GEMINI_MODEL)이 필요합니다.

```powershell
# 실제 API 수집·검증만 수행, DB 저장 없음
ai-worker/venv/Scripts/python.exe ai-worker/analyzer.py --date 2026-08-16
# 검증 완료한 전체 시리즈를 저장
ai-worker/venv/Scripts/python.exe ai-worker/analyzer.py --date 2026-08-16 --save
# 날짜 대신 최근 3개 시리즈
ai-worker/venv/Scripts/python.exe ai-worker/analyzer.py --limit 3 --save
```

--analyze를 추가하면 Gemini를 호출합니다. 이번 작업에서 새 AI 분석은 실행하지 않았습니다.
--output 경로 옵션으로 검증한 문서를 JSON으로 내보낼 수 있습니다.

## 정확성 정책

- 한국 날짜를 UTC 조회 범위로 변환합니다.
- Cargo의 필드 표시 이름 변환 문제를 피하도록 날짜·세트 번호에 명시적 별칭을 씁니다.
- 시리즈 MatchId를 찾고 해당 시리즈의 모든 세트를 다시 조회합니다.
- GameId, 승자, 팀별 5개 포지션 및 선수 10명을 검증합니다. 누락된 숫자는 0으로 만들지 않습니다.
- API 제한은 최대 3회 시도 후 오류로 종료합니다. 조회 실패를 빈 경기 목록으로 처리하지 않습니다.
- 모든 수집·검증 후 배치 저장합니다. 원본 GameId로 기존 문서를 먼저 찾고 중복이면 중단합니다.
- ID 없는 기존 문서는 옛 문서 경로가 정확히 일치할 때만 갱신합니다. 날짜·팀 이름이 다른 과거 문서는 별도로 남을 수 있습니다. 삭제하거나 추측 병합하지 않습니다.
- 원본 ID가 있는 경기가 존재하면 화면은 이를 우선 표시합니다. 원본 대조 전 데이터 포함 옵션은 공개 화면에서 제거했습니다. 기존 문서는 삭제하지 않았습니다.
- 데이터가 바뀌면 이전 AI 분석은 stale로 보존하고 화면에서 숨깁니다. 재분석 전에는 최신 분석으로 취급하지 않습니다.
- 초상화 에셋은 DDragon 16.18.1을 사용하며 경기 패치 값과 별개입니다.

## 검증 — 2026-09-23

8월 16일 실제 API에서 2경기 5세트를 수집하여 Firestore 저장과 브라우저 표시를 확인했습니다. Gemini 재생성·자동 스케줄 수집·운영 배포는 미실행입니다.

```powershell
ai-worker/venv/Scripts/python.exe -m unittest discover -s ai-worker/tests -v
npm --prefix frontend test
npm --prefix frontend run lint
npm --prefix frontend run build -- --configLoader native
```

외부 접속 없는 테스트는 KST 경계, 선수 누락, 누락값과 0 구분, 제한 재시도, 분석 유효성, 원본 식별자, 팀별 세트 정렬을 검증합니다.


## 상세 기록 확장 — 2026-09-23

ScoreboardGames에서 드래곤 6종·장로·전령·유충·아타칸·억제기·팀 골드·킬·경기 시간을 추가 수집합니다. ScoreboardPlayers에서 CS·시야·아이템·주문·룬을 수집합니다.
PostgameJsonMetadata가 가리키는 Leaguepedia V5 JSON에서 선수 피해·회복·보호막·와드 등의 경기 스탯을 선별합니다. 계정 ID·PUUID·핑 기록 등은 저장하지 않습니다.

postgame.py는 게임 ID·완료 여부·선수 10명·챔피언 조합·KDA를 대조합니다. 완결된 타임라인에서 포탑 방패, 건물, 주요 몬스터, 영혼 이벤트를 추출합니다. 방패 이벤트의 teamId는 파괴된 포탑 소유 팀이므로 상대 팀의 기록으로 집계합니다. teamId=0인 영혼 이벤트는 지형 변환이므로 영혼 획득으로 세지 않습니다.

방패 수는 원본 파괴 이벤트 수입니다. 특정 시즌의 상한 또는 골드 환산을 적용하지 않습니다. 드래곤 총수는 장로를 포함합니다. JSON이 없거나 불완전하면 수치를 0으로 생성하지 않고 미제공으로 표시합니다. 기본 경기 스탯은 계속 수집합니다. 전 대회·과거 패치의 모든 필드 수집을 보장하지 않으며, 대회 필터는 config/competitions.json의 지원 목록을 사용합니다. --competition WORLDS로 월즈를 지정할 수 있습니다.

AI 분석 실행 예시:

```powershell
ai-worker/venv/Scripts/python.exe ai-worker/analyzer.py --date 2026-08-16 --save --analyze --model gemini-3.5-flash
```

AI가 생성된 모델·시각·근거 지문을 저장합니다. 이 값은 사실 검증 완료를 의미하지 않습니다.
오브젝트 이미지 원본 주소 및 취득일은 frontend/public/objectives/sources.json, 사이트 하단 출처 표시는 SourceFooter.jsx에 있습니다. 신규 게임 아이콘은 Riot Games 소유, CommunityDragon 제공 이미지입니다. 기존 팀 로고의 개별 취득 출처는 확인되지 않았습니다.


## 선수 빌드 — 2026-09-28

V5 선수의 최종 item0~6, spell1Id/spell2Id(또는 summoner1Id/summoner2Id), perks, 게임 버전을 build 필드에 저장합니다. 검증 완료한 타임라인에서 해당 participantId의 구매·판매·되돌리기만 선별하고 participantId=0 또는 다른 선수 기록은 제외합니다. 아이템 파괴 이벤트는 조합 재료 소모일 수 있어 판매로 표시하지 않습니다. 되돌리기는 원본 데이터에 보존하지만 화면에서는 숨깁니다. 취소된 구매 자체는 구매 기록에 남으므로 최종 빌드는 종료 스냅샷으로 확인합니다.

선수 이름 버튼으로 상세 창을 열고 Escape 또는 닫기 버튼으로 닫습니다. 같은 분에 발생한 아이템 이벤트를 묶되 정확한 초를 함께 표시합니다. 최종 슬롯은 이벤트로 재구성하지 않고 종료 스냅샷을 사용합니다.

Riot Data Dragon 공개 JSON(ko_KR)과 이미지, CommunityDragon 능력치 파편을 사용합니다. 이 경로에는 Riot API 키가 필요하지 않습니다. 실제 gameVersion과 일치하는 패치 자료만 사용하고, 자료 미제공 시 원본 ID를 표시합니다. 경기마다 구매 취소·판매가 포함되므로 시간별 그룹은 귀환 횟수가 아닙니다.
아타칸은 간단/상세 오브젝트 화면에서 제거했습니다. 원본 보관 필드는 유지합니다. 이번 재수집으로 데이터 지문이 변경돼 기존 AI 분석은 재분석 필요 상태가 될 수 있습니다. AI 재생성은 이번 작업에 포함하지 않습니다.

## 최신 마무리 · 2026-09-28

선수별 SKILL_LEVEL_UP 기록을 검증된 타임라인에서 추출합니다. 실제 선수 ID와 1~4 스킬 슬롯만 저장합니다. 화면은 습득 순서대로 Q/W/E/R을 표시하며 챔피언 레벨로 추측하지 않습니다. 오늘 Python 18개·프론트 10개 테스트를 통과했습니다. 전체 상태와 다음 작업은 `../docs/handoff-2026-09-28.md`를 참고하세요.

## 경기 요약 저장 · 2026-10-07

워커 저장은 matches 상세와 matchSeries 요약을 같은 배치로 반영합니다. 최대 200세트로 제한해 시리즈 요약을 포함한 배치 크기를 제한합니다. 기존 데이터의 요약 생성은 `ai-worker/venv/Scripts/python.exe ai-worker/series_summary.py --save`로 실행합니다. 기본 실행은 미리보기입니다. 원본 상세는 삭제하지 않습니다. 요약에는 선수 빌드를 넣지 않으며 기존에 원본 ID가 없는 문서는 제외합니다.


## 수집 안정화 · 2026-10-07

이제 반복 수집은 collect.py를 사용합니다. analyzer.py는 특정 시리즈의 수동 재수집·AI 분석에 사용할 수 있습니다. 두 명령은 같은 로컬 실행 잠금을 사용합니다.

```powershell
# 대회 전체의 완료 세트를 탐색하고 저장된 ID·요약과 비교 (DB 변경 없음)
ai-worker/venv/Scripts/python.exe ai-worker/collect.py --competition LCK_POSTSEASON
# 새 세트 또는 요약 누락이 있는 시리즈만 수집·검증·저장
ai-worker/venv/Scripts/python.exe ai-worker/collect.py --competition LCK_POSTSEASON --save
# 특정 한국 날짜에 열린 시리즈의 모든 완료 세트 수집
ai-worker/venv/Scripts/python.exe ai-worker/collect.py --competition WORLDS --date 2026-10-16 --save
# 실패·중단된 저장 작업 재개: 출력된 실행 기록 파일명 사용
ai-worker/venv/Scripts/python.exe ai-worker/collect.py --resume 실행기록파일명.json --save
# 원본 수정 반영을 위한 재조회 (기존 경기도 수집)
ai-worker/venv/Scripts/python.exe ai-worker/collect.py --competition LCK_POSTSEASON --date 2026-09-13 --refresh --save
```

실행 기록은 ai-worker/.collection-runs에 저장하며 Git에서 제외합니다. 실행 파일에 범위·원본 세트 ID·성공/실패·누락 ID·시도 횟수·상세 자료 미제공 ID를 기록합니다. 네트워크 오류 원문에는 인증 정보가 포함될 수 있어 오류 종류와 처리 단계만 기록합니다. 날짜 탐색은 해당 날짜에 걸친 시리즈를 찾는 것이므로 저장 시에는 날짜 밖 세트도 다시 조회합니다.

기본 실행은 비교 미리보기이며 DB를 수정하지 않습니다. --save 실행에서 실패한 시리즈가 있으면 다른 시리즈는 계속 처리하고 종료 코드는 1입니다. --resume은 원래 실행 범위를 사용하며 이미 성공한 시리즈를 건너뜁니다. 원본에 뒤늦게 추가된 세트를 찾으려면 새 실행을 시작합니다. 정상 저장 여부는 원본 ID 집합과 matchSeries 요약으로 대조합니다. 원본에서 사라진 세트는 자동 삭제하지 않고 불일치로 남깁니다.

기본 반복 실행은 저장된 세트의 스탯 변경을 감지하지 않으므로 --refresh로 다시 조회합니다. 상세 JSON 미제공은 기본 경기 수집 실패와 구분합니다. 완료 세트 수집이 시리즈 종료 또는 대회 전체 완료를 보장하지 않습니다. 자동 예약 실행과 여러 서버 사이의 분산 잠금은 아직 구현하지 않았습니다. 한 컴퓨터·한 저장소에서 단일 워커로 운영하세요.

신규 상세 문서 ID는 원본 GameId의 해시를 사용합니다. 기존 문서 ID는 유지합니다. 상세와 요약은 시리즈별 같은 배치로 저장하고 저장 후 다시 읽어 대조합니다. [설계·검증·학습 기록](../docs/collection-stability-2026-10-07.md)을 참고하세요.


## 관전자용 구조화 AI 분석

수집과 분석을 분리한 analyze_saved.py를 사용합니다. 이미 저장된 시리즈의 세트만 읽고 aiReview 필드만 갱신하므로 경기 데이터 수집 성공과 AI API 실패가 서로 영향을 주지 않습니다.

```powershell
# 대상 확인: AI 호출·저장 없음
ai-worker/venv/Scripts/python.exe ai-worker/analyze_saved.py --series-id "LCK/2026 Season/Season Playoffs_Finals_1"
# 최대 4세트 분석·저장 (동일 근거의 생성된 분석은 건너뜀)
ai-worker/venv/Scripts/python.exe ai-worker/analyze_saved.py --series-id "LCK/2026 Season/Season Playoffs_Finals_1" --model gemini-3.1-flash-lite --limit 4 --save
```

--limit는 1~5, --force는 동일 근거 분석도 다시 호출합니다. 기본 모델은 GEMINI_MODEL 또는 gemini-3.1-flash-lite입니다. 대회 전체 자동 분석과 예산 기반 실행은 아직 구현하지 않았습니다. 수집·분석 명령은 같은 로컬 잠금을 사용합니다.

review.py는 표시용 필드와 선수 구매 원문을 제외한 근거를 선별합니다. 확인된 기록 문장은 코드가 만들고 AI는 요약·조합·승패 관련 해석 및 사용한 근거 ID를 반환합니다. JSON 구조·문장 길이·근거 ID 존재를 검사하되 해석의 정확성과 인과관계가 자동 검증됐다는 의미는 아닙니다. 실제 영상을 보지 않으므로 화면에 AI 추정과 분석 한계를 표시합니다.

상태는 pending → running → generated 또는 failed이며, 수집으로 근거가 바뀌면 stale입니다. interrupted 이후에는 같은 명령을 다시 실행합니다. 분석 중 DB 근거가 바뀌면 트랜잭션 비교로 저장을 거부합니다. 요청에는 타임아웃과 제한된 재시도를 설정하며 오류 원문·키를 저장하지 않습니다. 이미 열린 화면은 실시간 구독이 아니므로 목록 새로고침 후 경기 펼치기로 최신 상태를 확인합니다.

브라우저는 AI 키를 받거나 AI 호출을 직접 수행하지 않습니다. 기존 analyzer.py --analyze는 이전 텍스트 리포트 방식으로 남아 있으며 신규 구조화 분석에는 analyze_saved.py를 사용합니다.

SDK 대기와 관계없이 세트당 실제 경과 120초를 넘으면 별도 분석 프로세스를 종료하고 실패로 저장합니다. JSON 형식 검증은 해석 정확성의 보장이 아닙니다. [개발·검증 기록](../docs/ai-review-2026-10-07.md)을 참고하세요.


관전평 연결: communityReview에는 원본 경기 ID·세트·나무위키 문서 URL·제공일·기여자·라이선스·요약 문단을 저장합니다. 현재는 사용자가 전달한 결승 1세트 텍스트를 수동 입력한 단계이며 자동 크롤링이나 관리 화면은 없습니다. commentary.py가 경기 대응과 입력 크기를 검증하며, 분석은 F(경기 기록)와 N(작성자 관전평)을 구분합니다. 관전평이 바뀌면 기존 결과를 최신으로 취급하지 않습니다.

현재 세트별 전체 생성 상한은 120초입니다. SDK 요청당 30초, 일시 오류 최대 3회와 대기 시간을 포함하며 상한을 넘으면 프로세스를 종료합니다. 결승 1·3세트의 실패를 복구하여 현재 4세트 모두 generated이며 현재 근거와 일치합니다. 1세트는 사용자 제공 관전평을 반영했습니다. 복구 뒤 문장 개선 작업에서 결승 4세트를 다시 생성했습니다. 자동 분석 운영과 해석 정확성의 검증은 별도 과제입니다.


신규 분석은 GenerateContent의 구조화 JSON 응답을 사용합니다. finish_reason이 STOP인 완결 응답만 검증·저장합니다. 기본 모델은 gemini-3.1-flash-lite이며 --model 또는 GEMINI_MODEL로 변경할 수 있습니다. SDK 자체 재시도를 끄고 워커가 일시 오류·시간 초과를 최대 3회 처리합니다. 관전평을 포함하면 요약에 N 근거가 있어야 합니다. 출처 문구를 본문마다 삽입하지 않고 화면에서 해당 근거의 community_opinion 유형을 이용해 관전평 참고 표시를 붙입니다. 입력·출력·추론·총 토큰 수와 지침 버전을 기록하며 오류 종류·상태 코드만 저장합니다. 근거 ID의 존재 검사는 사건 순서나 해석의 의미를 검증하지 않습니다.


분석 지침 spectator-v6는 요약 1~2문장, 밴픽·경기 흐름 각각 1~2항목과 항목당 100자 이내를 목표로 합니다. 요약은 결론, 밴픽은 조합 역할, 경기 흐름은 사건을 설명하며 같은 설명을 반복하지 않도록 요청합니다. 문장 길이는 생성 지침이며 현재 코드의 저장 상한(요약 200자·상세 500자)과 구분합니다. AI 추정과 작성자 의견의 출처는 UI에서 표시하며 근거 ID·출처·이용 조건을 보존합니다.

## 분석 품질 평가
새 생성은 spectator-v7 지침과 review_quality.py의 제한된 검사를 사용합니다. 시점별 근거 없는 골드 변화·라인전 우위·경기 균형·교전 장면을 저장 전에 거부합니다. 작성자 의견 예외는 해당 문장이 실제 N 근거를 인용하는 경우에만 적용합니다. 규칙 통과는 의미·영상 검증 완료가 아닙니다.
```powershell
# 읽기 전용 평가: AI 호출과 DB 변경 없음
ai-worker/venv/Scripts/python.exe ai-worker/evaluate_saved.py --series-id "LCK/2026 Season/Season Playoffs_Finals_1"
```
결승 4세트에서 근거 부족 표현 6곳을 찾고 에이전트가 근거를 대조하여 편집했습니다. AI 초안·수정 범위·검토자를 editorialRevision에 보존하며 humanReviewStatus는 not_reviewed입니다. [평가 기준·사례·검증](../docs/review-quality-2026-10-07.md)을 참고하세요.
