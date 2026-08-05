"""
data_loader.py — Coleta automática de dados (API‑Football + FBref + Understat)
Versão otimizada: 3 créditos por análise. Fallback para temporada anterior.
Aproveitamento casa/fora incluso. Cache de 7 dias.
50 ligas pré‑mapeadas.
"""

import os, json, time, re, hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import requests
from bs4 import BeautifulSoup



# ============================================================
# Configurações gerais
# ============================================================
CACHE_DIR = Path("data")
CACHE_DIR.mkdir(exist_ok=True)
DELAY_FBREF = 8
DELAY_UNDERSTAT = 2
HEADERS_FBREF = {"User-Agent": "EngramScoreBot/1.0 (analytics@engramscore.com)"}
HEADERS_UNDERSTAT = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
CACHE_TTL = timedelta(days=7)



# ============================================================
# 50 ligas mapeadas
# ============================================================
LIGAS_MAP = {
    "Premier League": {"api_id": 39, "understat": "EPL", "fbref_comp": "9", "fbref_slug": "Premier-League"},
    "La Liga": {"api_id": 140, "understat": "La_liga", "fbref_comp": "12", "fbref_slug": "La-Liga"},
    "Bundesliga": {"api_id": 78, "understat": "Bundesliga", "fbref_comp": "20", "fbref_slug": "Bundesliga"},
    "Serie A": {"api_id": 135, "understat": "Serie_A", "fbref_comp": "11", "fbref_slug": "Serie-A"},
    "Ligue 1": {"api_id": 61, "understat": "Ligue_1", "fbref_comp": "13", "fbref_slug": "Ligue-1"},
    "Brasileirão Série A": {"api_id": 71, "understat": "BRA", "fbref_comp": "24", "fbref_slug": "Campeonato-Brasileiro-Serie-A"},
    "Eredivisie": {"api_id": 88, "understat": "Eredivisie", "fbref_comp": "23", "fbref_slug": "Eredivisie"},
    "Liga Portugal": {"api_id": 94, "understat": "Liga_Portugal", "fbref_comp": "32", "fbref_slug": "Primeira-Liga"},
    "Scottish Premiership": {"api_id": 179, "understat": "SPL", "fbref_comp": "43", "fbref_slug": "Scottish-Premiership"},
    "Championship": {"api_id": 40, "understat": "Championship", "fbref_comp": "10", "fbref_slug": "Championship"},
    "Belgian Pro League": {"api_id": 144, "understat": "Jupiler", "fbref_comp": "37", "fbref_slug": "Belgian-Pro-League"},
    "Swiss Super League": {"api_id": 207, "understat": "Swiss", "fbref_comp": "46", "fbref_slug": "Swiss-Super-League"},
    "Austrian Bundesliga": {"api_id": 218, "understat": "Austrian", "fbref_comp": "35", "fbref_slug": "Austrian-Bundesliga"},
    "Russian Premier League": {"api_id": 235, "understat": "RPL", "fbref_comp": "42", "fbref_slug": "Russian-Premier-League"},
    "Ukrainian Premier League": {"api_id": 333, "understat": "UPL", "fbref_comp": "39", "fbref_slug": "Ukrainian-Premier-League"},
    "Czech First League": {"api_id": 345, "understat": "Czech", "fbref_comp": "34", "fbref_slug": "Czech-First-League"},
    "Croatian HNL": {"api_id": 210, "understat": "HNL", "fbref_comp": "48", "fbref_slug": "Croatian-HNL"},
    "Serbian SuperLiga": {"api_id": 286, "understat": "Serbian", "fbref_comp": "54", "fbref_slug": "Serbian-SuperLiga"},
    "Danish Superliga": {"api_id": 119, "understat": "Danish", "fbref_comp": "31", "fbref_slug": "Danish-Superliga"},
    "Allsvenskan": {"api_id": 113, "understat": "Allsvenskan", "fbref_comp": "29", "fbref_slug": "Allsvenskan"},
    "Eliteserien": {"api_id": 103, "understat": "Eliteserien", "fbref_comp": "28", "fbref_slug": "Eliteserien"},
    "Ekstraklasa": {"api_id": 106, "understat": "Ekstraklasa", "fbref_comp": "36", "fbref_slug": "Ekstraklasa"},
    "Greek Super League": {"api_id": 197, "understat": "Greek", "fbref_comp": "27", "fbref_slug": "Greek-Super-League"},
    "Süper Lig": {"api_id": 203, "understat": "SuperLig", "fbref_comp": "26", "fbref_slug": "Super-Lig"},
    "Liga MX": {"api_id": 262, "understat": "Liga_MX", "fbref_comp": "22", "fbref_slug": "Liga-MX"},
    "Major League Soccer": {"api_id": 253, "understat": "MLS", "fbref_comp": "21", "fbref_slug": "Major-League-Soccer"},
    "Primera División Argentina": {"api_id": 128, "understat": "ARG", "fbref_comp": "19", "fbref_slug": "Primera-Division-Argentina"},
    "Primera División Chile": {"api_id": 265, "understat": "Chile", "fbref_comp": "56", "fbref_slug": "Primera-Division-Chile"},
    "Primera División Uruguay": {"api_id": 268, "understat": "Uruguay", "fbref_comp": "45", "fbref_slug": "Primera-Division-Uruguay"},
    "Categoría Primera A (Colombia)": {"api_id": 239, "understat": "Colombia", "fbref_comp": "58", "fbref_slug": "Categoria-Primera-A"},
    "Primera División Perú": {"api_id": 281, "understat": "Peru", "fbref_comp": "59", "fbref_slug": "Primera-Division-Peru"},
    "Primera División Paraguay": {"api_id": 250, "understat": "Paraguay", "fbref_comp": "60", "fbref_slug": "Primera-Division-Paraguay"},
    "Primera División Venezuela": {"api_id": 300, "understat": "Venezuela", "fbref_comp": "61", "fbref_slug": "Primera-Division-Venezuela"},
    "J1 League": {"api_id": 98, "understat": "J1", "fbref_comp": "25", "fbref_slug": "J1-League"},
    "K League 1": {"api_id": 292, "understat": "K1", "fbref_comp": "33", "fbref_slug": "K-League-1"},
    "A‑League": {"api_id": 188, "understat": "A-League", "fbref_comp": "30", "fbref_slug": "A-League"},
    "Saudi Pro League": {"api_id": 307, "understat": "Saudi", "fbref_comp": "41", "fbref_slug": "Saudi-Pro-League"},
    "Egyptian Premier League": {"api_id": 233, "understat": "Egypt", "fbref_comp": "62", "fbref_slug": "Egyptian-Premier-League"},
    "Indian Super League": {"api_id": 323, "understat": "ISL", "fbref_comp": "63", "fbref_slug": "Indian-Super-League"},
    "Liga 1 Indonesia": {"api_id": 274, "understat": "Indonesia", "fbref_comp": "64", "fbref_slug": "Liga-1-Indonesia"},
    "Liga Nacional Honduras": {"api_id": 264, "understat": "Honduras", "fbref_comp": "65", "fbref_slug": "Liga-Nacional-Honduras"},
    "Primera División El Salvador": {"api_id": 267, "understat": "El_Salvador", "fbref_comp": "66", "fbref_slug": "Primera-Division-El-Salvador"},
    "Costa Rica Primera División": {"api_id": 257, "understat": "Costa_Rica", "fbref_comp": "67", "fbref_slug": "Costa-Rica-Primera-Division"},
    "Liga Panameña de Fútbol": {"api_id": 296, "understat": "Panama", "fbref_comp": "68", "fbref_slug": "Liga-Panamena"},
    "Liga Dominicana de Fútbol": {"api_id": 311, "understat": "Dominicana", "fbref_comp": "69", "fbref_slug": "Liga-Dominicana"},
    "TT Pro League": {"api_id": 276, "understat": "Trinidad", "fbref_comp": "70", "fbref_slug": "TT-Pro-League"},
    "Jamaican Premier League": {"api_id": 273, "understat": "Jamaica", "fbref_comp": "71", "fbref_slug": "Jamaican-Premier-League"},
    "Ghana Premier League": {"api_id": 240, "understat": "Ghana", "fbref_comp": "72", "fbref_slug": "Ghana-Premier-League"},
    "South African Premier Division": {"api_id": 288, "understat": "South_Africa", "fbref_comp": "73", "fbref_slug": "South-African-Premier-Division"},
    "Moroccan Botola Pro": {"api_id": 200, "understat": "Morocco", "fbref_comp": "74", "fbref_slug": "Moroccan-Botola-Pro"},
}


