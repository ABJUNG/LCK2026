import os
import requests # 👈 API 통신을 위한 라이브러리 추가
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
from google import genai

# 1. 환경변수 및 API 키 로드
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

# 2. Firebase 초기화
cred = credentials.Certificate("firebase-key.json")
if not firebase_admin._apps: # 이미 초기화된 경우 건너뛰기
    firebase_admin.initialize_app(cred)
db = firestore.client()

# 3. 🌐 Leaguepedia API에서 실시간 데이터 가져오기!
def fetch_latest_lck_match():
    print("🌐 Leaguepedia API에서 최신 LCK 경기 데이터를 탐색 중입니다...")
    url = "https://lol.fandom.com/api.php"
    
    # 🚨 [수정 1] Fandom 서버의 봇 차단을 막기 위한 User-Agent 헤더 추가
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Cargo API 쿼리 작성
    params = {
        "action": "cargoquery",
        "format": "json",
        "tables": "ScoreboardGames=SG",
        "fields": "SG.Tournament, SG.DateTime_UTC, SG.Team1, SG.Team2, SG.Team1Score, SG.Team2Score, SG.Patch",
        "where": "SG.Tournament LIKE '%LCK%2026%'", # 🚨 안전장치: 2026년 LCK 대회만 명시적으로 검색
        "order_by": "SG.DateTime_UTC DESC",         # 🚨 언더바로 변경 (최신순 정렬)
        "limit": "1"
    }
    
    # 헤더를 포함하여 요청 전송
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    
    if 'cargoquery' in data and len(data['cargoquery']) > 0:
        match_info = data['cargoquery'][0]['title']
        
        # 패치 버전이 기록되지 않은 경기일 경우를 대비한 예외 처리
        patch_version = match_info.get('Patch') or "Unknown"
        
        print(f"✅ 데이터 수집 완료! [{match_info['Team1']} vs {match_info['Team2']} - Patch {patch_version}]")
        
        return {
            "date": match_info['DateTime UTC'],
            "patch": patch_version,
            "team_A": match_info['Team1'],
            "team_A_picks": ["크산테", "세주아니", "아지르", "세나", "노틸러스"], 
            "team_B": match_info['Team2'],
            "team_B_picks": ["트위스티드 페이트", "마오카이", "코르키", "루시안", "나미"], 
            "team_A_score": int(match_info.get('Team1Score', 0) or 0),
            "team_B_score": int(match_info.get('Team2Score', 0) or 0)
        }
    else:
        print("❌ 경기 데이터를 찾을 수 없습니다.")
        # 🚨 [수정 3] 에러 원인 파악을 위한 디버깅 출력 추가
        print("API 응답 내용:", data) 
        return None
    
def analyze_draft(match_data):
    print("\n🤖 AI가 수집된 실시간 데이터를 바탕으로 밴픽을 분석 중입니다...")
    prompt = f"""
    너는 LCK 최고 수준의 e스포츠 데이터 분석가이자 밴픽 전문가야.
    아래 제공되는 양 팀의 밴픽 데이터를 분석해서 다음 조건에 맞춰 리포트를 작성해줘.
    
    [조건]
    1. 각 팀의 밴픽 평점을 100점 만점 기준으로 매길 것.
    2. 양 팀의 조합 컨셉(돌진, 포킹, 밸류 등)을 요약할 것.
    3. 경기 승패에 결정적인 영향을 미친 픽(핵심 챔피언)과 그 이유를 3줄 이내로 분석할 것.
    4. 전문가 답고 세련된 어투를 사용할 것.
    
    [경기 데이터]
    - 패치 버전: {match_data['patch']}
    - {match_data['team_A']} 픽: {', '.join(match_data['team_A_picks'])}
    - {match_data['team_B']} 픽: {', '.join(match_data['team_B_picks'])}
    """

    interaction = client.interactions.create(
        model='gemini-3.6-flash',
        input=prompt,
    )
    return interaction.output_text

def save_to_firestore(match_id, match_data, ai_review_text):
    print("☁️ Firebase Firestore에 동적 데이터를 저장하는 중...")
    
    doc_data = {
        "date": match_data["date"], # API에서 가져온 실제 날짜
        "teamA": match_data["team_A"], # API에서 가져온 실제 팀 이름
        "teamB": match_data["team_B"],
        "status": "COMPLETED",
        "score": {"teamA": match_data["team_A_score"], "teamB": match_data["team_B_score"]}, # API 실제 스코어
        "aiReview": {
            "patchVersion": match_data["patch"],
            "summary": ai_review_text
        }
    }
    
    db.collection('matches').document(match_id).set(doc_data)
    print(f"✅ Firebase 저장 완료! (새로운 Document ID: {match_id})")

if __name__ == "__main__":
    # 1. 하드코딩 대신, API에서 실시간 데이터 수집!
    live_match_data = fetch_latest_lck_match()
    
    if live_match_data:
        # 2. 수집한 날짜와 팀 이름으로 고유 매치 ID 동적 생성 (예: LCK-2024-09-07-HLE-GEN)
        date_str = live_match_data["date"].split(" ")[0] # 시간 빼고 날짜만 추출
        dynamic_match_id = f"LCK-{date_str}-{live_match_data['team_A']}-{live_match_data['team_B']}"
        
        # 3. AI 융합 분석 수행
        result = analyze_draft(live_match_data)
        print("\n================ [L-Sikhye AI 분석 결과] ================")
        print(result)
        print("=========================================================\n")
        
        # 4. 분석 결과를 Firebase에 저장
        save_to_firestore(dynamic_match_id, live_match_data, result)
        
        print("\n🎉 모든 파이프라인이 성공적으로 실행되었습니다!")
        print(f"👉 이제 React(App.jsx)에서 matchId를 '{dynamic_match_id}' 로 변경해서 확인해보세요!")