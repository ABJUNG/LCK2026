import os
import re
import time
from datetime import datetime, timezone, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
from google import genai

from mwrogue.esports_client import EsportsClient
from mwrogue.auth_credentials import AuthCredentials

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

cred = credentials.Certificate("firebase-key.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

def convert_utc_to_kst(utc_str):
    if not utc_str:
        return "2026-01-01", "00:00"
    try:
        dt_utc = datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        dt_kst = dt_utc.astimezone(timezone(timedelta(hours=9)))
        return dt_kst.strftime("%Y-%m-%d"), dt_kst.strftime("%H:%M")
    except Exception:
        date_part = utc_str.split(" ")[0] if " " in utc_str else utc_str
        return date_part, "17:00"

def extract_week_info(match_id_raw, tournament_str):
    combined_str = f"{match_id_raw} {tournament_str}"
    week_match = re.search(r'Week\s*(\d+)|W(\d+)|_W(\d+)_', combined_str, re.IGNORECASE)
    if week_match:
        week_num = next(w for w in week_match.groups() if w is not None)
        return f"{week_num}주차", f"Week {week_num}"
    if "Playoffs" in combined_str: return "플레이오프", "Playoffs"
    elif "Finals" in combined_str: return "결승전", "Finals"
    return "정규시즌", "Regular Season"

def fetch_recent_lck_matches(limit_count=3):
    print(f"🌐 Leaguepedia API에서 선수 세부 데이터가 포함된 최근 {limit_count}개 세트를 탐색 중입니다...")
    
    # 🚨 os.getenv()로 .env 파일에서 불러옵니다!
    FANDOM_USERNAME = os.getenv("FANDOM_USERNAME")
    BOT_PASSWORD_SECRET = os.getenv("FANDOM_BOT_PASSWORD")

    auth_cred = AuthCredentials(username=FANDOM_USERNAME, password=BOT_PASSWORD_SECRET)
    site = EsportsClient("lol", credentials=auth_cred)
    
    lck_1st_teams = [
        "Gen.G", "T1", "Dplus KIA", "FearX", "OKSavingsBank BRION",
        "Hanwha Life Esports", "KT Rolster", "Kwangdong Freecs", "Nongshim RedForce", "DRX"
    ]
    teams_sql_str = ", ".join([f"'{team}'" for team in lck_1st_teams])
    
    # 🚨 ScoreboardGames + PicksAndBansS7 + ScoreboardPlayers 3개 테이블 JOIN
    response = site.cargo_client.query(
        tables="ScoreboardGames=SG, PicksAndBansS7=PB, ScoreboardPlayers=SP",
        join_on="SG.GameId=PB.GameId, SG.GameId=SP.GameId",
        fields="""
            SG.GameId, SG.Tournament=Tournament, SG.DateTime_UTC=DateTime, 
            SG.Team1=Team1, SG.Team2=Team2, 
            SG.Team1Score=Team1Score, SG.Team2Score=Team2Score, 
            SG.Patch=Patch, SG.N_GameInMatch=SetNumber, SG.MatchId=MatchId,
            PB.Team1Ban1, PB.Team1Ban2, PB.Team1Ban3, PB.Team1Ban4, PB.Team1Ban5,
            PB.Team2Ban1, PB.Team2Ban2, PB.Team2Ban3, PB.Team2Ban4, PB.Team2Ban5,
            SP.Link=PlayerName, SP.Team=PlayerTeam, SP.Champion=Champion, SP.Role=Role,
            SP.Kills=Kills, SP.Deaths=Deaths, SP.Assists=Assists, SP.Gold=Gold, SP.DamageToChampions=Damage
        """,
        where=f"SG.Tournament LIKE '%LCK%2026%' AND SG.Team1 IN ({teams_sql_str}) AND SG.Team2 IN ({teams_sql_str})",
        order_by="SG.DateTime_UTC DESC",
        limit=limit_count * 10
    )
    
    games_map = {}
    if response and len(response) > 0:
        for row in response:
            game_id = row['GameId']
            if game_id not in games_map:
                date_kst, time_kst = convert_utc_to_kst(row.get('DateTime', ''))
                week_kr, week_en = extract_week_info(row.get('MatchId', ''), row.get('Tournament', ''))
                
                games_map[game_id] = {
                    "tournament": row.get('Tournament', 'LCK 2026'),
                    "week_kr": week_kr,
                    "week_en": week_en,
                    "date_kst": date_kst,
                    "time_kst": time_kst,
                    "patch": row.get('Patch') or "Unknown",
                    "team_A": row.get('Team1', ''),
                    "team_B": row.get('Team2', ''),
                    "team_A_score": int(row.get('Team1Score') or 0),
                    "team_B_score": int(row.get('Team2Score') or 0),
                    "set_number": str(row.get('SetNumber') or "1"),
                    "team_A_bans": [row.get(f'Team1Ban{i}', '') for i in range(1, 6)],
                    "team_B_bans": [row.get(f'Team2Ban{i}', '') for i in range(1, 6)],
                    "team_A_players": [],
                    "team_B_players": []
                }
            
            # 괄호 안의 본명 제거 로직 추가
            raw_name = row.get('PlayerName', 'Unknown')
            clean_name = re.sub(r'\s*\(.*?\)', '', raw_name) # 괄호와 그 앞의 공백 제거

            player_info = {
                "name": clean_name, # 정제된 닉네임 저장
                "role": row.get('Role', ''),
                "champion": row.get('Champion', ''),
                "kills": int(row.get('Kills') or 0),
                "deaths": int(row.get('Deaths') or 0),
                "assists": int(row.get('Assists') or 0),
                "gold": int(row.get('Gold') or 0),
                "damage": int(row.get('DamageToChampions') or int(row.get('Damage') or 0)) # 딜량 필드 확실하게!
            }
            # 팀 구분
            if row.get('PlayerTeam') == games_map[game_id]['team_A']:
                games_map[game_id]['team_A_players'].append(player_info)
            else:
                games_map[game_id]['team_B_players'].append(player_info)

        print(f"✅ 총 {len(games_map)}개 세트의 선수 전원(10명) 픽/스탯 데이터를 완성했습니다!\n")
        return list(games_map.values())[:limit_count]
    else:
        print("❌ 경기 데이터를 찾을 수 없습니다.")
        return []

def analyze_draft(match_data):
    # AI 프롬프트에 포지션별 선수 닉네임과 픽 챔피언 제공
    team_a_lineup = ", ".join([f"{p['role']}: {p['name']}({p['champion']})" for p in match_data['team_A_players']])
    team_b_lineup = ", ".join([f"{p['role']}: {p['name']}({p['champion']})" for p in match_data['team_B_players']])

    prompt = f"""
    너는 LCK 최고 수준의 e스포츠 전력 분석가이자 밴픽 전문가야.
    아래 라인별 선수 출전 정보와 밴픽 데이터를 분석해서 전문 리포트를 작성해줘.
    
    [경기 정보]
    - 대회: {match_data['tournament']} {match_data['week_kr']} ({match_data['set_number']}세트)
    - {match_data['team_A']} 라인업: {team_a_lineup}
      * 밴: {', '.join(filter(None, match_data['team_A_bans']))}
    - {match_data['team_B']} 라인업: {team_b_lineup}
      * 밴: {', '.join(filter(None, match_data['team_B_bans']))}
    
    [작성 조건]
    1. 각 팀 밴픽 평점 (100점 만점)
    2. 양 팀 조합 컨셉 요약 (라인전 주도권, 한타 밸류, 사이드 운영 등)
    3. 라인별 핵심 매치업 및 승패를 가른 핵심 선수/픽 분석 (3줄 요약)
    """

    # 🚨 [추가] 429 에러(Rate Limit) 방어 및 자동 재시도 로직
    max_retries = 3
    for attempt in range(max_retries):
        try:
            interaction = client.interactions.create(
                model='gemini-3.6-flash',
                input=prompt,
            )
            return interaction.output_text
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "Quota" in error_msg:
                print(f"   ⚠️ API 할당량 초과 감지! 30초 대기 후 재시도합니다... ({attempt+1}/{max_retries})")
                import time
                time.sleep(30)
            else:
                # 429 Rate Limit이 아닌 진짜 에러면 그대로 프로그램 중단
                raise e
    
    return "API 호출 한도 초과로 인하여 분석 리포트를 생성하지 못했습니다."

    interaction = client.interactions.create(
        model='gemini-3.6-flash',
        input=prompt,
    )
    return interaction.output_text

def save_to_firestore(match_id, match_data, ai_review_text):
    # 포지션 순서 정렬 도우미
    role_order = {"Top": 1, "Jungle": 2, "Mid": 3, "Bot": 4, "Support": 5}
    
    team_a_sorted = sorted(match_data["team_A_players"], key=lambda x: role_order.get(x["role"], 99))
    team_b_sorted = sorted(match_data["team_B_players"], key=lambda x: role_order.get(x["role"], 99))

    doc_data = {
        "tournament": match_data["tournament"],
        "week": match_data["week_kr"],
        "weekEn": match_data["week_en"],
        "dateKST": match_data["date_kst"],
        "timeKST": match_data["time_kst"],
        "displayTitle": f"{match_data['tournament']} {match_data['week_kr']} | {match_data['date_kst']} {match_data['time_kst']} KST",
        "teamA": match_data["team_A"],
        "teamB": match_data["team_B"],
        "setNumber": match_data["set_number"],
        "status": "COMPLETED",
        "score": {"teamA": match_data["team_A_score"], "teamB": match_data["team_B_score"]},
        "players": {
            "teamA": team_a_sorted,
            "teamB": team_b_sorted
        },
        "bans": {
            "teamA": match_data["team_A_bans"],
            "teamB": match_data["team_B_bans"]
        },
        "aiReview": {
            "patchVersion": match_data["patch"],
            "summary": ai_review_text
        }
    }
    db.collection('matches').document(match_id).set(doc_data)

if __name__ == "__main__":
    recent_matches = fetch_recent_lck_matches(limit_count=3)
    if recent_matches:
        for match in recent_matches:
            time_clean = match['time_kst'].replace(":", "")
            date_clean = match['date_kst'].replace("-", "")
            week_code = match['week_en'].replace(" ", "")
            dynamic_match_id = f"LCK-{date_clean}-{time_clean}-{week_code}-{match['team_A']}-{match['team_B']}-SET{match['set_number']}"
            
            print(f"▶️ [{match['team_A']} vs {match['team_B']} {match['set_number']}세트] 선수 10명 세부 스탯 및 AI 분석 진행 중...")
            result = analyze_draft(match)
            save_to_firestore(dynamic_match_id, match, result)
            print(f"   ✅ Firestore 저장 완료! Document ID: {dynamic_match_id}\n")
            
            # 🚨 [추가] 무료 API 요금제 제한(Rate Limit)을 피하기 위해 1개 분석 후 30초 휴식
            print("⏳ API 호출 한도 보호를 위해 30초 대기합니다...\n")
            time.sleep(30) 

        print("🎉 모든 세부 선수 데이터 및 AI 리포트 저장이 완료되었습니다!")