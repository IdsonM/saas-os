import streamlit as st
import requests
import pandas as pd
import io
import plotly.express as px
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
import os

# ✅ API correta (sem valor fixo errado)
API_URL = "http://127.0.0.1:8000"

if not API_URL:
    st.error("API_URL não configurada no ambiente!")
    st.stop()

# ✅ config do Streamlit
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
                try:
                    payload = {"username": usuario, "password": senha}
                    res = requests.post(f"{API_URL}/login/", json=payload)
                    
                    if res.status_code == 200:
                        st.session_state["autenticado"] = True
                        st.session_state["usuario_nome"] = usuario
                        st.query_params["token_user"] = usuario
                        st.success("Acesso liberado!")
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")
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

# Incluído a aba de Cadastrar Usuários
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

    # quebra automática de linha
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
        response = requests.get(f"{API_URL}/os/")
        if response.status_code == 200:
            os_data = response.json()
            if len(os_data) == 0:
                st.info("Nenhuma Ordem de Serviço encontrada.")
            else:
                lista_formatada = []
                ids_disponiveis = []
                os_completa_dict = {}
                
                for os in os_data:
                    cliente_nome = os["cliente"]["nome"] if os["cliente"] else "Não identificado"
                    if filtro_status != "Todos" and os["status"] != filtro_status:
                        continue
                    if termo_busca and (termo_busca.lower() not in cliente_nome.lower() and termo_busca.lower() not in os["descricao"].lower()):
                        continue
                        
                    lista_formatada.append({
                        "ID da OS": os["id"],
                        "Cliente": cliente_nome,
                        "Descrição do Problema": os["descricao"],
                        "Valor (R$)": f"R$ {os['valor']:.2f}",
                        "Status": os["status"],
                        "Data Abertura": formatar_data(os.get("data_abertura")),
                        "Data Conclusão": formatar_data(os.get("data_conclusao"))
                    })
                    ids_disponiveis.append(os["id"])
                    os_completa_dict[os["id"]] = os
                
                if len(lista_formatada) == 0:
                    st.warning("Nenhuma OS corresponde aos filtros.")
                else:
                    st.dataframe(pd.DataFrame(lista_formatada), use_container_width=True, hide_index=True)
                    st.markdown("---")
                    st.subheader("🛠️ Gerenciar e Emitir Documentos")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        os_selecionada = st.selectbox("Selecione o ID da OS:", options=ids_disponiveis)
                    with col2:
                        novo_status = st.selectbox("Novo Status:", ["Aberta", "Em Andamento", "Concluída"])
                        if st.button("Atualizar Status", use_container_width=True):
                            res = requests.put(f"{API_URL}/os/{os_selecionada}/status?status={novo_status}")
                            if res.status_code == 200:
                                st.success("Status atualizado!")
                                st.rerun()
                    with col3:
                        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                        if os_selecionada in os_completa_dict:
                            st.download_button("🖨️ Baixar PDF da OS", data=gerar_pdf_os(os_completa_dict[os_selecionada]), file_name=f"OS_{os_selecionada}.pdf", mime="application/pdf", use_container_width=True)
                    with col4:
                        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                        if st.button("❌ Excluir esta OS", use_container_width=True, type="primary"):
                            if requests.delete(f"{API_URL}/os/{os_selecionada}").status_code == 204:
                                st.success("OS removida!")
                                st.rerun()
    except Exception as e:
        st.error(f"Erro ao conectar com servidor: {e}")
# -----------------------------------------------------------------------------
# ABA 2: CADASTRAR CLIENTE
# -----------------------------------------------------------------------------
with aba_clientes:
    st.subheader("Novo Cadastro de Cliente")
    with st.form("form_cliente", clear_on_submit=True):
        nome = st.text_input("Nome Completo:")
        telefone = st.text_input("Telefone / WhatsApp:")
        email = st.text_input("E-mail:")
        if st.form_submit_button("Salvar Cliente") and nome and telefone and email:
            res_cli = requests.post(f"{API_URL}/clientes/", json={"nome": nome, "telefone": telefone, "email": email})
            if res_cli.status_code == 201 or res_cli.status_code == 200:

                st.success(f"Cliente '{nome}' cadastrado!")

