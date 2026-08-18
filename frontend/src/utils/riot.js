// frontend/src/utils/riot.js

// 챔피언 이름 변환 예외 처리 딕셔너리
const CHAMPION_NAME_MAP = {
  "K'Sante": "KSante",
  "Twisted Fate": "TwistedFate",
  "Dr. Mundo": "DrMundo",
  "Master Yi": "MasterYi",
  "Miss Fortune": "MissFortune",
  "Tahm Kench": "TahmKench",
  "Xin Zhao": "XinZhao",
  "Aurelion Sol": "AurelionSol",
  "Jarvan IV": "JarvanIV",
  "Lee Sin": "LeeSin",
  "Wukong": "MonkeyKing",
  "Renata Glasc": "Renata",
  "Nunu & Willump": "Nunu",
  "Kog'Maw": "KogMaw",
  "Rek'Sai": "RekSai",
  "Bel'Veth": "Belveth",
  "Cho'Gath": "Chogath",
  "Kha'Zix": "Khazix",
  "Vel'Koz": "Velkoz",
  "Kai'Sa": "Kaisa",
  "LeBlanc": "Leblanc",
  "Ambessa": "Ambessa",
  "Smolder": "Smolder",
  "Mel": "Mel"
};

export const getChampionImageUrl = (championName) => {
  if (!championName) return "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-icons/-1.png";

  // 1. 매핑 테이블에 명시되어 있다면 해당 ID 사용
  let champId = CHAMPION_NAME_MAP[championName];

  if (!champId) {
    // 2. 특수문자(' space . 등) 제거 및 단어별 첫글자 대문자화
    champId = championName
      .replace(/['\s\.-]/g, "")
      .replace(/(^\w|\s\w)/g, (m) => m.toUpperCase());
  }

  // 최신 패치버전 15.3.1 기준으로 DDragon 이미지 호출
  return `https://ddragon.leagueoflegends.com/cdn/15.3.1/img/champion/${champId}.png`;
};

// 라인(포지션) 아이콘 변환
export const getRoleNameKr = (role) => {
  const roleMap = {
    "Top": "탑",
    "Jungle": "정글",
    "Mid": "미드",
    "Bot": "원딜",
    "Support": "서폿"
  };
  return roleMap[role] || role || "-";
};