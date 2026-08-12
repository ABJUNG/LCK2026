import os
from dotenv import load_dotenv
from google import genai

# 환경변수 로드 및 클라이언트 생성
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("🔍 내 API 키로 사용 가능한 모델 목록:")
print("-" * 40)

# 사용 가능한 모든 모델 리스트 출력
for model in client.models.list():
    # generateContent(텍스트 생성) 기능이 지원되는 모델만 필터링
    if "generateContent" in model.supported_actions:
        print(model.name)
        
print("-" * 40)