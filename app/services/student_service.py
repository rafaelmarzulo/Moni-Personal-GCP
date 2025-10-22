"""
Serviços de negócio para operações relacionadas aos alunos
"""
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List, Optional, Dict, Any

from app.models import Aluno, Avaliacao
from app.utils.logging import info_log, debug_log, error_log
from app.utils.datetime_utils import now_sao_paulo, utc_to_sao_paulo


class StudentService:
    """Serviço para operações relacionadas aos alunos"""

    @staticmethod
    def get_student_by_id(db: Session, student_id: int) -> Optional[Aluno]:
        """Busca um aluno pelo ID"""
        try:
            aluno = db.query(Aluno).filter(
                Aluno.id == student_id,
                Aluno.ativo == True
            ).first()

            if aluno:
                debug_log(f"👤 StudentService: Aluno {aluno.nome} encontrado")
            else:
                debug_log(f"❌ StudentService: Aluno ID {student_id} não encontrado")

            return aluno
        except Exception as e:
            error_log(f"❌ StudentService: Erro ao buscar aluno {student_id}: {str(e)}")
            return None

    @staticmethod
    def get_student_evaluations(db: Session, student_id: int) -> List[Avaliacao]:
        """Busca todas as avaliações de um aluno"""
        try:
            avaliacoes = db.query(Avaliacao).filter(
                Avaliacao.aluno_id == student_id
            ).order_by(Avaliacao.data_avaliacao.desc()).all()

            # Converter timestamps para timezone local
            for avaliacao in avaliacoes:
                if avaliacao.data_avaliacao:
                    avaliacao.data_local = utc_to_sao_paulo(avaliacao.data_avaliacao)

            debug_log(f"📊 StudentService: {len(avaliacoes)} avaliações encontradas para aluno {student_id}")
            return avaliacoes

        except Exception as e:
            error_log(f"❌ StudentService: Erro ao buscar avaliações do aluno {student_id}: {str(e)}")
            return []

    @staticmethod
    def create_evaluation(
        db: Session,
        student_id: int,
        peso: float,
        altura: float,
        observacoes: str = ""
    ) -> Optional[Avaliacao]:
        """Cria uma nova avaliação para um aluno"""
        try:
            # Verificar se o aluno existe
            aluno = StudentService.get_student_by_id(db, student_id)
            if not aluno:
                error_log(f"❌ StudentService: Tentativa de criar avaliação para aluno inexistente {student_id}")
                return None

            # Validar dados
            if peso <= 0 or altura <= 0:
                error_log(f"❌ StudentService: Dados inválidos - peso: {peso}, altura: {altura}")
                return None

            # Criar nova avaliação
            nova_avaliacao = Avaliacao(
                aluno_id=student_id,
                data_avaliacao=now_sao_paulo(),
                peso=peso,
                altura=altura,
                observacoes=observacoes or ""
            )

            # Calcular IMC
            imc = peso / ((altura / 100) ** 2)
            nova_avaliacao.imc = round(imc, 2)

            # Salvar no banco
            db.add(nova_avaliacao)
            db.commit()
            db.refresh(nova_avaliacao)

            info_log(f"✅ StudentService: Avaliação criada para {aluno.nome} - Peso: {peso}kg, Altura: {altura}cm, IMC: {nova_avaliacao.imc}")

            return nova_avaliacao

        except Exception as e:
            error_log(f"❌ StudentService: Erro ao criar avaliação: {str(e)}")
            db.rollback()
            return None

    @staticmethod
    def get_student_stats(db: Session, student_id: int) -> Dict[str, Any]:
        """Calcula estatísticas básicas de um aluno"""
        try:
            aluno = StudentService.get_student_by_id(db, student_id)
            if not aluno:
                return {}

            avaliacoes = StudentService.get_student_evaluations(db, student_id)

            if not avaliacoes:
                return {
                    "aluno": aluno,
                    "total_avaliacoes": 0,
                    "ultima_avaliacao": None,
                    "imc_atual": None,
                    "peso_atual": None
                }

            ultima_avaliacao = avaliacoes[0]  # Já está ordenado por data desc

            stats = {
                "aluno": aluno,
                "total_avaliacoes": len(avaliacoes),
                "ultima_avaliacao": ultima_avaliacao,
                "imc_atual": ultima_avaliacao.imc,
                "peso_atual": ultima_avaliacao.peso,
                "altura_atual": ultima_avaliacao.altura
            }

            # Calcular tendências se houver mais de uma avaliação
            if len(avaliacoes) >= 2:
                penultima_avaliacao = avaliacoes[1]
                diferenca_peso = ultima_avaliacao.peso - penultima_avaliacao.peso
                diferenca_imc = ultima_avaliacao.imc - penultima_avaliacao.imc

                stats.update({
                    "diferenca_peso": round(diferenca_peso, 2),
                    "diferenca_imc": round(diferenca_imc, 2),
                    "tendencia_peso": "↑" if diferenca_peso > 0 else "↓" if diferenca_peso < 0 else "→",
                    "tendencia_imc": "↑" if diferenca_imc > 0 else "↓" if diferenca_imc < 0 else "→"
                })

            debug_log(f"📊 StudentService: Estatísticas calculadas para {aluno.nome}")
            return stats

        except Exception as e:
            error_log(f"❌ StudentService: Erro ao calcular estatísticas do aluno {student_id}: {str(e)}")
            return {}

    @staticmethod
    def classify_imc(imc: float) -> Dict[str, str]:
        """Classifica o IMC de acordo com os padrões da OMS"""
        if imc < 18.5:
            return {"categoria": "Abaixo do peso", "cor": "text-info"}
        elif imc < 25:
            return {"categoria": "Peso normal", "cor": "text-success"}
        elif imc < 30:
            return {"categoria": "Sobrepeso", "cor": "text-warning"}
        elif imc < 35:
            return {"categoria": "Obesidade grau I", "cor": "text-danger"}
        elif imc < 40:
            return {"categoria": "Obesidade grau II", "cor": "text-danger"}
        else:
            return {"categoria": "Obesidade grau III", "cor": "text-danger"}


