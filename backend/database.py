from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Define o caminho do banco de dados SQLite local
SQLALCHEMY_DATABASE_URL = "sqlite:///../sistema_os.db"

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