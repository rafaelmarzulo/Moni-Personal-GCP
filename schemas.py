from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional, List

class AvaliacaoBase(BaseModel):
    nome: str
    peso: str
    medidas: str
    faltou_algo: str
    gostou_mais_menos: str
    meta_agua: str
    alimentacao: str
    melhorias: Optional[str] = ""
    outros_melhorias: Optional[str] = ""
    pedido_especial: Optional[str] = ""
    sugestao_geral: Optional[str] = ""

class AvaliacaoCreate(AvaliacaoBase):
    pass

class AvaliacaoResponse(AvaliacaoBase):
    id: int
    data: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class UsuarioBase(BaseModel):
    email: EmailStr
    nome: str

class UsuarioCreate(UsuarioBase):
    senha: str

class UsuarioResponse(UsuarioBase):
    id: int
    ativo: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    senha: str

# Schemas para Alunos
class AlunoBase(BaseModel):
    nome: str
    email: EmailStr
    telefone: Optional[str] = None
    data_nascimento: Optional[date] = None

class AlunoCreate(AlunoBase):
    senha: str

class AlunoUpdate(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    data_nascimento: Optional[date] = None

class AlunoResponse(AlunoBase):
    id: int
    ativo: bool
    created_at: datetime

    class Config:
        from_attributes = True

class AlunoLogin(BaseModel):
    email: EmailStr
    senha: str

# Schemas para autenticação
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_type: str
    user_id: int
    nome: str

class AlunoResumo(BaseModel):
    nome: str
    total_avaliacoes: int
    primeira_avaliacao: datetime
    ultima_avaliacao: datetime