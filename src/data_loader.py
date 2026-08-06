"""
data_loader.py – Coleta de dados via Selenium (FBref) + requests (Understat, Soccerway, Soccerstats)
Usa navegador Chrome visível (não headless) para contornar Cloudflare.
Cache de 7 dias. Suporte a ligas anuais (Brasileirão) e europeias.
"""

import os, json, time, re, hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Selenium imports
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# ============================================================
# Configurações gerais
# ============================================================
CACHE_DIR = Path("data")
CACHE_DIR.mkdir(exist_ok=True)
DELAY_FBREF = 10
DELAY_UNDERSTAT = 2
DELAY_SOCCER = 5

HEADERS_UNDERSTAT = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"}
HEADERS_SOCCER = {"User-Agent": "Mozilla/5.0 (compatible; EngramScoreBot/1.0)"}
CACHE_TTL = timedelta(days=7)

# Liga: understat, fbref_comp, fbref_slug, temporada_anual (True para ligas de ano civil)
LIGAS_MAP = {
    "Premier League": {"understat": "EPL", "fbref_comp": "9", "fbref_slug": "Premier-League", "temporada_anual": False},
    "La Liga": {"understat": "La_liga", "fbref_comp": "12", "fbref_slug": "La-Liga", "temporada_anual": False},
    "Bundesliga": {"understat": "Bundesliga", "fbref_comp": "20", "fbref_slug": "Bundesliga", "temporada_anual": False},
    "Serie A": {"understat": "Serie_A", "fbref_comp": "11", "fbref_slug": "Serie-A", "temporada_anual": False},
    "Ligue 1": {"understat": "Ligue_1", "fbref_comp": "13", "fbref_slug": "Ligue-1", "temporada_anual": False},
    "Brasileirão Série A": {"understat": "BRA", "fbref_comp": "24", "fbref_slug": "Campeonato-Brasileiro-Serie-A", "temporada_anual": True},
}

TIMES_FBREF_SLUG = {
    "Arsenal": "Arsenal", "Chelsea": "Chelsea", "Liverpool": "Liverpool",
    "Manchester City": "Manchester-City", "Manchester United": "Manchester-United",
    "Flamengo": "Flamengo", "Palmeiras": "Palmeiras", "Corinthians": "Corinthians",
    "São Paulo": "Sao-Paulo",
}

def _cache_path(key, extension="json"):
    hash_key = hashlib.md5(key.encode()).hexdigest()
    return CACHE_DIR / f"{hash_key}.{extension}"

def _cache_save(key, data, extension="json"):
    path = _cache_path(key, extension)
    if extension == "json":
        with open(path, "w") as f: json.dump(data, f, default=str)
    elif extension == "csv":
        data.to_csv(path, index=False)
    (path.with_suffix(".meta")).write_text(datetime.now().isoformat())

def _cache_load(key, ttl=CACHE_TTL, extension="json"):
    path = _cache_path(key, extension)
    if not path.exists(): return None
    meta = path.with_suffix(".meta")
    if meta.exists():
        if datetime.now() - datetime.fromisoformat(meta.read_text().strip()) > ttl:
            return None
    if extension == "json":
        return json.loads(path.read_text())
    return pd.read_csv(path)

# ============================================================
# Selenium (FBref)
# ============================================================
def _get_page(url):
    """Usa Selenium com navegador visível para contornar Cloudflare."""
    options = uc.ChromeOptions()
    # Modo visível (não headless) para máxima compatibilidade
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = uc.Chrome(options=options)
    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        time.sleep(5)  # pequena pausa para garantir carregamento total
        html = driver.page_source
        return html
    finally:
        driver.quit()

def _request_fbref(url, use_cache=True):
    cache_key = f"fbref_html_{url}"
    if use_cache:
        cached = _cache_load(cache_key, extension="csv")
        if cached is not None: return cached
    html = _get_page(url)
    df = pd.read_html(html, flavor='lxml')[0]
    if use_cache: _cache_save(cache_key, df, extension="csv")
    return df

def _request_fbref_soup(url):
    html = _get_page(url)
    return BeautifulSoup(html, "lxml")

# ============================================================
# FBref scraping
# ============================================================
def get_league_table_fbref(comp_slug, season_str):
    url = f"https://fbref.com/en/comps/{comp_slug}/{season_str}/"
    return _request_fbref(url)