# -----------------------------------------------------------------------------
# ABA 3: ABRIR NOVA OS (CORRIGIDO)
# -----------------------------------------------------------------------------
with aba_cadastro_os:
    st.subheader("Abertura de Chamado / OS")
    try:
        res_clientes = requests.get(f"{API_URL}/clientes/")
        if res_clientes.status_code == 200:
            clientes = res_clientes.json()
            if len(clientes) == 0:
                st.warning("Cadastre um cliente primeiro antes de abrir uma OS.")
            else:
                opcoes_clientes = {c["nome"]: c["id"] for c in clientes}
                with st.form("form_os", clear_on_submit=True):
                    cliente_sel = st.selectbox("Selecione o Cliente:", options=list(opcoes_clientes.keys()))
                    desc = st.text_area("Descrição do problema:")
                    val = st.number_input("Valor (R$):", min_value=0.0, format="%.2f")
                    stt = st.selectbox("Status Inicial:", ["Aberta", "Em Andamento", "Concluída"])
                    
                    if st.form_submit_button("Gerar Ordem de Serviço"):
                        if desc:
                            payload_os = {"cliente_id": opcoes_clientes[cliente_sel], "descricao": desc, "valor": val, "status": stt}
                            res_o = requests.post(f"{API_URL}/os/", json=payload_os)
                            if res_o.status_code == 201 or res_o.status_code == 200:
                                st.success("OS criada com sucesso e notificação gerada!")
                            else:
                                st.error("Erro ao criar Ordem de Serviço.")
                        else:
                            st.warning("Descreva o problema antes de salvar.")
    except Exception as e:
        st.error(f"Erro de conexão com o servidor: {e}")

# -----------------------------------------------------------------------------
# ABA 4: CADASTRAR USUÁRIO/TÉCNICO
# -----------------------------------------------------------------------------
with aba_usuarios:
    st.subheader("Cadastrar Novo Funcionário / Operador")
    with st.form("form_usuario", clear_on_submit=True):
        novo_user = st.text_input("Nome de Usuário (Login):")
        nova_senha = st.text_input("Senha de Acesso:", type="password")
        
        if st.form_submit_button("Registrar Técnico"):
            if novo_user and nova_senha:
                res = requests.post(f"{API_URL}/usuarios/", json={"username": novo_user, "password": nova_senha})
                if res.status_code == 201:
                    st.success(f"Técnico '{novo_user}' registrado! Já pode fazer login com essa credencial.")
                else:
                    st.error("Erro ao registrar ou usuário já existente.")
            else:
                st.warning("Preencha todos os campos do formulário.")

# -----------------------------------------------------------------------------
# ABA 5: DASHBOARD
# -----------------------------------------------------------------------------
with aba_dash:
    st.subheader("Estatísticas e Métricas Financeiras")
    try:
        res_dash = requests.get(f"{API_URL}/dashboard/estatisticas")

        if res_dash.status_code == 200:
            dados_dash = res_dash.json()

            # ✅ segurança caso API venha vazia
            total_faturamento = float(dados_dash.get("total_faturamento", 0))
            total_os = int(dados_dash.get("total_os", 0))
            status_contagem = dados_dash.get("status_contagem", {})

        else:
            raise Exception("API não retornou dados")

    except:
        # ✅ FALLBACK: calcula direto das OS
        st.warning("API de dashboard indisponível. Calculando localmente...")

        res_os = requests.get(f"{API_URL}/os/")
        if res_os.status_code != 200:
            st.error("Erro ao carregar dados.")
            st.stop()

        os_data = res_os.json()

        total_os = len(os_data)

        # ✅ NORMALIZA status
        concluidas = [
            os for os in os_data
            if os.get("status", "").lower() == "concluída".lower()
        ]

        total_faturamento = sum(float(os.get("valor", 0)) for os in concluidas)

        # ✅ CONTAGEM de status
        status_contagem = {}
        for os_item in os_data:
            status = os_item.get("status", "Desconhecido")
            status_contagem[status] = status_contagem.get(status, 0) + 1

    # ✅ EXIBIÇÃO (sempre executa)
    m1, m2 = st.columns(2)

    with m1:
        st.metric(
            label="Faturamento Total (Apenas OS Concluídas)",
            value=f"R$ {total_faturamento:.2f}"
        )

    with m2:
        st.metric(
            label="Total de Ordens de Serviço Criadas",
            value=total_os
        )

    st.markdown("---")
    st.write("### Distribuição de OS por Status")

    if status_contagem:
        dados_grafico = pd.DataFrame({
            "Status": list(status_contagem.keys()),
            "Quantidade": list(status_contagem.values())
        })

        fig = px.bar(
            dados_grafico,
            x="Status",
            y="Quantidade",
            color="Status",
            color_discrete_map={
                "Aberta": "#EF553B",
                "Em Andamento": "#636EFA",
                "Concluída": "#00CC96"
            }
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para exibição.")