from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# ==========================================
# USUÁRIOS
# ==========================================
class UsuarioCreate(BaseModel):
    username: str
    password: str


class UsuarioResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


# ==========================================
# CLIENTES
# ==========================================
class ClienteBase(BaseModel):
    nome: str
    telefone: str
    email: str


class ClienteCreate(ClienteBase):
    pass


class ClienteResponse(ClienteBase):
    id: int

    class Config:
        from_attributes = True


# ==========================================
# ORDEM DE SERVIÇO (OS)
# ==========================================
class OSBase(BaseModel):
    descricao: str
    status: str
    valor: float


class OSCreate(OSBase):
    cliente_id: int


class OSResponse(OSBase):
    id: int
    cliente_id: int
    data_abertura: datetime
    data_conclusao: Optional[datetime] = None
    cliente: Optional[ClienteResponse] = None

    class Config:
        from_attributes = True