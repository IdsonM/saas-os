from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
import datetime
import bcrypt
import smtplib
from email.mime.text import MIMEText
import requests
import os

from dotenv import load_dotenv
load_dotenv()

from backend import models, schemas, database

app = FastAPI(title="API Sistema de OS PRO")

models.Base.metadata.create_all(bind=database.engine)

# ==========================================
# CONFIG
# ==========================================
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# ==========================================
# NOTIFICAÇÃO
# ==========================================
def disparar_notificacao_cliente(cliente_nome, cliente_email, cliente_telefone, os_id, novo_status):

    mensagem_texto = f"Olá {cliente_nome}! Sua OS #{os_id} agora está como: {novo_status}"

    # EMAIL
    if SMTP_USER and SMTP_PASSWORD:
        try:
            msg = MIMEText(mensagem_texto, 'plain', 'utf-8')
            msg['From'] = SMTP_USER
            msg['To'] = cliente_email
            msg['Subject'] = f"Atualização OS #{os_id}"

            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, cliente_email, msg.as_string())
            server.quit()
        except Exception as e:
            print(f"Erro email: {e}")

    # WHATSAPP
    if TWILIO_SID and TWILIO_AUTH and TWILIO_NUMBER:
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"

            payload = {
                "From": f"whatsapp:{TWILIO_NUMBER}",
                "To": f"whatsapp:{cliente_telefone}",
                "Body": mensagem_texto
            }

            requests.post(url, data=payload, auth=(TWILIO_SID, TWILIO_AUTH))
        except Exception as e:
            print(f"Erro WhatsApp: {e}")

# ==========================================
# SEGURANÇA
# ==========================================
def gerar_senha_hash(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

def verificar_senha(senha_pura: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha_pura.encode(), senha_hash.encode())
    except:
        return False

# ==========================================
# ADMIN PADRÃO
# ==========================================
def criar_admin_padrao():
    db = database.SessionLocal()
    try:
        if not db.query(models.Usuario).filter_by(username="admin").first():
            db.add(models.Usuario(
                username="admin",
                senha_hash=gerar_senha_hash("1234")
            ))
            db.commit()
    finally:
        db.close()

criar_admin_padrao()

# ==========================================
# AUTH
# ==========================================
@app.post("/usuarios/", response_model=schemas.UsuarioResponse, status_code=201)
def cadastrar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(database.get_db)):
    if db.query(models.Usuario).filter_by(username=usuario.username).first():
        raise HTTPException(400, "Usuário já existe")

    user = models.Usuario(
        username=usuario.username,
        senha_hash=gerar_senha_hash(usuario.password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/login/")
def login(dados: schemas.LoginRequest, db: Session = Depends(database.get_db)):
    user = db.query(models.Usuario).filter_by(username=dados.username).first()

    if not user or not verificar_senha(dados.password, user.senha_hash):
        raise HTTPException(401, "Login inválido")

    return {"status": "ok", "user": user.username}


# ==========================================
# CLIENTES
# ==========================================
@app.post("/clientes/", response_model=schemas.ClienteResponse, status_code=201)
def criar_cliente(cliente: schemas.ClienteCreate, db: Session = Depends(database.get_db)):
    cli = models.Cliente(**cliente.model_dump())
    db.add(cli)
    db.commit()
    db.refresh(cli)
    return cli


@app.get("/clientes/", response_model=List[schemas.ClienteResponse])
def listar_clientes(db: Session = Depends(database.get_db)):
    return db.query(models.Cliente).all()


# ==========================================
# ORDEM DE SERVIÇO
# ==========================================
@app.post("/os/", response_model=schemas.OSResponse, status_code=201)
def criar_os(os: schemas.OSCreate, db: Session = Depends(database.get_db)):

    cliente = db.query(models.Cliente).filter_by(id=os.cliente_id).first()

    if not cliente:
        raise HTTPException(404, "Cliente não encontrado")

    nova_os = models.OrdemServico(**os.model_dump())
    db.add(nova_os)
    db.commit()
    db.refresh(nova_os)

    # 🔥 importante: carregar cliente
    nova_os = db.query(models.OrdemServico)\
        .options(joinedload(models.OrdemServico.cliente))\
        .filter_by(id=nova_os.id)\
        .first()

    return nova_os


@app.get("/os/", response_model=List[schemas.OSResponse])
def listar_os(db: Session = Depends(database.get_db)):

    return db.query(models.OrdemServico)\
        .options(joinedload(models.OrdemServico.cliente))\
        .all()


@app.put("/os/{os_id}/status", response_model=schemas.OSResponse)
def atualizar_status_os(os_id: int, status: str, db: Session = Depends(database.get_db)):

    os_db = db.query(models.OrdemServico)\
        .options(joinedload(models.OrdemServico.cliente))\
        .filter_by(id=os_id)\
        .first()

    if not os_db:
        raise HTTPException(404, "OS não encontrada")

    os_db.status = status
    os_db.data_conclusao = datetime.datetime.utcnow() if status == "Concluída" else None

    db.commit()
    db.refresh(os_db)

    return os_db


@app.delete("/os/{os_id}", status_code=204)
def deletar_os(os_id: int, db: Session = Depends(database.get_db)):

    os_db = db.query(models.OrdemServico).filter_by(id=os_id).first()

    if not os_db:
        raise HTTPException(404, "OS não encontrada")

    db.delete(os_db)
    db.commit()


# ==========================================
# DASHBOARD
# ==========================================
@app.get("/dashboard/estatisticas")
def dashboard(db: Session = Depends(database.get_db)):

    os_list = db.query(models.OrdemServico).all()

    total_os = len(os_list)

    concluidas = [o for o in os_list if o.status == "Concluída"]
    total_faturamento = sum(o.valor for o in concluidas)

    status_contagem = {}
    for o in os_list:
        status_contagem[o.status] = status_contagem.get(o.status, 0) + 1

    return {
        "total_os": total_os,
        "total_faturamento": total_faturamento,
        "status_contagem": status_contagem
    }