class AdminService:
    """Serviço para operações administrativas"""

    @staticmethod
    def get_all_students_with_stats(db: Session) -> List[Dict[str, Any]]:
        """Retorna todos os alunos com suas estatísticas básicas"""
        try:
            alunos = db.query(Aluno).order_by(Aluno.nome).all()

            alunos_stats = []
            for aluno in alunos:
                stats = StudentService.get_student_stats(db, aluno.id)
                alunos_stats.append(stats)

            info_log(f"📊 AdminService: {len(alunos)} alunos carregados com estatísticas")
            return alunos_stats

        except Exception as e:
            error_log(f"❌ AdminService: Erro ao carregar alunos: {str(e)}")
            return []

    @staticmethod
    def get_system_stats(db: Session) -> Dict[str, Any]:
        """Calcula estatísticas gerais do sistema"""
        try:
            from sqlalchemy import func

            # Estatísticas básicas
            total_alunos = db.query(Aluno).count()
            alunos_ativos = db.query(Aluno).filter(Aluno.ativo == True).count()
            total_avaliacoes = db.query(Avaliacao).count()

            # Avaliações dos últimos 30 dias
            from datetime import timedelta
            data_limite = now_sao_paulo() - timedelta(days=30)
            avaliacoes_recentes = db.query(Avaliacao).filter(
                Avaliacao.data_avaliacao >= data_limite
            ).count()

            # IMC médio do sistema
            imc_medio = db.query(func.avg(Avaliacao.imc)).filter(
                Avaliacao.imc.isnot(None)
            ).scalar()

            stats = {
                "total_alunos": total_alunos,
                "alunos_ativos": alunos_ativos,
                "total_avaliacoes": total_avaliacoes,
                "avaliacoes_ultimos_30_dias": avaliacoes_recentes,
                "imc_medio": round(float(imc_medio), 2) if imc_medio else None,
                "timestamp": now_sao_paulo().isoformat()
            }

            info_log(f"📊 AdminService: Estatísticas do sistema calculadas")
            return stats

        except Exception as e:
            error_log(f"❌ AdminService: Erro ao calcular estatísticas do sistema: {str(e)}")
            return {}