import streamlit as st
import requests
import pandas as pd
import io
import plotly.express as px
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
import urllib3

# ✅ REMOVE WARNING SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ✅ API
API_URL = "https://saas-os-api.onrender.com"

# ✅ CONFIG
st.set_page_config(
    page_title="Sistema de OS PRO",
    layout="wide",
    page_icon="⚙️"
)

st.info(f"API conectada: {API_URL}")

# -----------------------------------------
# 🔐 LOGIN
# -----------------------------------------
def verificar_login_definitivo():

    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if "usuario_nome" not in st.session_state:
        st.session_state["usuario_nome"] = ""

    if st.session_state["autenticado"]:
        return True

    params = st.query_params

    if "token_user" in params:
        st.session_state["autenticado"] = True
        st.session_state["usuario_nome"] = params["token_user"]
        return True

    st.markdown("<h2 style='text-align:center;'>🔐 Acesso Restrito</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([3, 2, 3])

    with col2:
        with st.form("form_login"):

            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")

            entrar = st.form_submit_button("Entrar", use_container_width=True)

            if entrar:

                if not usuario or not senha:
                    st.warning("Preencha usuário e senha")
                    return False

                with st.spinner("Conectando com API..."):

                    try:
                        response = requests.post(
                            f"{API_URL}/login/",
                            json={"username": usuario, "password": senha},
                            timeout=60,
                            verify=False  # 🔥 CORREÇÃO SSL
                        )

                        # ✅ DEBUG
                        st.write("Status HTTP:", response.status_code)
                        st.write("Resposta:", response.text)

                        if response.status_code == 200:
                            st.session_state["autenticado"] = True
                            st.session_state["usuario_nome"] = usuario
                            st.query_params["token_user"] = usuario

                            st.success("Login realizado ✅")
                            st.rerun()

                        else:
                            st.error("Usuário ou senha inválidos")

                    except Exception as e:
                        import traceback

                        st.error("Erro ao conectar com backend")
                        st.text(f"Tipo: {type(e).__name__}")
                        st.text(f"Detalhes: {str(e)}")
                        st.text(traceback.format_exc())

    return False


# BLOQUEIO
if not verificar_login_definitivo():
    st.stop()

# -----------------------------------------
# SIDEBAR
# -----------------------------------------
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['usuario_nome']}")

    if st.button("🚪 Sair", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_nome"] = ""
        st.query_params.clear()
        st.rerun()

# -----------------------------------------
# FUNÇÕES
# -----------------------------------------
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

    p.drawString(50, 750, "Malato's Tech")
    p.drawString(50, 720, f"OS Nº {os_info['id']}")

    p.save()
    buffer.seek(0)
    return buffer


# -----------------------------------------
# MAIN
# -----------------------------------------
st.title("⚙️ Sistema de Ordem de Serviço")
st.markdown("---")

aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "📋 Ordens",
    "👤 Clientes",
    "➕ Nova OS",
    "🧑‍💻 Usuários",
    "📊 Dashboard"
])

# -----------------------------------------
# LISTAR OS
# -----------------------------------------
with aba1:

    st.subheader("Ordens de Serviço")

    busca = st.text_input("Buscar")
    status = st.selectbox("Status", ["Todos", "Aberta", "Em Andamento", "Concluída"])

    try:
        response = requests.get(
            f"{API_URL}/os/",
            timeout=30,
            verify=False  # 🔥 CORREÇÃO SSL
        )

        if response.status_code == 200:

            dados = response.json()
            lista = []

            for item in dados:

                cliente = item["cliente"]["nome"] if item.get("cliente") else "Não identificado"

                if status != "Todos" and item["status"] != status:
                    continue

                if busca:
                    b = busca.lower()
                    if b not in cliente.lower() and b not in item["descricao"].lower():
                        continue

                lista.append({
                    "ID": item["id"],
                    "Cliente": cliente,
                    "Descrição": item["descricao"],
                    "Valor": f"R$ {item['valor']:.2f}",
                    "Status": item["status"],
                    "Data": formatar_data(item.get("data_abertura"))
                })

            if lista:
                df = pd.DataFrame(lista)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Sem resultados")

        else:
            st.error(f"Erro API: {response.status_code}")

    except Exception as e:
        st.error(f"Erro conexão: {e}")

# -----------------------------------------
# OUTRAS ABAS
# -----------------------------------------
with aba2:
    st.subheader("Clientes")
    st.info("Em construção")

with aba3:
    st.subheader("Nova OS")
    st.info("Em construção")

with aba4:
    st.subheader("Usuários")
    st.info("Em construção")

with aba5:
    st.subheader("Dashboard")
    st.info("Em construção")