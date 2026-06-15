import streamlit as st
import requests
import pandas as pd
import io
import plotly.express as px
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
import os

# ✅ API correta apontando para o Render
API_URL = "https://saas-os-api.onrender.com"

st.info(f"API conectada: {API_URL}")

if not API_URL:
    st.error("API_URL não configurada no ambiente!")
    st.stop()

# ✅ Configuração de página do Streamlit
st.set_page_config(
    page_title="Sistema de OS PRO",
    layout="wide",
    page_icon="⚙️"
)

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
                with st.spinner("Conectando ao servidor na nuvem... (Pode demorar se o servidor estiver acordando)"):
                    try:
                        payload = {"username": usuario, "password": senha}
                        # Rota ajustada para /login (sem barra final) e timeout estendido para o Render
                        res = requests.post(f"{API_URL}/login", json=payload, timeout=60)
                        
                        if res.status_code == 200:
                            st.session_state["autenticado"] = True
                            st.session_state["usuario_nome"] = usuario
                            st.query_params["token_user"] = usuario
                            st.success("Acesso liberado!")
                            st.rerun()
                        else:
                            st.error("Usuário ou senha incorretos.")
                    except requests.exceptions.Timeout:
                        st.error("O servidor do Render demorou muito para responder. Tente clicar novamente em alguns instantes.")
                    except requests.exceptions.ConnectionError:
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

# Definição das abas do sistema
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

    # ==============================
    # DADOS DA EMPRESA
    # ==============================
    empresa_nome = "Malato's Tech"
    empresa_cnpj = "00.000.000/0001-00"
    empresa_tel = "(91) 992691862"
    empresa_email = "slashilck@hotmail.com"

    # ==============================
    # BORDA (DEIXA PROFISSIONAL)
    # ==============================
    p.rect(30, 80, 550, 700)

    # ==============================
    # CABEÇALHO
    # ==============================
    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, 750, empresa_nome)

    p.setFont("Helvetica", 10)
    p.drawString(40, 735, f"CNPJ: {empresa_cnpj}")
    p.drawString(40, 720, f"Telefone: {empresa_tel}")
    p.drawString(40, 705, f"E-mail: {empresa_email}")

    p.line(40, 690, 560, 690)

    # ==============================
    # TÍTULO CENTRAL
    # ==============================
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(300, 660, f"ORDEM DE SERVIÇO Nº {os_info['id']}")

    # ==============================
    # DADOS DO CLIENTE
    # ==============================
    cliente = os_info.get("cliente", {}) or {}

    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, 620, "DADOS DO CLIENTE")

    p.setFont("Helvetica", 11)
    p.drawString(40, 600, f"Nome: {cliente.get('nome', '-')}")
    p.drawString(40, 585, f"Telefone: {cliente.get('telefone', '-')}")
    p.drawString(40, 570, f"E-mail: {cliente.get('email', '-')}")

    # ==============================
    # DETALHES
    # ==============================
    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, 530, "DETALHES DO SERVIÇO")

    p.setFont("Helvetica", 11)
    p.drawString(40, 510, f"Status: {os_info.get('status', '-')}")
    p.drawString(40, 495, f"Valor: R$ {float(os_info.get('valor', 0)):.2f}")
    p.drawString(40, 480, f"Abertura: {formatar_data(os_info.get('data_abertura'))}")
    p.drawString(40, 465, f"Conclusão: {formatar_data(os_info.get('data_conclusao'))}")

    # ==============================
    # DESCRIÇÃO (COM QUEBRA)
    # ==============================
    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, 430, "DESCRIÇÃO")

    text = p.beginText(40, 410)
    text.setFont("Helvetica", 11)
    text.setLeading(14)

    descricao = os_info.get("descricao", "-")

    # Quebra automática de linha
    for linha in descricao.split("\n"):
        text.textLine(linha)

    p.drawText(text)

    # ==============================
    # ASSINATURAS PROFISSIONAIS
    # ==============================
    y_assinatura = 160

    # Cliente
    p.line(80, y_assinatura, 260, y_assinatura)
    p.setFont("Helvetica", 10)
    p.drawCentredString(170, y_assinatura - 15, "Assinatura do Cliente")

    # Empresa
    p.line(340, y_assinatura, 520, y_assinatura)
    p.drawCentredString(430, y_assinatura - 15, "Assinatura da Empresa")

    # ==============================
    # RODAPÉ
    # ==============================
    p.setFont("Helvetica-Oblique", 8)
    p.drawCentredString(300, 100, "Documento gerado automaticamente por Malato's Tech")

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
        # Adicionado timeout na listagem de OS também para evitar travamentos
        response = requests.get(f"{API_URL}/os/", timeout=30)
        if response.status_code == 200:
            os_data = response.json()
            if len(os_data) == 0:
                st.info("Nenhuma Ordem de Serviço encontrada.")
            else:
                lista_formatada = []
                ids_disponiveis = []
                os_completa_dict = {}
                
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