def get_standings_fbref(comp_slug, season_str):
    df = get_league_table_fbref(comp_slug, season_str)
    standings = {}
    for _, row in df.iterrows():
        squad = row.get("Squad", "")
        rank = row.get("Rk", None)
        if squad and rank is not None:
            try: standings[squad.strip()] = int(rank)
            except: pass
    return standings

def get_team_links_from_league(comp_slug, season_str):
    url = f"https://fbref.com/en/comps/{comp_slug}/{season_str}/"
    soup = _request_fbref_soup(url)
    links = {}
    for a in soup.find_all("a", href=True):
        if "/squads/" in a["href"]:
            links[a.text.strip()] = a["href"]
    return links

def get_team_advanced_fbref(team_slug, season_str):
    url = f"https://fbref.com/en/squads/{team_slug}/{season_str}/"
    try:
        soup = _request_fbref_soup(url)
        dados = {}

        def extrair_tabela(tabela_id):
            table = soup.find("table", id=tabela_id)
            if not table: return None
            df = pd.read_html(str(table))[0]
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [' '.join(col).strip() for col in df.columns.values]
            df = df[df["Player"] != "Player"]
            return df

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
                dados["Gls"] = float(row.get("Gls", 0))
                dados["GA"] = float(row.get("GA", 0))
                dados["SoTA"] = float(row.get("SoTA", 0)) if "SoTA" in row else 0.0

        shoot = extrair_tabela("stats_shooting_9")
        if shoot is not None:
            total_row = shoot[shoot["Player"] == "Squad Total"]
            if not total_row.empty:
                row = total_row.iloc[0]
                dados["xG"] = float(row.get("xG", 0))

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
                    "ShortPass", "ThrBall", "AttThird", "Int", "Tkl", "CrdY", "Fls",
                    "Gls", "GA", "SoTA"]:
            if key not in dados:
                dados[key] = 0.0

        return dados
    except Exception as e:
        print(f"Erro ao buscar FBref para {team_slug}: {e}")
        return {}

def get_recent_matches_fbref(team_slug, season_str, n=10):
    url = f"https://fbref.com/en/squads/{team_slug}/{season_str}/"
    try:
        soup = _request_fbref_soup(url)
        table = soup.find("table", id="matchlogs_all")
        if not table: return []
        df = pd.read_html(str(table))[0]
        resultados = []
        for _, row in df.iterrows():
            res = row.get("Result", "")
            if res == "W": resultados.append("V")
            elif res == "D": resultados.append("E")
            elif res == "L": resultados.append("D")
        return resultados[::-1][-n:]
    except Exception as e:
        print(f"Erro ao buscar resultados FBref: {e}")
        return []

def get_match_history_fbref(team_slug, season_str):
    url = f"https://fbref.com/en/squads/{team_slug}/{season_str}/"
    soup = _request_fbref_soup(url)
    table = soup.find("table", id="matchlogs_all")
    if not table: return []
    df = pd.read_html(str(table))[0]
    history = []
    for _, row in df.iterrows():
        res = row.get("Result", "")
        if res == "W": resultado = "V"
        elif res == "D": resultado = "E"
        elif res == "L": resultado = "D"
        else: continue
        adversario = row.get("Opponent", "")
        gf = row.get("GF", 0)
        ga = row.get("GA", 0)
        venue = row.get("Venue", "")
        is_home = "Home" in str(venue)
        history.append({
            "resultado": resultado,
            "adversario": adversario,
            "gols_pro": gf,
            "gols_contra": ga,
            "is_home": is_home
        })
    return history[::-1]

def get_league_averages_fbref(comp_slug, season_str):
    df = get_league_table_fbref(comp_slug, season_str)
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

# Understat, Soccerway, Soccerstats (requests normais)
def get_understat_team_xg(team_slug, league, season):
    cache_key = f"understat_team_{team_slug}_{season}"
    cached = _cache_load(cache_key)
    if cached: return cached
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

