"""
data_loader.py — Coleta automática de dados (API‑Football + FBref + Understat)

Fornece a função carregar_dados_automaticos(), que retorna um dicionário
compatível com resultados.py, sem nenhuma dependência do WhoScored.

Regras de scraping:
  - FBref: delay mínimo 8s, User‑Agent identificado
  - Understat: delay 2s, User‑Agent realista
  - API‑Football: via RapidAPI (X‑RapidAPI‑Key)
"""

import os
import json
import time
import re
import hashlib
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

HEADERS_FBREF = {
    "User-Agent": "EngramScoreBot/1.0 (analytics@engramscore.com)"
}
HEADERS_UNDERSTAT = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

CACHE_TTL = timedelta(hours=6)

# ============================================================
# Mapeamento de ligas (exemplos – expanda conforme necessário)
# ============================================================
LIGAS_MAP = {
    "Premier League": {
        "api_id": 39,
        "understat": "EPL",
        "fbref_comp": "9",
        "fbref_slug": "Premier-League"
    },
    "La Liga": {
        "api_id": 140,
        "understat": "La_liga",
        "fbref_comp": "12",
        "fbref_slug": "La-Liga"
    },
    "Bundesliga": {
        "api_id": 78,
        "understat": "Bundesliga",
        "fbref_comp": "20",
        "fbref_slug": "Bundesliga"
    },
    "Serie A": {
        "api_id": 135,
        "understat": "Serie_A",
        "fbref_comp": "11",
        "fbref_slug": "Serie-A"
    },
    "Ligue 1": {
        "api_id": 61,
        "understat": "Ligue_1",
        "fbref_comp": "13",
        "fbref_slug": "Ligue-1"
    },
    "Brasileirão Série A": {
        "api_id": 71,
        "understat": "BRA",
        "fbref_comp": "24",
        "fbref_slug": "Campeonato-Brasileiro-Serie-A"
    },
}