# ============================================================
# Mapeamento manual de times → slug FBref (fallback)
# ============================================================
TIMES_FBREF_SLUG = {
    "Arsenal": "Arsenal",
    "Aston Villa": "Aston-Villa",
    "Bournemouth": "Bournemouth",
    "Brentford": "Brentford",
    "Brighton": "Brighton-and-Hove-Albion",
    "Chelsea": "Chelsea",
    "Crystal Palace": "Crystal-Palace",
    "Everton": "Everton",
    "Fulham": "Fulham",
    "Leeds United": "Leeds-United",
    "Leicester City": "Leicester-City",
    "Liverpool": "Liverpool",
    "Manchester City": "Manchester-City",
    "Manchester United": "Manchester-United",
    "Newcastle United": "Newcastle-United",
    "Nottingham Forest": "Nottingham-Forest",
    "Southampton": "Southampton",
    "Tottenham": "Tottenham-Hotspur",
    "West Ham": "West-Ham-United",
    "Wolverhampton": "Wolverhampton-Wanderers",
    "Flamengo": "Flamengo",
    "Palmeiras": "Palmeiras",
    "Corinthians": "Corinthians",
    "São Paulo": "Sao-Paulo",
}


# ============================================================
# Cache local
# ============================================================
def _cache_path(key: str, extension: str = "json") -> Path:
    hash_key = hashlib.md5(key.encode()).hexdigest()
    return CACHE_DIR / f"{hash_key}.{extension}"

