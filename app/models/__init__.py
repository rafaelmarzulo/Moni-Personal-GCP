from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    from backports.zoneinfo import ZoneInfo  # Fallback para versões antigas

# Timezone do Brasil - São Paulo
SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")

def now_sao_paulo():
    """Retorna datetime atual no timezone de São Paulo"""
    return datetime.now(SAO_PAULO_TZ)

class Avaliacao(Base):
    __tablename__ = "avaliacoes"

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=True)  # Nullable para compatibilidade com dados existentes
    nome = Column(String(100), nullable=False, index=True)  # Manter por compatibilidade

    # Campos antigos (manter compatibilidade)
    peso = Column(String(20), nullable=True)  # Manter para compatibilidade
    medidas = Column(Text, nullable=True)     # Manter para compatibilidade

    # Novos campos específicos para medidas corporais
    # Dados básicos
    peso_kg = Column(Float, nullable=True)           # Peso em kg
    altura_cm = Column(Float, nullable=True)         # Altura em cm
    percentual_gordura = Column(Float, nullable=True) # % de gordura corporal

    # Circunferências em cm
    circunferencia_pescoco = Column(Float, nullable=True)
    circunferencia_braco_direito = Column(Float, nullable=True)
    circunferencia_braco_esquerdo = Column(Float, nullable=True)
    circunferencia_antebraco_direito = Column(Float, nullable=True)
    circunferencia_antebraco_esquerdo = Column(Float, nullable=True)
    circunferencia_torax = Column(Float, nullable=True)
    circunferencia_cintura = Column(Float, nullable=True)
    circunferencia_abdome = Column(Float, nullable=True)
    circunferencia_quadril = Column(Float, nullable=True)
    circunferencia_coxa_direita = Column(Float, nullable=True)
    circunferencia_coxa_esquerda = Column(Float, nullable=True)
    circunferencia_panturrilha_direita = Column(Float, nullable=True)
    circunferencia_panturrilha_esquerda = Column(Float, nullable=True)

    # Dobras cutâneas em mm (para avaliações mais avançadas)
    dobra_bicipital = Column(Float, nullable=True)
    dobra_tricipital = Column(Float, nullable=True)
    dobra_subescapular = Column(Float, nullable=True)
    dobra_suprailiaca = Column(Float, nullable=True)
    dobra_abdominal = Column(Float, nullable=True)
    dobra_coxa = Column(Float, nullable=True)

    # Outros dados úteis
    imc = Column(Float, nullable=True)              # Índice de Massa Corporal (calculado)
    observacoes_medidas = Column(Text, nullable=True) # Observações sobre as medidas
    faltou_algo = Column(Text, nullable=False)
    gostou_mais_menos = Column(Text, nullable=False)
    meta_agua = Column(Text, nullable=False)
    meta_agua_melhorar = Column(Text, nullable=True)
    alimentacao = Column(Text, nullable=False)
    melhorias = Column(Text)  # Lista de melhorias separadas por vírgula
    outros_melhorias = Column(Text)
    pedido_especial = Column(Text, nullable=False)
    rotina_treino = Column(Text, nullable=True)
    sugestao_geral = Column(Text, nullable=False)
    data = Column(DateTime, default=now_sao_paulo, nullable=False)
    created_at = Column(DateTime, default=now_sao_paulo, nullable=False)

    # Relacionamento com aluno
    aluno = relationship("Aluno", back_populates="avaliacoes")

    def __repr__(self):
        return f"<Avaliacao(id={self.id}, nome='{self.nome}', data='{self.data}')>"

class Aluno(Base):
    __tablename__ = "alunos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    telefone = Column(String(20))
    senha_hash = Column(String(255), nullable=False)
    data_nascimento = Column(DateTime)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now_sao_paulo, nullable=False)

    # Relacionamento com avaliações
    avaliacoes = relationship("Avaliacao", back_populates="aluno")

    def __repr__(self):
        return f"<Aluno(id={self.id}, nome='{self.nome}', email='{self.email}')>"

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    nome = Column(String(100), nullable=False)
    senha_hash = Column(String(255), nullable=False)
    tipo = Column(String(20), default="admin")  # admin, personal_trainer
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now_sao_paulo)

    def __repr__(self):
        return f"<Usuario(id={self.id}, email='{self.email}', nome='{self.nome}', tipo='{self.tipo}')>"