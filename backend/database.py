import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 🟢 Define um caminho absoluto seguro independente de onde o sistema esteja rodando
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Garante que o banco seja criado na pasta raiz do projeto na nuvem (uma pasta acima do backend)
DB_PATH = os.path.join(BASE_DIR, "..", "sistema_os.db")

# Cria a URL com o caminho absoluto correto
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.abspath(DB_PATH)}"

# Cria o motor do banco de dados
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Cria a fábrica de sessões para as requisições
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para a criação dos modelos do banco de dados
Base = declarative_base()

# Função utilitária para abrir e fechar a conexão com o banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