def get_soccerway_match_stats(match_url):
    try:
        time.sleep(DELAY_SOCCER)
        resp = requests.get(match_url, headers=HEADERS_SOCCER)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        table = soup.find("table", class_="stats")
        if not table: return None
        stats = {}
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) == 3:
                label = cells[0].text.strip().lower()
                home = cells[1].text.strip()
                away = cells[2].text.strip()
                try:
                    home_val = float(home.replace('%', ''))
                    away_val = float(away.replace('%', ''))
                except: continue
                if "posse" in label:
                    stats["posse_casa"] = home_val
                    stats["posse_fora"] = away_val
                elif "chutes" in label and "a gol" not in label:
                    stats["chutes_casa"] = home_val
                    stats["chutes_fora"] = away_val
                elif "chutes a gol" in label:
                    stats["chutes_gol_casa"] = home_val
                    stats["chutes_gol_fora"] = away_val
                elif "escanteios" in label:
                    stats["escanteios_casa"] = home_val
                    stats["escanteios_fora"] = away_val
                elif "faltas" in label:
                    stats["faltas_casa"] = home_val
                    stats["faltas_fora"] = away_val
                elif "cartões amarelos" in label:
                    stats["cartoes_amarelos_casa"] = home_val
                    stats["cartoes_amarelos_fora"] = away_val
                elif "cartões vermelhos" in label:
                    stats["cartoes_vermelhos_casa"] = home_val
                    stats["cartoes_vermelhos_fora"] = away_val
        return stats
    except Exception as e:
        print(f"Erro ao buscar Soccerway: {e}")
        return None

def get_soccerstats_league_trends(league_name):
    try:
        time.sleep(DELAY_SOCCER)
        url = f"https://www.soccerstats.com/trends.asp?league={league_name}"
        resp = requests.get(url, headers=HEADERS_SOCCER)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        dados = {}
        avg_goals = soup.find(string=re.compile(r"Avg goals / match", re.I))
        if avg_goals:
            parts = avg_goals.split()
            for i, p in enumerate(parts):
                if "avg" in p.lower():
                    try: dados["media_gols"] = float(parts[i+1])
                    except: pass
        btts_text = soup.find(string=re.compile(r"Both teams scored", re.I))
        if btts_text:
            percent = re.search(r"(\d+\.?\d*)%", btts_text)
            if percent: dados["btts_pct"] = float(percent.group(1))
        over_text = soup.find(string=re.compile(r"Over 2\.5 goals", re.I))
        if over_text:
            percent = re.search(r"(\d+\.?\d*)%", over_text)
            if percent: dados["over25_pct"] = float(percent.group(1))
        under_text = soup.find(string=re.compile(r"Under 2\.5 goals", re.I))
        if under_text:
            percent = re.search(r"(\d+\.?\d*)%", under_text)
            if percent: dados["under25_pct"] = float(percent.group(1))
        return dados if dados else None
    except Exception as e:
        print(f"Erro ao buscar Soccerstats: {e}")
        return None

