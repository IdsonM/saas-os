import streamlit as st
import requests
import pandas as pd
import io
import plotly.express as px
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
import os

# ✅ API correta e segura apontando para o Render
API_URL = "https://saas-os-api.onrender.com"

# ✅ Configuração de página do Streamlit
st.set_page_config(
    page_title="Sistema de OS PRO",
    layout="wide",
    page_icon="⚙️"
)

st.info(f"API conectada: {API_URL}")

# --- SISTEMA DE PERSISTÊNCIA COMPATÍVEL COM F5 ---
def verificar_login_definitivo():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
    if "usuario_nome" not in st.session_state:
        st.session_state["usuario_nome"] = ""

    if st.session_state["autenticado"]:
        return True

    params = st.query_params
    if "token_user" in params and not st.session_state["autenticado"]:
        st.session_state["autenticado"] = True
        st.session_state["usuario_nome"] = params["token_user"]
        return True

    st.markdown("<h2 style='text-align: center;'>🔐 Acesso Restrito</h2>", unsafe_allow_html=True)
    col_esquerda, col_centro, col_direita = st.columns([3.5, 3.0, 3.5])
    
    with col_centro:
        with st.form("formulario_login"):
            usuario = st.text_input("Usuário:")
            senha = st.text_input("Senha:", type="password")
            botao_entrar = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            
            if botao_entrar:
                with st.spinner("Conectando ao servidor na nuvem..."):
                    try:
                        payload = {"username": usuario, "password": senha}
                        # Envia com a barra final idêntica ao backend FastAPI
                        res = requests.post(f"{API_URL}/login/", json=payload, timeout=60)
                        
                        if res.status_code == 200:
                            st.session_state["autenticado"] = True
                            st.session_state["usuario_nome"] = usuario
                            st.query_params["token_user"] = usuario
                            st.success("Acesso liberado!")
                            st.rerun()
                        else:
                            st.error("Usuário ou senha incorretos.")
                    except requests.exceptions.RequestException:
                        st.error("Não foi possível conectar ao Backend para autenticar.")
    return False

if not verificar_login_definitivo():
    st.stop()

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown(f"### 👤 Usuário: **{st.session_state['usuario_nome']}**")
    st.markdown("---")
    if st.button("🚪 Sair do Sistema", use_container_width=True, type="primary"):
        st.session_state["autenticado"] = False
        st.session_state["usuario_nome"] = ""
        st.query_params.clear()
        st.rerun()

st.title("⚙️ Gerenciador de OS Malato's Tech")
st.markdown("---")

aba_os, aba_clientes, aba_cadastro_os, aba_usuarios, aba_dash = st.tabs([
    "📋 Listar Ordens de Serviço", 
    "👤 Cadastrar Cliente", 
    "➕ Abrir Nova OS",
    "🧑‍💻 Cadastrar Usuário/Técnico",
    "📊 Dashboard"
])

def formatar_data(data_str):
    if not data_str:
        return "-"
    try:
        dt = datetime.fromisoformat(data_str.replace("Z", ""))
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return data_str

def gerar_pdf_os(os_info):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.rect(30, 80, 550, 700)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, 750, "Malato's Tech")
    p.line(40, 690, 560, 690)
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(300, 660, f"ORDEM DE SERVIÇO Nº {os_info['id']}")
    p.save()
    buffer.seek(0)
    return buffer

# --- ABA 1: LISTAR ORDENS DE SERVIÇO ---
with aba_os:
    st.subheader("Ordens de Serviço Cadastradas")
    col_busca1, col_busca2 = st.columns(2)
    with col_busca1:
        termo_busca = st.text_input("🔍 Buscar por nome do cliente ou descrição:")
    with col_busca2:
        filtro_status = st.selectbox("🗂️ Filtrar por Status:", ["Todos", "Aberta", "Em Andamento", "Concluída"])
    
    try:
        response = requests.get(f"{API_URL}/os/", timeout=30)
        if response.status_code == 200:
            os_data = response.json()
            if len(os_data) == 0:
                st.info("Nenhuma Ordem de Serviço encontrada.")
            else:
                lista_formatada = []
                for os_item in os_data:
                    cliente_nome = os_item["cliente"]["nome"] if os_item["cliente"] else "Não identificado"
                    if filtro_status != "Todos" and os_item["status"] != filtro_status:
                        continue
                    if termo_busca and (termo_busca.lower() not in cliente_nome.lower() and termo_busca.lower() not in os_item["descricao"].lower()):
                        continue
                        
                    lista_formatada.append({
                        "ID da OS": os_item["id"],
                        "Cliente": cliente_nome,
                        "Descrição do Problema": os_item["descricao"],
                        "Valor (R$)": f"R$ {os_item['valor']:.2f}",
                        "Status": os_item["status"],
                        "Data Abertura": formatar_data(os_item.get("data_abertura")),
                    })
                
                if lista_formatada:
                    df = pd.DataFrame(lista_formatada)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("Nenhuma OS corresponde aos filtros aplicados.")
        else:
            st.error(f"Erro ao buscar OS: {response.status_code}")
    except requests.exceptions.RequestException:
        st.error("Erro na comunicação com o backend para listar as ordens.")
