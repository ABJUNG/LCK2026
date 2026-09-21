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

# 💡 파라미터에 target_date 추가 (기본값은 None)
def fetch_recent_lck_matches(limit_count=10, target_date=None):
    if target_date:
        print(f"🌐 Leaguepedia API에서 [{target_date}]에 진행된 LCK 경기를 탐색 중입니다...")
    else:
        print(f"🌐 Leaguepedia API에서 최근 경기를 탐색 중입니다...")
        
    FANDOM_USERNAME = os.getenv("FANDOM_USERNAME")
    BOT_PASSWORD_SECRET = os.getenv("FANDOM_BOT_PASSWORD")

    # 💡 1. 원래대로 .env 인증 사용 (인증은 이미 완벽합니다)
    auth_cred = AuthCredentials(username=FANDOM_USERNAME, password=BOT_PASSWORD_SECRET)
    site = EsportsClient("lol", credentials=auth_cred, user_agent="LCK_2026_Data_App_by_tjdnf")
    
    # 🚨 2. DB가 싫어하는 복잡한 IN 조건 제거! 아주 단순한 WHERE 절 생성
    where_clause = "Tournament LIKE '%LCK%2026%'"
    if target_date:
        where_clause += f" AND DateTime_UTC >= '{target_date} 00:00:00' AND DateTime_UTC <= '{target_date} 23:59:59'"

    def safe_query(**kwargs):
        for attempt in range(3):
            try:
                return site.cargo_client.query(**kwargs)
            except Exception as e:
                error_details = str(e)
                print(f"\n   🚨 [API 오류] 시도 {attempt+1}/3: {error_details}")
                if "ratelimited" in error_details.lower():
                    import time
                    time.sleep(30)
                else:
                    raise e
        return None

    # 💡 3. 경기 기본 정보 (순정 테이블 이름 사용, 정렬 옵션 제거)
    games_response = safe_query(
        tables="ScoreboardGames",
        fields="GameId, Tournament, DateTime_UTC, Team1, Team2, Team1Score, Team2Score, Patch, N_GameInMatch, MatchId",
        where=where_clause,
        limit=limit_count * 5
    )

    if not games_response:
        print("❌ 조건에 맞는 경기 데이터를 찾을 수 없습니다.")
        return []

    # 파이썬에서 안전하게 시간순 정렬 (DB 부담 제로)
    games_response = sorted(games_response, key=lambda x: x.get('DateTime_UTC', ''))

    lck_1st_teams = ["Gen.G", "T1", "Dplus KIA", "FearX", "OKSavingsBank BRION", "Hanwha Life Esports", "KT Rolster", "Kwangdong Freecs", "Nongshim RedForce", "DRX"]
    
    games_map = {}
    game_ids = []
    
    for row in games_response:
        # 🚨 4. 1군 팀 필터링을 파이썬에서 수행!
        if row.get('Team1') not in lck_1st_teams or row.get('Team2') not in lck_1st_teams:
            continue

        g_id = row['GameId']
        game_ids.append(f"'{g_id}'")
        
        date_kst, time_kst = convert_utc_to_kst(row.get('DateTime_UTC', ''))
        week_kr, week_en = extract_week_info(row.get('MatchId', ''), row.get('Tournament', ''))
        
        games_map[g_id] = {
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
            "set_number": str(row.get('N_GameInMatch') or "1"),
            "team_A_bans": [], "team_B_bans": [],
            "team_A_players": [], "team_B_players": []
        }
        
        if len(games_map) >= limit_count:
            break
            
    if not game_ids:
        print("❌ 1군 경기 데이터를 찾을 수 없습니다.")
        return []
        
    game_ids_str = ", ".join(game_ids)

    # 💡 5. 밴픽 데이터
    pb_response = safe_query(
        tables="PicksAndBansS7=PB",
        fields="PB.GameId, PB.Team1Ban1, PB.Team1Ban2, PB.Team1Ban3, PB.Team1Ban4, PB.Team1Ban5, PB.Team2Ban1, PB.Team2Ban2, PB.Team2Ban3, PB.Team2Ban4, PB.Team2Ban5",
        where=f"PB.GameId IN ({game_ids_str})"
    )
    if pb_response:
        for pb in pb_response:
            g_id = pb['GameId']
            if g_id in games_map:
                games_map[g_id]["team_A_bans"] = [pb.get(f'Team1Ban{i}', '') for i in range(1, 6)]
                games_map[g_id]["team_B_bans"] = [pb.get(f'Team2Ban{i}', '') for i in range(1, 6)]

    # 💡 6. 선수 데이터
    players_response = safe_query(
        tables="ScoreboardPlayers=SP",
        fields="SP.GameId, SP.Link, SP.Team, SP.Champion, SP.Role, SP.Kills, SP.Deaths, SP.Assists, SP.Gold, SP.DamageToChampions",
        where=f"SP.GameId IN ({game_ids_str})"
    )
    if players_response:
        import re
        for sp in players_response:
            g_id = sp['GameId']
            if g_id in games_map:
                clean_name = re.sub(r'\s*\(.*?\)', '', sp.get('Link', 'Unknown'))
                player_info = {
                    "name": clean_name,
                    "role": sp.get('Role', ''),
                    "champion": sp.get('Champion', ''),
                    "kills": int(sp.get('Kills') or 0),
                    "deaths": int(sp.get('Deaths') or 0),
                    "assists": int(sp.get('Assists') or 0),
                    "gold": int(sp.get('Gold') or 0),
                    "damage": int(sp.get('DamageToChampions') or 0)
                }
                if sp.get('Team') == games_map[g_id]['team_A']:
                    games_map[g_id]['team_A_players'].append(player_info)
                else:
                    games_map[g_id]['team_B_players'].append(player_info)

    print(f"✅ 총 {len(games_map)}개 세트의 데이터 조립을 완료했습니다!\n")
    return list(games_map.values())

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
    # 💡 사용자에게 날짜 입력받기 (터미널에서 타이핑)
    print("=========================================")
    user_input_date = input("📅 분석할 LCK 경기 날짜를 입력하세요 (예: 2026-08-16)\n[그냥 엔터(Enter)를 치면 가장 최근 3세트를 가져옵니다]: ").strip()
    print("=========================================\n")

    if user_input_date:
        # 특정 날짜를 입력한 경우, 그 날의 모든 세트(넉넉하게 10세트)를 가져옴
        recent_matches = fetch_recent_lck_matches(limit_count=10, target_date=user_input_date)
    else:
        # 엔터를 친 경우 최근 3세트만 가져옴
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
            
            print("⏳ API 호출 한도 보호를 위해 30초 대기합니다...\n")
            import time
            time.sleep(30) 

        print(f"🎉 모든 파이프라인 처리가 완료되었습니다!")
    else:
        print(f"❌ 해당 조건({user_input_date})에 맞는 경기 데이터를 찾지 못했습니다.")