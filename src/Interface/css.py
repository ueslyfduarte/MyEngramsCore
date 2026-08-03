"""
CSS Premium — EngramScore
Estilos visuais do aplicativo (temas, cores, fontes, cards).
"""

import streamlit as st

def carregar_css():
    """Carrega todo o CSS personalizado do EngramScore."""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

        * { font-family: 'Inter', sans-serif; }

        .stApp {
            background: linear-gradient(135deg, #06080D 0%, #0B0F17 50%, #0D111A 100%);
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0A0D14 0%, #0F1219 100%);
            border-right: 1px solid #1E2330;
        }
        [data-testid="stSidebar"] h2 {
            color: #F0C040 !important;
            font-weight: 800;
            letter-spacing: 2px;
            text-transform: uppercase;
            font-size: 14px;
            border-bottom: 2px solid #F0C040;
            padding-bottom: 8px;
            margin-bottom: 16px;
        }
        [data-testid="stSidebar"] .stNumberInput input {
            background: #111620;
            border: 1px solid #252B38;
            border-radius: 6px;
            color: #E0E0E0;
        }
        [data-testid="stSidebar"] .stNumberInput input:focus {
            border-color: #F0C040;
            box-shadow: 0 0 8px rgba(240,192,64,0.2);
        }

        /* Cards premium */
        .card-premium {
            background: linear-gradient(145deg, rgba(20,24,35,0.9) 0%, rgba(16,20,30,0.95) 100%);
            border: 1px solid #252B38;
            border-radius: 14px;
            padding: 20px 16px;
            margin: 8px 0;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.03);
            position: relative;
            overflow: hidden;
        }
        .card-premium::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(240,192,64,0.3), transparent);
        }
        .card-premium:hover {
            border-color: #F0C040;
            box-shadow: 0 12px 40px rgba(0,0,0,0.6), 0 0 20px rgba(240,192,64,0.1);
        }
        .card-header-premium {
            font-size: 14px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: #B0B8C0;
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Métricas gigantes */
        .metric-premium {
            font-size: 52px;
            font-weight: 900;
            text-align: center;
            background: linear-gradient(180deg, #F0C040 0%, #D4A017 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -2px;
            line-height: 1;
            margin: 6px 0;
        }
        .metric-premium-blue {
            font-size: 52px;
            font-weight: 900;
            text-align: center;
            background: linear-gradient(180deg, #4A90D9 0%, #2A5FA0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -2px;
            line-height: 1;
            margin: 6px 0;
        }

        .high-confidence {
            background: linear-gradient(180deg, #F0C040 0%, #D4A017 100%) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            background-clip: text !important;
            font-weight: 900;
        }

        .metric-label-premium {
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 3px;
            color: #B0B8C0;
            text-align: center;
            font-weight: 600;
        }

        /* Barras de progresso */
        .bar-premium {
            height: 6px;
            border-radius: 3px;
            background: rgba(255,255,255,0.05);
            margin: 10px 0;
            overflow: hidden;
        }
        .bar-fill-gold {
            height: 100%;
            border-radius: 3px;
            background: linear-gradient(90deg, #F0C040, #D4A017);
        }
        .bar-fill-blue {
            height: 100%;
            border-radius: 3px;
            background: linear-gradient(90deg, #4A90D9, #2A5FA0);
        }

        /* Selos */
        .selo-dourado {
            border: 2px solid #F0C040;
            border-radius: 20px;
            padding: 5px 14px;
            background: linear-gradient(135deg, rgba(240,192,64,0.15) 0%, rgba(240,192,64,0.05) 100%);
            color: #F0C040;
            font-weight: 700;
            font-size: 12px;
            display: inline-block;
            letter-spacing: 1px;
        }
        .selo-verde {
            border: 2px solid #00E676;
            border-radius: 20px;
            padding: 5px 14px;
            background: linear-gradient(135deg, rgba(0,230,118,0.15) 0%, rgba(0,230,118,0.05) 100%);
            color: #00E676;
            font-weight: 700;
            font-size: 12px;
            display: inline-block;
            letter-spacing: 1px;
        }
        .selo-amarelo {
            border: 2px solid #FFB300;
            border-radius: 20px;
            padding: 5px 14px;
            background: linear-gradient(135deg, rgba(255,179,0,0.15) 0%, rgba(255,179,0,0.05) 100%);
            color: #FFB300;
            font-weight: 700;
            font-size: 12px;
            display: inline-block;
            letter-spacing: 1px;
        }

        /* Botão principal */
        .stButton > button {
            background: linear-gradient(135deg, #F0C040 0%, #D4A017 100%);
            color: #0A0D14;
            font-weight: 800;
            font-size: 15px;
            letter-spacing: 2px;
            text-transform: uppercase;
            border: none;
            border-radius: 12px;
            padding: 14px 40px;
            box-shadow: 0 8px 24px rgba(240,192,64,0.3);
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 32px rgba(240,192,64,0.5);
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            background: rgba(255,255,255,0.02);
            border-radius: 12px;
            padding: 4px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 10px 18px;
            font-weight: 600;
            font-size: 14px;
            color: #B0B8C0;
            transition: all 0.2s;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, rgba(240,192,64,0.15) 0%, rgba(240,192,64,0.05) 100%) !important;
            color: #F0C040 !important;
            border: 1px solid rgba(240,192,64,0.3);
        }

        /* Prob boxes */
        .prob-box {
            background: linear-gradient(145deg, rgba(20,24,35,0.8) 0%, rgba(16,20,30,0.9) 100%);
            border-radius: 14px;
            padding: 20px 12px;
            text-align: center;
            border: 1px solid #252B38;
        }

        /* Info cards */
        .info-card {
            background: rgba(240,192,64,0.03);
            border: 1px solid rgba(240,192,64,0.1);
            border-radius: 12px;
            padding: 14px;
            margin: 6px 0;
            font-size: 15px;
            color: #E0E0E0;
            line-height: 1.6;
        }

        /* Divisor */
        .divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, #252B38, transparent);
            margin: 20px 0;
        }

        /* Campos de input */
        .stNumberInput input, .stTextInput input {
            background: #111620 !important;
            border: 1px solid #252B38 !important;
            border-radius: 8px !important;
            color: #E0E0E0 !important;
        }
        .stSelectbox > div > div {
            background: #111620 !important;
            border: 1px solid #252B38 !important;
            border-radius: 8px !important;
        }

        /* TextArea */
        .stTextArea textarea {
            background: #111620 !important;
            border: 1px solid #252B38 !important;
            border-radius: 8px !important;
            color: #E0E0E0 !important;
            font-size: 13px !important;
        }

        /* Títulos e subtítulos */
        h2, h3 {
            font-weight: 800 !important;
            letter-spacing: -0.5px;
            color: #F0C040 !important;
        }
    </style>
    """, unsafe_allow_html=True)


def renderizar_header():
    """Renderiza o cabeçalho principal do EngramScore."""
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 30px 0;">
        <div style="font-size:13px; text-transform:uppercase; letter-spacing:4px; color:#B0B8C0; margin-bottom:8px;">
            Sistema de Análise Esportiva
        </div>
        <h1 style="font-size:44px; font-weight:900; margin:0; letter-spacing:-1px;">
            <span style="background:linear-gradient(180deg, #F0C040 0%, #D4A017 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                ENGRAM
            </span>
            <span style="color:#E0E0E0; font-weight:300;">SCORE</span>
        </h1>
        <div style="font-size:13px; color:#B0B8C0; letter-spacing:3px; margin-top:4px;">
            ÍNDICE DE FORÇA ABSOLUTA — ONDE A MEMÓRIA CONSOLIDA O PADRÃO
        </div>
    </div>
    """, unsafe_allow_html=True)


def renderizar_rodape():
    """Renderiza o rodapé do aplicativo."""
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; padding:20px; color:#B0B8C0; font-size:13px; letter-spacing:2px;">
        ENGRAMSCORE © 2026 · ANÁLISE DIFERENCIAL DE FORÇA
    </div>
    """, unsafe_allow_html=True)
