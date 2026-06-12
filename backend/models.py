from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from .database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    senha_hash = Column(String, nullable=False)


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    telefone = Column(String, nullable=False)
    email = Column(String, nullable=False)

    ordens = relationship("OrdemServico", back_populates="cliente")


class OrdemServico(Base):
    __tablename__ = "ordens_servico"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)

    descricao = Column(String, nullable=False)
    valor = Column(Float, nullable=False)
    status = Column(String, default="Aberta")

    data_abertura = Column(DateTime, default=datetime.datetime.utcnow)
    data_conclusao = Column(DateTime, nullable=True)

    cliente = relationship("Cliente", back_populates="ordens")