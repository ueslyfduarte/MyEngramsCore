import sys
import importlib.util
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
INTERFACE_DIR = SRC_DIR / "interface"

sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(SRC_DIR))

import streamlit as st

# Verificar quais arquivos existem
st.set_page_config(page_title="EngramScore ⚽", page_icon="⚽", layout="wide")

# Listar arquivos na pasta interface
if INTERFACE_DIR.exists():
    arquivos = list(INTERFACE_DIR.iterdir())
    st.success(f"✅ Pasta interface encontrada! {len(arquivos)} arquivos.")
    for a in arquivos:
        st.write(f"📄 {a.name}")
else:
    st.error(f"❌ Pasta NÃO encontrada: {INTERFACE_DIR}")
    
    # Tentar encontrar a pasta interface em outro lugar
    st.write("Procurando pasta interface...")
    for root, dirs, files in os.walk(str(BASE_DIR)):
        if 'interface' in dirs:
            st.success(f"✅ Encontrada em: {os.path.join(root, 'interface')}")
        for f in files:
            if 'css.py' in f:
                st.success(f"✅ css.py encontrado em: {os.path.join(root, f)}")