# ============================================================
# Mapeamento de times → slug FBref (exemplos)
# ============================================================
TIMES_FBREF_SLUG = {
    # Inglaterra
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
    # Brasil
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
# API-Football (RapidAPI)
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

def get_team_by_name(team_name: str, league: str, api_key: str) -> dict:
    cache_key = f"api_team_{team_name}_{league}"
    cached = _cache_load(cache_key)
    if cached:
        return cached

    league_id = LIGAS_MAP[league]["api_id"]
    season = datetime.now().year
    try:
        teams = _api_get("teams", {"league": league_id, "season": season}, api_key)
    except:
        teams = _api_get("teams", {"search": team_name}, api_key)

    for t in teams:
        if t["team"]["name"].lower() == team_name.lower():
            _cache_save(cache_key, t["team"])
            return t["team"]
    for t in teams:
        if team_name.lower() in t["team"]["name"].lower():
            _cache_save(cache_key, t["team"])
            return t["team"]
    raise ValueError(f"Time '{team_name}' não encontrado na liga '{league}'.")

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
    passes_stats = stats.get("passes", {})
    tackles = stats.get("tackles", {})

    dados = {
        "GM": goals.get("for", {}).get("average", {}).get("total", 0) or 0,
        "GS": goals.get("against", {}).get("average", {}).get("total", 0) or 0,
        "FA": shots.get("on", {}).get("average", {}).get("total", 0) or 0,
        "FAS": shots.get("on", {}).get("against", {}).get("average", {}).get("total", 0) or 0,
        "ECa": 0,  # API não fornece escanteios diretamente
        "Poss": 0,  # Pode vir nulo; complementaremos com FBref
        "FC": fouls.get("average", {}).get("total", 0) or 0,
        "CA": cards.get("yellow", {}).get("average", {}).get("total", 0) or 0,
        "Tkl": tackles.get("average", {}).get("total", 0) or 0,
        "n_jogos": played,
    }
    _cache_save(cache_key, dados)
    return dados

def get_recent_matches(team_id: int, league_id: int, season: int, api_key: str, n: int = 10) -> List[dict]:
    cache_key = f"api_matches_{team_id}_{league_id}_{season}"
    cached = _cache_load(cache_key)
    if cached:
        return cached[-n:]

    all_fixtures = []
    response = _api_get("fixtures", {
        "league": league_id,
        "season": season,
        "team": team_id,
        "status": "FT"
    }, api_key)

    for fx in response:
        home = fx["teams"]["home"]["id"]
        away = fx["teams"]["away"]["id"]
        is_home = (home == team_id)
        opponent = away if is_home else home

        home_goals = fx["score"]["fulltime"]["home"]
        away_goals = fx["score"]["fulltime"]["away"]
        if home_goals is None or away_goals is None:
            continue

        if is_home:
            if home_goals > away_goals: res = "V"
            elif home_goals == away_goals: res = "E"
            else: res = "D"
        else:
            if away_goals > home_goals: res = "V"
            elif away_goals == home_goals: res = "E"
            else: res = "D"

        all_fixtures.append({
            "date": fx["fixture"]["date"],
            "resultado": res,
            "opponent_id": opponent,
            "is_home": is_home,
            "gols_pro": home_goals if is_home else away_goals,
            "gols_contra": away_goals if is_home else home_goals,
        })

    all_fixtures.sort(key=lambda x: x["date"])
    _cache_save(cache_key, all_fixtures)
    return all_fixtures[-n:]

def get_standings(league_id: int, season: int, api_key: str) -> dict:
    cache_key = f"api_standings_{league_id}_{season}"
    cached = _cache_load(cache_key)
    if cached:
        return cached

    response = _api_get("standings", {"league": league_id, "season": season}, api_key)
    standings = {}
    for league_data in response:
        for team in league_data["league"]["standings"][0]:
            team_id = team["team"]["id"]
            rank = team["rank"]
            standings[team_id] = rank
    _cache_save(cache_key, standings)
    return standings

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

# ============================================================
# FBref scraping
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
        season = datetime.now().year

    # 1. IDs dos times
    team_casa_info = get_team_by_name(time_casa, liga, api_key)
    team_fora_info = get_team_by_name(time_fora, liga, api_key)
    id_casa = team_casa_info["id"]
    id_fora = team_fora_info["id"]

    # 2. Estatísticas básicas
    stats_casa = get_team_stats_api(id_casa, league_info["api_id"], season, api_key)
    stats_fora = get_team_stats_api(id_fora, league_info["api_id"], season, api_key)

    # 3. Resultados recentes
    recent_casa = get_recent_matches(id_casa, league_info["api_id"], season, api_key, n=10)
    recent_fora = get_recent_matches(id_fora, league_info["api_id"], season, api_key, n=10)

    def resultados_to_string(matches, n=5):
        return "".join([m["resultado"] for m in matches[-n:]])

    res_casa = resultados_to_string(recent_casa, 5)
    res_fora = resultados_to_string(recent_fora, 5)
    cons_casa = resultados_to_string(recent_casa, 10)
    cons_fora = resultados_to_string(recent_fora, 10)

    def moral_3(matches):
        ult3 = matches[-3:]
        return sum(3 if m["resultado"]=="V" else 1 if m["resultado"]=="E" else 0 for m in ult3)

    moral_casa = moral_3(recent_casa)
    moral_fora = moral_3(recent_fora)

    # 4. Posições
    standings = get_standings(league_info["api_id"], season, api_key)
    pos_casa = standings.get(id_casa, 10)
    pos_fora = standings.get(id_fora, 10)

    # 5. CPP automático
    from src.metricas.cpp_v2 import classificar_prateleira, calcular_cpp_v2, construir_historico_prateleiras

    all_matches_casa = get_recent_matches(id_casa, league_info["api_id"], season, api_key, n=100)
    all_matches_fora = get_recent_matches(id_fora, league_info["api_id"], season, api_key, n=100)

    def construir_historico(matches, standings_dict):
        hist = []
        for m in matches:
            pos_adv = standings_dict.get(m["opponent_id"], 10)
            hist.append({
                "adversario": str(m["opponent_id"]),
                "posicao_adversario": pos_adv,
                "resultado": m["resultado"],
                "gols_pro": m["gols_pro"],
                "gols_contra": m["gols_contra"]
            })
        return construir_historico_prateleiras(hist)

    hist_casa = construir_historico(all_matches_casa, standings)
    hist_fora = construir_historico(all_matches_fora, standings)

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

    # 6. FBref avançado
    fbref_comp = league_info["fbref_comp"]
    season_fbref = f"{season-1}-{season}"
    league_url = f"https://fbref.com/en/comps/{fbref_comp}/{season_fbref}/"
    time.sleep(DELAY_FBREF)
    resp = requests.get(league_url, headers=HEADERS_FBREF)
    soup = BeautifulSoup(resp.text, "lxml")
    squad_links = {}
    for a in soup.find_all("a", href=True):
        if "/squads/" in a["href"]:
            squad_links[a.text.strip()] = a["href"]

    def get_team_link(team_name):
        for name, href in squad_links.items():
            if team_name.lower() in name.lower():
                return href
        return None

    link_casa = get_team_link(time_casa)
    link_fora = get_team_link(time_fora)

    adv_casa = {}
    adv_fora = {}
    if link_casa:
        team_slug = link_casa.split("/squads/")[1]
        adv_casa = get_team_advanced_fbref(team_slug, season_fbref)
    if link_fora:
        team_slug = link_fora.split("/squads/")[1]
        adv_fora = get_team_advanced_fbref(team_slug, season_fbref)

    # 7. Mesclar dados
    dados_A = {**stats_casa, **adv_casa}
    dados_B = {**stats_fora, **adv_fora}

    # 8. Métricas derivadas
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

    # 9. Médias da liga
    medias_liga = get_league_averages_fbref(fbref_comp, season_fbref)
    for k in ['GM','FA','ECa','Poss','GS','FAS','ECc','Des','FC','CA','Int','TC']:
        if k not in medias_liga:
            medias_liga[k] = 0.0

    # 10. Odds
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

    # 11. Dicionário final
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