def carregar_dados_automaticos(time_casa, time_fora, liga, season=None, usar_soccerstats=False):
    if liga not in LIGAS_MAP:
        raise ValueError(f"Liga '{liga}' não mapeada.")
    info = LIGAS_MAP[liga]
    temporada_anual = info.get("temporada_anual", False)

    # Determinar a string da temporada para FBref
    current_year = datetime.now().year
    if season is not None:
        if temporada_anual:
            season_str = str(season)
        else:
            season_str = f"{season-1}-{season}"
    else:
        if temporada_anual:
            season_str = str(current_year)
            test_url = f"https://fbref.com/en/comps/{info['fbref_comp']}/{season_str}/"
            try:
                resp = requests.get(test_url, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code != 200:
                    season_str = str(current_year - 1)
            except:
                season_str = str(current_year - 1)
        else:
            season_str = f"{current_year-1}-{current_year}"
            test_url = f"https://fbref.com/en/comps/{info['fbref_comp']}/{season_str}/"
            try:
                resp = requests.get(test_url, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code != 200:
                    season_str = f"{current_year-2}-{current_year-1}"
            except:
                season_str = f"{current_year-2}-{current_year-1}"

    standings = get_standings_fbref(info["fbref_comp"], season_str)
    lista_times = list(standings.keys())

    if time_casa not in lista_times or time_fora not in lista_times:
        raise ValueError("Time não encontrado na liga. Verifique o nome.")

    pos_casa = standings[time_casa]
    pos_fora = standings[time_fora]

    team_links = get_team_links_from_league(info["fbref_comp"], season_str)
    def get_team_slug(name):
        for tname, href in team_links.items():
            if name.lower() == tname.lower() or name.lower() in tname.lower():
                return href.split("/squads/")[1]
        return TIMES_FBREF_SLUG.get(name, name.replace(" ", "-"))

    slug_casa = get_team_slug(time_casa)
    slug_fora = get_team_slug(time_fora)

    adv_casa = get_team_advanced_fbref(slug_casa, season_str)
    adv_fora = get_team_advanced_fbref(slug_fora, season_str)

    res_casa_list = get_recent_matches_fbref(slug_casa, season_str, n=5)
    res_fora_list = get_recent_matches_fbref(slug_fora, season_str, n=5)
    res_casa = "".join(res_casa_list)
    res_fora = "".join(res_fora_list)

    cons_casa_list = get_recent_matches_fbref(slug_casa, season_str, n=10)
    cons_fora_list = get_recent_matches_fbref(slug_fora, season_str, n=10)
    cons_casa = "".join(cons_casa_list)
    cons_fora = "".join(cons_fora_list)

    def moral_from_list(lst):
        ult3 = lst[-3:] if len(lst) >= 3 else lst
        return sum(3 if r=="V" else 1 if r=="E" else 0 for r in ult3)

    moral_casa = moral_from_list(cons_casa_list)
    moral_fora = moral_from_list(cons_fora_list)

    hist_casa_raw = get_match_history_fbref(slug_casa, season_str)
    hist_fora_raw = get_match_history_fbref(slug_fora, season_str)

    def calc_home_away(history):
        home_pts = away_pts = home_j = away_j = 0
        for jogo in history:
            if jogo["is_home"]:
                home_j += 1
                if jogo["resultado"] == "V": home_pts += 3
                elif jogo["resultado"] == "E": home_pts += 1
            else:
                away_j += 1
                if jogo["resultado"] == "V": away_pts += 3
                elif jogo["resultado"] == "E": away_pts += 1
        home_pct = (home_pts / (3 * home_j) * 100) if home_j > 0 else 50.0
        away_pct = (away_pts / (3 * away_j) * 100) if away_j > 0 else 50.0
        return home_pct, away_pct

    aprov_casa_casa, _ = calc_home_away(hist_casa_raw)
    _, aprov_fora_fora = calc_home_away(hist_fora_raw)

    from src.metricas.cpp_v2 import classificar_prateleira, calcular_cpp_v2, construir_historico_prateleiras

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

    prob_v_default, prob_e_default = 0.4, 0.3
    calcular_cpp_v2(hist_casa, prat_adv_casa, prob_v_default, prob_e_default)
    calcular_cpp_v2(hist_fora, prat_adv_fora, prob_v_default, prob_e_default)

    dados_cpp_casa = hist_casa[prat_adv_casa]
    dados_cpp_fora = hist_fora[prat_adv_fora]
    pts_cpp_casa = dados_cpp_casa["pontos"]
    jogos_cpp_casa = dados_cpp_casa["jogos"]
    pts_cpp_fora = dados_cpp_fora["pontos"]
    jogos_cpp_fora = dados_cpp_fora["jogos"]

    if temporada_anual:
        understat_season = int(season_str)
    else:
        understat_season = int(season_str[:4]) + 1
    understat_casa = get_understat_team_xg(slug_casa, info["understat"], understat_season)
    understat_fora = get_understat_team_xg(slug_fora, info["understat"], understat_season)

    dados_A = {**adv_casa, **understat_casa}
    dados_B = {**adv_fora, **understat_fora}

    def efetividade(gm, shots):
        if shots and shots > 0: return (gm / shots) * 100
        return 0.0
    ef_casa = efetividade(adv_casa.get("Gls", 1.0), adv_casa.get("Shots", 10.0))
    ef_fora = efetividade(adv_fora.get("Gls", 1.0), adv_fora.get("Shots", 10.0))

    def transicao(prgp, poss, ef):
        return (prgp * 0.6 + max(0, 1 - poss/100) * 100 * 0.4) * (ef / 100)
    trans_casa = transicao(dados_A.get("PrgP", 10), dados_A.get("Poss", 50), ef_casa)
    trans_fora = transicao(dados_B.get("PrgP", 10), dados_B.get("Poss", 50), ef_fora)

    dados_A["Efetividade"] = ef_casa
    dados_A["Transicao"] = trans_casa
    dados_B["Efetividade"] = ef_fora
    dados_B["Transicao"] = trans_fora

    medias_liga = get_league_averages_fbref(info["fbref_comp"], season_str)

    if usar_soccerstats:
        league_name_soccerstats = info.get("soccerstats", None)
        if league_name_soccerstats:
            trend = get_soccerstats_league_trends(league_name_soccerstats)
            if trend:
                if "media_gols" in trend: medias_liga["media_gols_real"] = trend["media_gols"]
                if "btts_pct" in trend: medias_liga["btts_pct"] = trend["btts_pct"]
                if "over25_pct" in trend: medias_liga["over25_pct"] = trend["over25_pct"]

    for k in ['GM','FA','ECa','Poss','GS','FAS','ECc','Des','FC','CA','Int','TC']:
        if k not in medias_liga: medias_liga[k] = 0.0

    odds_dict = {
        "odd_casa": 1.8, "odd_empate": 3.5, "odd_fora": 4.0,
        "odd_over15": 1.2, "odd_over25": 1.8, "odd_over35": 2.5,
        "odd_btts_sim": 1.8, "odd_btts_nao": 1.9, "odd_ht": 1.5
    }

    return {
        "nome_casa": time_casa, "nome_fora": time_fora,
        "n_casa": len(hist_casa_raw), "n_fora": len(hist_fora_raw),
        "gm_casa": adv_casa.get("Gls", 1.4), "fa_casa": adv_casa.get("SoT", 4.0),
        "eca_casa": 5.0, "posse_casa": adv_casa.get("Poss", 50.0),
        "gs_casa": adv_casa.get("GA", 1.4), "fas_casa": adv_casa.get("SoTA", 4.0),
        "des_casa": adv_casa.get("Tkl", 15.0), "fc_casa": adv_casa.get("Fls", 12.0),
        "ca_casa": adv_casa.get("CrdY", 2.0),
        "gm_fora": adv_fora.get("Gls", 1.4), "fa_fora": adv_fora.get("SoT", 4.0),
        "eca_fora": 5.0, "posse_fora": adv_fora.get("Poss", 50.0),
        "gs_fora": adv_fora.get("GA", 1.4), "fas_fora": adv_fora.get("SoTA", 4.0),
        "des_fora": adv_fora.get("Tkl", 15.0), "fc_fora": adv_fora.get("Fls", 12.0),
        "ca_fora": adv_fora.get("CrdY", 2.0),
        "res_casa": res_casa, "cons_casa": cons_casa, "moral_casa": moral_casa,
        "pos_casa": pos_casa, "pts_cpp_casa": pts_cpp_casa, "jogos_cpp_casa": jogos_cpp_casa,
        "res_fora": res_fora, "cons_fora": cons_fora, "moral_fora": moral_fora,
        "pos_fora": pos_fora, "pts_cpp_fora": pts_cpp_fora, "jogos_cpp_fora": jogos_cpp_fora,
        "prat_casa": prat_adv_casa, "prat_fora": prat_adv_fora,
        "medias_liga": medias_liga, "dados_A": dados_A, "dados_B": dados_B,
        "crs_casa": adv_casa.get("Crs", 0), "thrball_casa": adv_casa.get("ThrBall", 0),
        "shortpass_casa": adv_casa.get("ShortPass", 0), "longball_casa": adv_casa.get("LongPass", 0),
        "attthird_casa": adv_casa.get("AttThird", 50),
        "crs_fora": adv_fora.get("Crs", 0), "thrball_fora": adv_fora.get("ThrBall", 0),
        "shortpass_fora": adv_fora.get("ShortPass", 0), "longball_fora": adv_fora.get("LongPass", 0),
        "attthird_fora": adv_fora.get("AttThird", 50),
        "aprov_casa_casa": aprov_casa_casa, "aprov_fora_fora": aprov_fora_fora,
        "odd_casa": odds_dict["odd_casa"], "odd_empate": odds_dict["odd_empate"],
        "odd_fora": odds_dict["odd_fora"], "odd_over15": odds_dict["odd_over15"],
        "odd_over25": odds_dict["odd_over25"], "odd_over35": odds_dict["odd_over35"],
        "odd_btts_sim": odds_dict["odd_btts_sim"], "odd_btts_nao": odds_dict["odd_btts_nao"],
        "odd_ht": odds_dict["odd_ht"],
    }

def get_match_period_stats_fbref(match_url):
    try:
        soup = _request_fbref_soup(match_url)
        tables = soup.find_all("table")
        for table in tables:
            try:
                df = pd.read_html(str(table))[0]
                cols = [str(c) for c in df.columns]
                if any('1-15' in c or '16-30' in c or 'Statistic' in c for c in cols):
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = [' '.join(col).strip() for col in df.columns.values]
                    return df
            except: continue
        return None
    except Exception as e:
        print(f"Erro no scraping da partida: {e}")
        return None
