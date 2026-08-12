import os
from dotenv import load_dotenv
from google import genai

# 1. 환경변수(.env)에서 API 키 불러오기
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# 2. 최신 SDK 방식으로 Gemini 클라이언트 생성
client = genai.Client(api_key=API_KEY)

def analyze_draft(match_data):
    print("🤖 AI가 L-Sikhye 밴픽을 최신 Interactions API(Gemini 3.5 Flash)로 분석 중입니다...\n")
    
    # 3. AI 프롬프트 구성
    prompt = f"""
    너는 LCK 최고 수준의 e스포츠 데이터 분석가이자 밴픽 전문가야.
    아래 제공되는 양 팀의 밴픽 데이터를 분석해서 다음 조건에 맞춰 리포트를 작성해줘.
    
    [조건]
    1. 각 팀의 밴픽 평점을 100점 만점 기준으로 매길 것 (예: T1: 85점, GEN: 90점).
    2. 양 팀의 조합 컨셉(돌진, 포킹, 밸류 등)을 요약할 것.
    3. 경기 승패에 결정적인 영향을 미친 픽(핵심 챔피언)과 그 이유를 3줄 이내로 분석할 것.
    4. 전문가 답고 세련된 어투를 사용할 것.
    
    [경기 데이터]
    - 패치 버전: {match_data['patch']}
    - {match_data['team_A']} 픽: {', '.join(match_data['team_A_picks'])}
    - {match_data['team_B']} 픽: {', '.join(match_data['team_B_picks'])}
    """

    # 4. 🚨 [핵심 변경] 기존 generate_content 대신 최신 Interactions API 사용
    interaction = client.interactions.create(
        model='gemini-3.5-flash',
        input=prompt,
    )
    
    # 5. 응답 텍스트 추출 방식도 output_text로 변경됨
    return interaction.output_text

# --- 테스트 실행부 ---
if __name__ == "__main__":
    sample_match = {
        "patch": "14.12",
        "team_A": "T1",
        "team_A_picks": ["크산테", "세주아니", "아지르", "세나", "노틸러스"],
        "team_B": "GEN",
        "team_B_picks": ["트위스티드 페이트", "마오카이", "코르키", "루시안", "나미"]
    }
    
    result = analyze_draft(sample_match)
    print("================ [L-Sikhye AI 분석 결과] ================")
    print(result)
    print("=========================================================")