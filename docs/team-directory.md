# Leaguepedia 팀 디렉터리

수집 명령: `ai-worker/venv/Scripts/python.exe ai-worker/rosters.py --write`
`--write` 없이 실행하면 통계만 출력합니다. 기존 인증 환경변수를 사용하며 Firebase는 변경하지 않습니다.

## 데이터 흐름

Leaguepedia Cargo → Python 검증·정리 → `frontend/public/team-rosters.json` → React 팀 디렉터리.
팀 명단을 펼칠 때만 JSON을 읽습니다. 정적 스냅샷이며 자동 갱신은 아닙니다.

- Players: 현재 팀, 공개 이름, 닉네임, 국가, 기본 역할.
- TenuresUnbroken → RosterChangeIds → RosterChanges → NewsItems: 현재 소속 기간과 최신 세부 역할·상태.
- PlayerRedirects: 동명이인 문서 및 별칭 대응. ID는 닉네임이 아닌 원본 문서명.
- 지원 팀 별칭은 명시적으로 관리하고 정확히 대응합니다. 아카데미·CL 팀을 이름 유사도로 합치지 않습니다.
- 비활동·후보 상태를 표시하고 스트리머/구단주만으로 등록된 인물은 제외합니다.
- 최신 시각에 상충하는 역할이 있으면 기본 프로필 역할로 돌아가고 세부 확인 불가를 표시합니다.
- 전체 조회 성공 및 10팀 선수 존재 검증 후 임시 파일을 원자적으로 교체합니다. 실패하면 기존 파일을 보존합니다.

이 명단은 수집 시점의 원본 현재 소속이며 2026 시즌 전체 또는 대회 공식 등록 명단이 아닙니다. 과거 matches 데이터와 결합하거나 덮어쓰지 않습니다. 향후 이적 이력은 별도 기간 데이터로 확장합니다.

## 출처

https://lol.fandom.com/wiki/Module:TeamMembers
Leaguepedia 및 기여자, CC BY-SA 3.0. 각 팀·개인 문서 링크와 수집일 표시. 역할명 번역·팀별 분류. 이미지 권리 확인 전 인물 사진은 수집하지 않습니다.
