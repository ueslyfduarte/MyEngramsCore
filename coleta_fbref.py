"""
coleta_fbref.py — Coleta de estatísticas do FBref

Roda no PC Linux (não no Streamlit Cloud).
Coleta médias da liga e estatísticas de todos os times.

Como usar:
    python3 coleta_fbref.py

O que ele faz:
    1. Acessa a página da liga no FBref
    2. Extrai a tabela de estatísticas por time
    3. Extrai médias da liga
    4. Salva tudo em CSV na pasta dados/
"""

import requests
import pandas as pd
import time
import random
import os
from datetime import datetime

# ========== CONFIGURAÇÕES ==========
DELAY = 10  # segundos entre requisições (seguro para não ser bloqueado)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/119.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/17.1",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
]

# ========== 50 LIGAS ==========
LIGAS = {
    # ===== TOP 5 EUROPA =====
    "premier_league": {
        "nome": "Premier League",
        "url": "https://fbref.com/en/comps/9/Premier-League-Stats",
        "total_times": 20,
    },
    "la_liga": {
        "nome": "La Liga",
        "url": "https://fbref.com/en/comps/12/La-Liga-Stats",
        "total_times": 20,
    },
    "bundesliga": {
        "nome": "Bundesliga",
        "url": "https://fbref.com/en/comps/20/Bundesliga-Stats",
        "total_times": 18,
    },
    "serie_a": {
        "nome": "Serie A",
        "url": "https://fbref.com/en/comps/11/Serie-A-Stats",
        "total_times": 20,
    },
    "ligue_1": {
        "nome": "Ligue 1",
        "url": "https://fbref.com/en/comps/13/Ligue-1-Stats",
        "total_times": 18,
    },

    # ===== SEGUNDAS DIVISÕES EUROPA =====
    "championship": {
        "nome": "EFL Championship",
        "url": "https://fbref.com/en/comps/10/Championship-Stats",
        "total_times": 24,
    },
    "bundesliga_2": {
        "nome": "2. Bundesliga",
        "url": "https://fbref.com/en/comps/33/2-Bundesliga-Stats",
        "total_times": 18,
    },
    "serie_b": {
        "nome": "Serie B",
        "url": "https://fbref.com/en/comps/18/Serie-B-Stats",
        "total_times": 20,
    },
    "ligue_2": {
        "nome": "Ligue 2",
        "url": "https://fbref.com/en/comps/60/Ligue-2-Stats",
        "total_times": 20,
    },
    "la_liga_2": {
        "nome": "La Liga 2",
        "url": "https://fbref.com/en/comps/17/Segunda-Division-Stats",
        "total_times": 22,
    },

    # ===== AMÉRICAS =====
    "brasileirao_serie_a": {
        "nome": "Brasileirão Série A",
        "url": "https://fbref.com/en/comps/24/Serie-A-Stats",
        "total_times": 20,
    },
    "brasileirao_serie_b": {
        "nome": "Brasileirão Série B",
        "url": "https://fbref.com/en/comps/38/Serie-B-Stats",
        "total_times": 20,
    },
    "mls": {
        "nome": "Major League Soccer",
        "url": "https://fbref.com/en/comps/22/Major-League-Soccer-Stats",
        "total_times": 29,
    },
    "liga_mx": {
        "nome": "Liga MX",
        "url": "https://fbref.com/en/comps/31/Liga-MX-Stats",
        "total_times": 18,
    },
    "primera_division_argentina": {
        "nome": "Primera División Argentina",
        "url": "https://fbref.com/en/comps/21/Primera-Division-Stats",
        "total_times": 28,
    },

    # ===== OUTRAS LIGAS EUROPEIAS =====
    "eredivisie": {
        "nome": "Eredivisie",
        "url": "https://fbref.com/en/comps/23/Eredivisie-Stats",
        "total_times": 18,
    },
    "liga_portugal": {
        "nome": "Liga Portugal",
        "url": "https://fbref.com/en/comps/32/Primeira-Liga-Stats",
        "total_times": 18,
    },
    "super_lig_turquia": {
        "nome": "Süper Lig",
        "url": "https://fbref.com/en/comps/26/Super-Lig-Stats",
        "total_times": 19,
    },
    "jupiler_pro_league": {
        "nome": "Jupiler Pro League (Bélgica)",
        "url": "https://fbref.com/en/comps/37/Belgian-Pro-League-Stats",
        "total_times": 16,
    },
    "superliga_grecia": {
        "nome": "Super League Greece",
        "url": "https://fbref.com/en/comps/27/Super-League-Greece-Stats",
        "total_times": 14,
    },
    "russian_premier_league": {
        "nome": "Russian Premier League",
        "url": "https://fbref.com/en/comps/30/Russian-Premier-League-Stats",
        "total_times": 16,
    },
    "austrian_bundesliga": {
        "nome": "Austrian Bundesliga",
        "url": "https://fbref.com/en/comps/56/Austrian-Bundesliga-Stats",
        "total_times": 12,
    },
    "super_liga_suica": {
        "nome": "Swiss Super League",
        "url": "https://fbref.com/en/comps/58/Swiss-Super-League-Stats",
        "total_times": 12,
    },
    "superliga_dinamarca": {
        "nome": "Danish Superliga",
        "url": "https://fbref.com/en/comps/50/Danish-Superliga-Stats",
        "total_times": 12,
    },
    "allsvenskan": {
        "nome": "Allsvenskan (Suécia)",
        "url": "https://fbref.com/en/comps/29/Allsvenskan-Stats",
        "total_times": 16,
    },
    "eliteserien": {
        "nome": "Eliteserien (Noruega)",
        "url": "https://fbref.com/en/comps/28/Eliteserien-Stats",
        "total_times": 16,
    },
    "czech_first_league": {
        "nome": "Czech First League",
        "url": "https://fbref.com/en/comps/66/Czech-First-League-Stats",
        "total_times": 16,
    },
    "ekstraklasa": {
        "nome": "Ekstraklasa (Polônia)",
        "url": "https://fbref.com/en/comps/36/Ekstraklasa-Stats",
        "total_times": 18,
    },
    "liga_1_romenia": {
        "nome": "Liga I (Romênia)",
        "url": "https://fbref.com/en/comps/48/Liga-I-Stats",
        "total_times": 16,
    },
    "ukrainian_premier_league": {
        "nome": "Ukrainian Premier League",
        "url": "https://fbref.com/en/comps/39/Ukrainian-Premier-League-Stats",
        "total_times": 16,
    },
    "scottish_premiership": {
        "nome": "Scottish Premiership",
        "url": "https://fbref.com/en/comps/40/Scottish-Premiership-Stats",
        "total_times": 12,
    },
    "croatian_hnl": {
        "nome": "Croatian HNL",
        "url": "https://fbref.com/en/comps/63/Croatian-HNL-Stats",
        "total_times": 10,
    },

    # ===== AMÉRICA DO SUL =====
    "primera_division_uruguai": {
        "nome": "Primera División (Uruguai)",
        "url": "https://fbref.com/en/comps/45/Primera-Division-Stats",
        "total_times": 16,
    },
    "primera_division_chile": {
        "nome": "Primera División (Chile)",
        "url": "https://fbref.com/en/comps/44/Primera-Division-Stats",
        "total_times": 16,
    },
    "primera_a_equador": {
        "nome": "Serie A (Equador)",
        "url": "https://fbref.com/en/comps/70/Serie-A-Stats",
        "total_times": 16,
    },
    "primera_division_paraguai": {
        "nome": "Primera División (Paraguai)",
        "url": "https://fbref.com/en/comps/64/Primera-Division-Stats",
        "total_times": 12,
    },
    "primera_division_peru": {
        "nome": "Liga 1 (Peru)",
        "url": "https://fbref.com/en/comps/65/Liga-1-Stats",
        "total_times": 18,
    },
    "categoria_primera_a": {
        "nome": "Categoría Primera A (Colômbia)",
        "url": "https://fbref.com/en/comps/59/Categoria-Primera-A-Stats",
        "total_times": 20,
    },
    "primera_division_venezuela": {
        "nome": "Liga FUTVE (Venezuela)",
        "url": "https://fbref.com/en/comps/71/Liga-FUTVE-Stats",
        "total_times": 15,
    },

    # ===== ÁSIA =====
    "j1_league": {
        "nome": "J1 League (Japão)",
        "url": "https://fbref.com/en/comps/25/J1-League-Stats",
        "total_times": 18,
    },
    "k_league_1": {
        "nome": "K League 1 (Coreia do Sul)",
        "url": "https://fbref.com/en/comps/55/K-League-1-Stats",
        "total_times": 12,
    },
    "saudi_pro_league": {
        "nome": "Saudi Pro League",
        "url": "https://fbref.com/en/comps/35/Saudi-Professional-League-Stats",
        "total_times": 16,
    },
    "a_league": {
        "nome": "A-League (Austrália)",
        "url": "https://fbref.com/en/comps/47/A-League-Stats",
        "total_times": 12,
    },

    # ===== ÁFRICA =====
    "egyptian_premier_league": {
        "nome": "Egyptian Premier League",
        "url": "https://fbref.com/en/comps/42/Egyptian-Premier-League-Stats",
        "total_times": 18,
    },

    # ===== OUTRAS =====
    "superettan": {
        "nome": "Superettan (Suécia 2ª)",
        "url": "https://fbref.com/en/comps/51/Superettan-Stats",
        "total_times": 16,
    },
    "liga_1_indonesia": {
        "nome": "Liga 1 (Indonésia)",
        "url": "https://fbref.com/en/comps/53/Liga-1-Stats",
        "total_times": 18,
    },
    "indian_super_league": {
        "nome": "Indian Super League",
        "url": "https://fbref.com/en/comps/52/Indian-Super-League-Stats",
        "total_times": 11,
    },
    "liga_nacional_honduras": {
        "nome": "Liga Nacional (Honduras)",
        "url": "https://fbref.com/en/comps/57/Liga-Nacional-Stats",
        "total_times": 10,
    },
    "liga_fpf": {
        "nome": "Liga FPF (Portugal 2ª)",
        "url": "https://fbref.com/en/comps/62/Liga-Portugal-2-Stats",
        "total_times": 18,
    },
}