def _cache_save(key: str, data, extension: str = "json"):
    path = _cache_path(key, extension)
    if extension == "json":
        with open(path, "w") as f:
            json.dump(data, f, default=str)
    elif extension == "csv":
        data.to_csv(path, index=False)
    meta_path = path.with_suffix(".meta")
    with open(meta_path, "w") as f:
        f.write(datetime.now().isoformat())

def _cache_load(key: str, ttl: timedelta = CACHE_TTL, extension: str = "json"):
    path = _cache_path(key, extension)
    if not path.exists():
        return None
    meta_path = path.with_suffix(".meta")
    if meta_path.exists():
        with open(meta_path) as f:
            ts_str = f.read().strip()
            if ts_str:
                ts = datetime.fromisoformat(ts_str)
                if datetime.now() - ts > ttl:
                    return None
    if extension == "json":
        with open(path) as f:
            return json.load(f)
    elif extension == "csv":
        return pd.read_csv(path)
    return None


# ============================================================
# API-Football (RapidAPI) – uso mínimo
# ============================================================
def _api_headers(api_key: str) -> dict:
    return {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

def _api_get(endpoint: str, params: dict, api_key: str) -> dict:
    url = f"https://api-football-v1.p.rapidapi.com/v3/{endpoint}"
    headers = _api_headers(api_key)
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()
    if data.get("errors"):
        raise Exception(f"API-Football errors: {data['errors']}")
    return data["response"]

def get_all_teams_from_league(league_id: int, season: int, api_key: str) -> Dict[str, int]:
    cache_key = f"api_teams_league_{league_id}_{season}"
    cached = _cache_load(cache_key)
    if cached:
        return cached
    response = _api_get("teams", {"league": league_id, "season": season}, api_key)
    teams_dict = {}
    for item in response:
        nome = item["team"]["name"]
        team_id = item["team"]["id"]
        teams_dict[nome] = team_id
    _cache_save(cache_key, teams_dict)
    return teams_dict

def get_team_stats_api(team_id: int, league_id: int, season: int, api_key: str) -> dict:
    cache_key = f"api_stats_{team_id}_{league_id}_{season}"
    cached = _cache_load(cache_key)
    if cached:
        return cached
    response = _api_get("teams/statistics", {
        "league": league_id,
        "season": season,
        "team": team_id
    }, api_key)
    stats = response
    fixtures = stats.get("fixtures", {})
    played = fixtures.get("played", {}).get("total", 0) or 0
    goals = stats.get("goals", {})
    cards = stats.get("cards", {})
    fouls = stats.get("fouls", {})
    shots = stats.get("shots", {})
    tackles = stats.get("tackles", {})
    dados = {
        "GM": goals.get("for", {}).get("average", {}).get("total", 0) or 0,
        "GS": goals.get("against", {}).get("average", {}).get("total", 0) or 0,
        "FA": shots.get("on", {}).get("average", {}).get("total", 0) or 0,
        "FAS": shots.get("on", {}).get("against", {}).get("average", {}).get("total", 0) or 0,
        "ECa": 0,
        "Poss": 0,
        "FC": fouls.get("average", {}).get("total", 0) or 0,
        "CA": cards.get("yellow", {}).get("average", {}).get("total", 0) or 0,
        "Tkl": tackles.get("average", {}).get("total", 0) or 0,
        "n_jogos": played,
    }
    _cache_save(cache_key, dados)
    return dados

def get_odds_api(fixture_id: int, api_key: str) -> Optional[dict]:
    try:
        resp = _api_get("odds", {"fixture": fixture_id}, api_key)
        if resp:
            bookmakers = resp[0].get("bookmakers", [])
            if bookmakers:
                bets = bookmakers[0].get("bets", [])
                odds = {}
                for bet in bets:
                    if bet["name"] == "Match Winner":
                        for odd in bet["values"]:
                            if odd["value"] == "Home":
                                odds["odd_casa"] = float(odd["odd"])
                            elif odd["value"] == "Draw":
                                odds["odd_empate"] = float(odd["odd"])
                            elif odd["value"] == "Away":
                                odds["odd_fora"] = float(odd["odd"])
                return odds
    except:
        pass
    return None

def get_home_away_pct(team_id: int, league_id: int, season: int, api_key: str) -> Tuple[float, float]:
    """Retorna (aproveitamento_casa, aproveitamento_fora) em % (0-100)."""
    fixtures = _api_get("fixtures", {
        "league": league_id,
        "season": season,
        "team": team_id,
        "status": "FT"
    }, api_key)
    home_pts = away_pts = home_j = away_j = 0
    for fx in fixtures:
        if fx["score"]["fulltime"]["home"] is None:
            continue
        is_home = fx["teams"]["home"]["id"] == team_id
        if is_home:
            home_j += 1
            if fx["score"]["fulltime"]["home"] > fx["score"]["fulltime"]["away"]:
                home_pts += 3
            elif fx["score"]["fulltime"]["home"] == fx["score"]["fulltime"]["away"]:
                home_pts += 1
        else:
            away_j += 1
            if fx["score"]["fulltime"]["away"] > fx["score"]["fulltime"]["home"]:
                away_pts += 3
            elif fx["score"]["fulltime"]["away"] == fx["score"]["fulltime"]["home"]:
                away_pts += 1
    home_pct = (home_pts / (3 * home_j) * 100) if home_j > 0 else 50.0
    away_pct = (away_pts / (3 * away_j) * 100) if away_j > 0 else 50.0
    return home_pct, away_pct
# ============================================================
# FBref scraping – tabelas, classificação, resultados, stats
# ============================================================
def _request_fbref(url: str, use_cache: bool = True) -> pd.DataFrame:
    cache_key = f"fbref_html_{url}"
    if use_cache:
        cached = _cache_load(cache_key, extension="csv")
        if cached is not None:
            return cached
    time.sleep(DELAY_FBREF)
    resp = requests.get(url, headers=HEADERS_FBREF)
    if resp.status_code == 429:
        print("Rate limit FBref, aguardando 60s...")
        time.sleep(60)
        resp = requests.get(url, headers=HEADERS_FBREF)
    resp.raise_for_status()
    tables = pd.read_html(resp.text, flavor='lxml')
    df = tables[0]
    if use_cache:
        _cache_save(cache_key, df, extension="csv")
    return df

def get_league_table_fbref(comp_slug: str, season: str) -> pd.DataFrame:
    url = f"https://fbref.com/en/comps/{comp_slug}/{season}/"
    return _request_fbref(url)

def get_standings_fbref(comp_slug: str, season: str) -> Dict[str, int]:
    df = get_league_table_fbref(comp_slug, season)
    standings = {}
    for _, row in df.iterrows():
        squad = row.get("Squad", "")
        rank = row.get("Rk", None)
        if squad and rank is not None:
            try:
                standings[squad.strip()] = int(rank)
            except:
                pass
    return standings

def get_team_links_from_league(comp_slug: str, season: str) -> Dict[str, str]:
    url = f"https://fbref.com/en/comps/{comp_slug}/{season}/"
    time.sleep(DELAY_FBREF)
    resp = requests.get(url, headers=HEADERS_FBREF)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    links = {}
    for a in soup.find_all("a", href=True):
        if "/squads/" in a["href"]:
            nome = a.text.strip()
            href = a["href"]
            links[nome] = href
    return links

def get_team_advanced_fbref(team_slug: str, season: str) -> dict:
    url = f"https://fbref.com/en/squads/{team_slug}/{season}/"
    try:
        time.sleep(DELAY_FBREF)
        resp = requests.get(url, headers=HEADERS_FBREF)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        dados = {}

        def extrair_tabela(tabela_id):
            table = soup.find("table", id=tabela_id)
            if table:
                df = pd.read_html(str(table))[0]
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [' '.join(col).strip() for col in df.columns.values]
                df = df[df["Player"] != "Player"]
                return df
            return None

        std = extrair_tabela("stats_standard_9")
        if std is not None:
            total_row = std[std["Player"] == "Squad Total"]
            if not total_row.empty:
                row = total_row.iloc[0]
                dados["Poss"] = float(row.get("Poss", 0))
                dados["Shots"] = float(row.get("Shots", 0))
                dados["SoT"] = float(row.get("SoT", 0))
                dados["CrdY"] = float(row.get("CrdY", 0))
                dados["Fls"] = float(row.get("Fls", 0))

        shoot = extrair_tabela("stats_shooting_9")
        if shoot is not None:
            total_row = shoot[shoot["Player"] == "Squad Total"]
            if not total_row.empty:
                row = total_row.iloc[0]
                dados["xG"] = float(row.get("xG", 0))
                dados["Gls"] = float(row.get("Gls", 0))

        pass_table = extrair_tabela("stats_passing_9")
        if pass_table is not None:
            total_row = pass_table[pass_table["Player"] == "Squad Total"]
            if not total_row.empty:
                row = total_row.iloc[0]
                dados["PrgP"] = float(row.get("PrgP", 0))
                dados["Crs"] = float(row.get("Crs", 0))
                dados["LongPass"] = float(row.get("Long", 0))
                dados["ShortPass"] = float(row.get("Short", 0))

        pass_types = extrair_tabela("stats_passing_types_9")
        if pass_types is not None:
            total_row = pass_types[pass_types["Player"] == "Squad Total"]
            if not total_row.empty:
                row = total_row.iloc[0]
                dados["ThrBall"] = float(row.get("TB", 0))

        poss_table = extrair_tabela("stats_possession_9")
        if poss_table is not None:
            total_row = poss_table[poss_table["Player"] == "Squad Total"]
            if not total_row.empty:
                row = total_row.iloc[0]
                dados["AttThird"] = float(row.get("Att 3rd", 0))

        def_table = extrair_tabela("stats_defense_9")
        if def_table is not None:
            total_row = def_table[def_table["Player"] == "Squad Total"]
            if not total_row.empty:
                row = total_row.iloc[0]
                dados["Int"] = float(row.get("Int", 0))
                dados["Tkl"] = float(row.get("Tkl", 0))

        for key in ["Poss", "Shots", "SoT", "xG", "PrgP", "Crs", "LongPass",
                    "ShortPass", "ThrBall", "AttThird", "Int", "Tkl", "CrdY", "Fls"]:
            if key not in dados:
                dados[key] = 0.0

        return dados
    except Exception as e:
        print(f"Erro ao buscar FBref para {team_slug}: {e}")
        return {}
        def get_recent_matches_fbref(team_slug: str, season: str, n: int = 10) -> List[str]:
    url = f"https://fbref.com/en/squads/{team_slug}/{season}/"
    try:
        time.sleep(DELAY_FBREF)
        resp = requests.get(url, headers=HEADERS_FBREF)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        table = soup.find("table", id="matchlogs_all")
        if not table:
            print("Tabela de resultados não encontrada.")
            return []
        df = pd.read_html(str(table))[0]
        resultados = []
        for _, row in df.iterrows():
            res = row.get("Result", "")
            if res == "W":
                resultados.append("V")
            elif res == "D":
                resultados.append("E")
            elif res == "L":
                resultados.append("D")
        resultados = resultados[::-1]  # cronológico
        return resultados[-n:]
    except Exception as e:
        print(f"Erro ao buscar resultados FBref: {e}")
        return []

def get_match_history_fbref(team_slug: str, season: str) -> List[dict]:
    """Retorna histórico completo com adversário, resultado e gols."""
    url = f"https://fbref.com/en/squads/{team_slug}/{season}/"
    time.sleep(DELAY_FBREF)
    resp = requests.get(url, headers=HEADERS_FBREF)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    table = soup.find("table", id="matchlogs_all")
    if not table:
        return []
    df = pd.read_html(str(table))[0]
    history = []
    for _, row in df.iterrows():
        res = row.get("Result", "")
        if res == "W":
            resultado = "V"
        elif res == "D":
            resultado = "E"
        elif res == "L":
            resultado = "D"
        else:
            continue
        adversario = row.get("Opponent", "")
        gf = row.get("GF", 0)
        ga = row.get("GA", 0)
        history.append({
            "resultado": resultado,
            "adversario": adversario,
            "gols_pro": gf,
            "gols_contra": ga
        })
    return history[::-1]

def get_league_averages_fbref(comp_slug: str, season: str) -> dict:
    df = get_league_table_fbref(comp_slug, season)
    medias = {}
    mapeamento = {
        'GM': 'Gls', 'FA': 'SoT', 'Poss': 'Poss', 'ECa': 'CK',
        'GS': 'GA', 'FAS': 'SoTA', 'Des': 'Tkl', 'FC': 'Fls',
        'CA': 'CrdY', 'Int': 'Int'
    }
    for nosso, col in mapeamento.items():
        if col in df.columns:
            vals = pd.to_numeric(df[df['Squad'] != 'Squad Total'][col], errors='coerce')
            medias[nosso] = vals.mean() if not vals.empty else 0.0
        else:
            medias[nosso] = 0.0
    if 'Sh' in df.columns:
        medias['TC'] = pd.to_numeric(df[df['Squad'] != 'Squad Total']['Sh'], errors='coerce').mean()
    else:
        medias['TC'] = 0.0
    return medias

# ============================================================
# Understat scraping
# ============================================================
def get_understat_team_xg(team_slug: str, league: str, season: int) -> dict:
    cache_key = f"understat_team_{team_slug}_{season}"
    cached = _cache_load(cache_key)
    if cached:
        return cached

    league_url = f"https://understat.com/league/{league}/{season}"
    time.sleep(DELAY_UNDERSTAT)
    resp = requests.get(league_url, headers=HEADERS_UNDERSTAT)
    resp.raise_for_status()
    json_match = re.search(r"var teamsData\s*=\s*JSON\.parse\('(.*?)'\)", resp.text)
    if json_match:
        json_str = json_match.group(1).encode().decode('unicode_escape')
        teams_data = json.loads(json_str)
        for name, stats in teams_data.items():
            if name.lower() == team_slug.lower():
                dados = {
                    "xG": float(stats.get("xG", 0)),
                    "xGA": float(stats.get("xGA", 0)),
                    "npxG": float(stats.get("npxG", 0)),
                    "npxGA": float(stats.get("npxGA", 0)),
                    "deep": float(stats.get("deep", 0)),
                    "ppda": float(stats.get("ppda", 0)),
                }
                _cache_save(cache_key, dados)
                return dados
    return {}

# ============================================================
# Função principal
# ============================================================
def carregar_dados_automaticos(
    time_casa: str,
    time_fora: str,
    liga: str,
    api_key: str,
    season: Optional[int] = None,
    usar_odds_api: bool = True
) -> dict:
    if liga not in LIGAS_MAP:
        raise ValueError(f"Liga '{liga}' não mapeada. Adicione em LIGAS_MAP.")

    league_info = LIGAS_MAP[liga]
    if season is None:
        current_season = datetime.now().year
        try:
            _ = get_all_teams_from_league(league_info["api_id"], current_season, api_key)
            season = current_season
        except:
            season = current_season - 1

    season_fbref = f"{season-1}-{season}"

    # 1. Lista de times da liga (1 crédito)
    times_liga = get_all_teams_from_league(league_info["api_id"], season, api_key)

    def find_team_id(name):
        if name in times_liga:
            return times_liga[name]
        for nome, tid in times_liga.items():
            if name.lower() in nome.lower():
                return tid
        raise ValueError(f"Time '{name}' não encontrado na liga '{liga}'.")

    id_casa = find_team_id(time_casa)
    id_fora = find_team_id(time_fora)

    # 2. Estatísticas da API (2 créditos)
    stats_casa = get_team_stats_api(id_casa, league_info["api_id"], season, api_key)
    stats_fora = get_team_stats_api(id_fora, league_info["api_id"], season, api_key)

    # 3. Aproveitamento casa/fora
    aprov_casa_casa, aprov_fora_casa = get_home_away_pct(id_casa, league_info["api_id"], season, api_key)
    aprov_casa_fora, aprov_fora_fora = get_home_away_pct(id_fora, league_info["api_id"], season, api_key)

    # 4. Scraping: classificação e resultados
    standings = get_standings_fbref(league_info["fbref_comp"], season_fbref)
    team_links = get_team_links_from_league(league_info["fbref_comp"], season_fbref)

    def get_team_slug(name):
        for tname, href in team_links.items():
            if name.lower() == tname.lower() or name.lower() in tname.lower():
                return href.split("/squads/")[1]
        return TIMES_FBREF_SLUG.get(name, name.replace(" ", "-"))

    slug_casa = get_team_slug(time_casa)
    slug_fora = get_team_slug(time_fora)

    res_casa_list = get_recent_matches_fbref(slug_casa, season_fbref, n=5)
    res_fora_list = get_recent_matches_fbref(slug_fora, season_fbref, n=5)
    res_casa = "".join(res_casa_list)
    res_fora = "".join(res_fora_list)

    cons_casa_list = get_recent_matches_fbref(slug_casa, season_fbref, n=10)
    cons_fora_list = get_recent_matches_fbref(slug_fora, season_fbref, n=10)
    cons_casa = "".join(cons_casa_list)
    cons_fora = "".join(cons_fora_list)

    def moral_from_list(lst):
        ult3 = lst[-3:] if len(lst) >= 3 else lst
        return sum(3 if r=="V" else 1 if r=="E" else 0 for r in ult3)

    moral_casa = moral_from_list(cons_casa_list)
    moral_fora = moral_from_list(cons_fora_list)

    pos_casa = standings.get(time_casa, 10)
    pos_fora = standings.get(time_fora, 10)

    # 5. CPP automático
    from src.metricas.cpp_v2 import classificar_prateleira, calcular_cpp_v2, construir_historico_prateleiras

    hist_casa_raw = get_match_history_fbref(slug_casa, season_fbref)
    hist_fora_raw = get_match_history_fbref(slug_fora, season_fbref)

    def build_cpp_history(history, standings_dict):
        cpp_hist = []
        for jogo in history:
            adv_name = jogo["adversario"]
            pos_adv = standings_dict.get(adv_name, 10)
            cpp_hist.append({
                "adversario": adv_name,
                "posicao_adversario": pos_adv,
                "resultado": jogo["resultado"],
                "gols_pro": jogo["gols_pro"],
                "gols_contra": jogo["gols_contra"]
            })
        return construir_historico_prateleiras(cpp_hist)

    hist_casa = build_cpp_history(hist_casa_raw, standings)
    hist_fora = build_cpp_history(hist_fora_raw, standings)

    prat_adv_casa = classificar_prateleira(pos_fora)
    prat_adv_fora = classificar_prateleira(pos_casa)

    prob_v_default = 0.4
    prob_e_default = 0.3
    calcular_cpp_v2(hist_casa, prat_adv_casa, prob_v_default, prob_e_default)
    calcular_cpp_v2(hist_fora, prat_adv_fora, prob_v_default, prob_e_default)

    dados_cpp_casa = hist_casa[prat_adv_casa]
    dados_cpp_fora = hist_fora[prat_adv_fora]
    pts_cpp_casa = dados_cpp_casa["pontos"]
    jogos_cpp_casa = dados_cpp_casa["jogos"]
    pts_cpp_fora = dados_cpp_fora["pontos"]
    jogos_cpp_fora = dados_cpp_fora["jogos"]

    # 6. Estatísticas avançadas (FBref + Understat)
    adv_casa = get_team_advanced_fbref(slug_casa, season_fbref)
    adv_fora = get_team_advanced_fbref(slug_fora, season_fbref)

    understat_league = league_info["understat"]
    understat_casa = get_understat_team_xg(slug_casa, understat_league, season)
    understat_fora = get_understat_team_xg(slug_fora, understat_league, season)

    dados_A = {**stats_casa, **adv_casa, **understat_casa}
    dados_B = {**stats_fora, **adv_fora, **understat_fora}

    # Métricas derivadas
    def efetividade(gm, shots):
        if shots and shots > 0:
            return (gm / shots) * 100
        return 0.0

    ef_casa = efetividade(stats_casa.get("GM", 1.0), dados_A.get("Shots", 10.0))
    ef_fora = efetividade(stats_fora.get("GM", 1.0), dados_B.get("Shots", 10.0))

    def transicao(prgp, poss, ef):
        return (prgp * 0.6 + max(0, 1 - poss/100) * 100 * 0.4) * (ef / 100)

    trans_casa = transicao(dados_A.get("PrgP", 10), dados_A.get("Poss", 50), ef_casa)
    trans_fora = transicao(dados_B.get("PrgP", 10), dados_B.get("Poss", 50), ef_fora)

    dados_A["Efetividade"] = ef_casa
    dados_A["Transicao"] = trans_casa
    dados_B["Efetividade"] = ef_fora
    dados_B["Transicao"] = trans_fora

    # Médias da liga
    medias_liga = get_league_averages_fbref(league_info["fbref_comp"], season_fbref)
    for k in ['GM','FA','ECa','Poss','GS','FAS','ECc','Des','FC','CA','Int','TC']:
        if k not in medias_liga:
            medias_liga[k] = 0.0

    # Odds (opcional)
    odds_dict = {
        "odd_casa": 1.8, "odd_empate": 3.5, "odd_fora": 4.0,
        "odd_over15": 1.2, "odd_over25": 1.8, "odd_over35": 2.5,
        "odd_btts_sim": 1.8, "odd_btts_nao": 1.9, "odd_ht": 1.5
    }
    if usar_odds_api:
        try:
            h2h = _api_get("fixtures", {
                "league": league_info["api_id"],
                "season": season,
                "h2h": f"{id_casa}-{id_fora}",
                "next": 1
            }, api_key)
            if h2h:
                fixture_id = h2h[0]["fixture"]["id"]
                api_odds = get_odds_api(fixture_id, api_key)
                if api_odds:
                    odds_dict.update(api_odds)
        except:
            pass

    # Montagem do dicionário final
    dados = {
        "nome_casa": time_casa,
        "nome_fora": time_fora,
        "n_casa": stats_casa.get("n_jogos", 10),
        "n_fora": stats_fora.get("n_jogos", 10),
        "gm_casa": stats_casa.get("GM", 1.4),
        "fa_casa": stats_casa.get("FA", 4.0),
        "eca_casa": stats_casa.get("ECa", 5.0),
        "posse_casa": dados_A.get("Poss", 50.0),
        "gs_casa": stats_casa.get("GS", 1.4),
        "fas_casa": stats_casa.get("FAS", 4.0),
        "des_casa": stats_casa.get("Tkl", 15.0),
        "fc_casa": stats_casa.get("FC", 12.0),
        "ca_casa": stats_casa.get("CA", 2.0),
        "gm_fora": stats_fora.get("GM", 1.4),
        "fa_fora": stats_fora.get("FA", 4.0),
        "eca_fora": stats_fora.get("ECa", 5.0),
        "posse_fora": dados_B.get("Poss", 50.0),
        "gs_fora": stats_fora.get("GS", 1.4),
        "fas_fora": stats_fora.get("FAS", 4.0),
        "des_fora": stats_fora.get("Tkl", 15.0),
        "fc_fora": stats_fora.get("FC", 12.0),
        "ca_fora": stats_fora.get("CA", 2.0),
        "res_casa": res_casa,
        "cons_casa": cons_casa,
        "moral_casa": moral_casa,
        "pos_casa": pos_casa,
        "pts_cpp_casa": pts_cpp_casa,
        "jogos_cpp_casa": jogos_cpp_casa,
        "res_fora": res_fora,
        "cons_fora": cons_fora,
        "moral_fora": moral_fora,
        "pos_fora": pos_fora,
        "pts_cpp_fora": pts_cpp_fora,
        "jogos_cpp_fora": jogos_cpp_fora,
        "prat_casa": prat_adv_casa,
        "prat_fora": prat_adv_fora,
        "medias_liga": medias_liga,
        "dados_A": dados_A,
        "dados_B": dados_B,
        "crs_casa": dados_A.get("Crs", 0),
        "thrball_casa": dados_A.get("ThrBall", 0),
        "shortpass_casa": dados_A.get("ShortPass", 0),
        "longball_casa": dados_A.get("LongPass", 0),
        "attthird_casa": dados_A.get("AttThird", 50),
        "crs_fora": dados_B.get("Crs", 0),
        "thrball_fora": dados_B.get("ThrBall", 0),
        "shortpass_fora": dados_B.get("ShortPass", 0),
        "longball_fora": dados_B.get("LongPass", 0),
        "attthird_fora": dados_B.get("AttThird", 50),
        "aprov_casa_casa": aprov_casa_casa,
        "aprov_fora_fora": aprov_fora_fora,
        "odd_casa": odds_dict["odd_casa"],
        "odd_empate": odds_dict["odd_empate"],
        "odd_fora": odds_dict["odd_fora"],
        "odd_over15": odds_dict["odd_over15"],
        "odd_over25": odds_dict["odd_over25"],
        "odd_over35": odds_dict["odd_over35"],
        "odd_btts_sim": odds_dict["odd_btts_sim"],
        "odd_btts_nao": odds_dict["odd_btts_nao"],
        "odd_ht": odds_dict["odd_ht"],
    }

    return dados
    def get_match_period_stats_fbref(match_url: str) -> Optional[pd.DataFrame]:
    """
    Faz scraping da página de uma partida no FBref e retorna estatísticas por período.
    Exemplo de URL: 'https://fbref.com/en/matches/abc123/2023-2024/TeamA-TeamB'
    """
    try:
        time.sleep(DELAY_FBREF)
        resp = requests.get(match_url, headers=HEADERS_FBREF)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        tables = soup.find_all("table")
        for table in tables:
            try:
                df = pd.read_html(str(table))[0]
                cols = [str(c) for c in df.columns]
                if any('1-15' in c or '16-30' in c or 'Statistic' in c for c in cols):
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = [' '.join(col).strip() for col in df.columns.values]
                    return df
            except:
                continue
        return None
    except Exception as e:
        print(f"Erro no scraping da partida: {e}")
        return None