# ========== PASTA DE SAÍDA ==========
PASTA_DADOS = "dados"
os.makedirs(PASTA_DADOS, exist_ok=True)


# ========== FUNÇÃO DE REQUISIÇÃO SEGURA ==========
def requisicao_segura(url, max_tentativas=3):
    """Faz requisição com retry, backoff e User-Agent rotativo."""
    for tentativa in range(max_tentativas):
        try:
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Referer": "https://www.google.com/",
            }
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                print(f"⏳ Rate limit. Esperando 60s...")
                time.sleep(60)
            else:
                print(f"⚠️ Status {response.status_code}. Tentando novamente...")
                time.sleep(DELAY * 2)
        except Exception as e:
            print(f"❌ Erro: {e}. Tentativa {tentativa+1}/{max_tentativas}")
            time.sleep(DELAY * 2)

    return None


# ========== COLETA DE UMA LIGA ==========
def coletar_liga(chave, config):
    """Coleta todas as estatísticas de uma liga e salva em CSV."""
    nome = config["nome"]
    url = config["url"]

    print(f"\n{'='*60}")
    print(f"🔍 Coletando: {nome}")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")

    response = requisicao_segura(url)
    if not response:
        print(f"❌ Falha ao acessar {nome}")
        return None

    print("📊 Extraindo tabela de estatísticas...")
    try:
        tabelas = pd.read_html(response.text)
        df_stats = None
        for t in tabelas:
            cols = [str(c).lower() for c in t.columns if isinstance(c, str)]
            if 'possession' in ' '.join(cols) or 'gls' in ' '.join(cols):
                df_stats = t
                break
        if df_stats is None:
            df_stats = tabelas[0]

        if isinstance(df_stats.columns, pd.MultiIndex):
            df_stats.columns = ['_'.join(str(c).strip() for c in col).strip() 
                                for col in df_stats.columns.values]

        df_stats = df_stats[~df_stats.iloc[:, 0].astype(str).str.contains('Squad', na=False)]
        print(f"✅ {len(df_stats)} times encontrados")

    except Exception as e:
        print(f"❌ Erro ao extrair tabela: {e}")
        return None

    arquivo_times = os.path.join(PASTA_DADOS, f"{chave}_times.csv")
    df_stats.to_csv(arquivo_times, index=False)
    print(f"💾 Salvo: {arquivo_times}")

    print("📈 Calculando médias da liga...")
    medias = {}

    mapeamento_padroes = {
        'GM': ['Gls', 'Goals'],
        'FA': ['SoT'],
        'ECa': ['CK'],
        'Poss': ['Poss'],
        'GS': ['GA', 'Goals Against'],
        'FAS': ['SoTA'],
        'FC': ['Fls'],
        'CA': ['CrdY'],
        'Des': ['Tkl'],
    }

    for cod_engram, padroes in mapeamento_padroes.items():
        valor = None
        for padrao in padroes:
            colunas_match = [c for c in df_stats.columns 
                           if padrao.lower() in str(c).lower() and 'per 90' in str(c).lower()]
            if not colunas_match:
                colunas_match = [c for c in df_stats.columns 
                               if padrao.lower() in str(c).lower()]
            if colunas_match:
                try:
                    valores = pd.to_numeric(df_stats[colunas_match[0]], errors='coerce')
                    valor = valores.mean()
                    break
                except:
                    continue
        medias[cod_engram] = valor if valor is not None and not pd.isna(valor) else 0.0

    if medias.get('ECc', 0) == 0:
        medias['ECc'] = medias.get('ECa', 5.0)
    if medias.get('TC', 0) == 0:
        medias['TC'] = medias.get('FA', 4.0) * 2.5

    df_medias = pd.DataFrame([medias])
    arquivo_medias = os.path.join(PASTA_DADOS, f"{chave}_medias.csv")
    df_medias.to_csv(arquivo_medias, index=False)
    print(f"💾 Salvo: {arquivo_medias}")

    return df_stats, df_medias


# ========== RESUMO FINAL ==========
def gerar_resumo():
    """Gera um arquivo de resumo com todas as ligas coletadas."""
    resumo = []
    for chave, config in LIGAS.items():
        arquivo = os.path.join(PASTA_DADOS, f"{chave}_medias.csv")
        if os.path.exists(arquivo):
            resumo.append({
                "liga": config["nome"],
                "chave": chave,
                "arquivo": arquivo,
                "coletado_em": datetime.now().strftime('%Y-%m-%d %H:%M'),
            })

    if resumo:
        df_resumo = pd.DataFrame(resumo)
        df_resumo.to_csv(os.path.join(PASTA_DADOS, "resumo_ligas.csv"), index=False)
        print(f"\n📋 Resumo salvo: dados/resumo_ligas.csv")


# ========== EXECUÇÃO PRINCIPAL ==========
if __name__ == "__main__":
    print("⚽ ENGRAMSCORE — Coleta de Dados FBref")
    print(f"⏱️  Delay: {DELAY}s entre requisições")
    print(f"🏆 Ligas configuradas: {len(LIGAS)}")
    print(f"⏰ Tempo estimado: ~{len(LIGAS) * DELAY / 60:.0f} minutos\n")

    inicio = time.time()

    for chave, config in LIGAS.items():
        coletar_liga(chave, config)
        print(f"⏳ Aguardando {DELAY}s...")
        time.sleep(DELAY)

    gerar_resumo()

    fim = time.time()
    print(f"\n✅ Coleta concluída em {(fim-inicio)/60:.1f} minutos!")
    print(f"📁 Arquivos salvos em: {PASTA_DADOS}/")
    print("📌 Próximo passo: rodar analisar_pendentes.py")
