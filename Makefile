# MoniPersonal - Sistema de Reavaliação Física
.PHONY: help build up down logs clean dev test

help: ## Mostra esta ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Constrói as imagens Docker
	docker-compose build

up: ## Inicia os serviços
	docker-compose up -d

down: ## Para os serviços
	docker-compose down

logs: ## Mostra os logs
	docker-compose logs -f

clean: ## Remove containers, volumes e imagens
	docker-compose down -v --rmi all

dev: ## Inicia em modo desenvolvimento
	docker-compose up --build

test: ## Roda os testes (implementar)
	echo "Testes não implementados ainda"

shell: ## Acessa shell do container web
	docker-compose exec web bash

db-shell: ## Acessa shell do PostgreSQL
	docker-compose exec db psql -U monipersonal_user -d monipersonal

migrate: ## Roda migrações do banco
	docker-compose exec web python -c "from database import engine; import models; models.Base.metadata.create_all(bind=engine)"

backup: ## Backup do banco
	docker-compose exec db pg_dump -U monipersonal_user monipersonal > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore: ## Restaura backup (uso: make restore BACKUP=backup_file.sql)
	docker-compose exec -T db psql -U monipersonal_user monipersonal < $(BACKUP)

# ============= COMANDOS DE DESENVOLVIMENTO =============

# Branch workflow
branch: ## Cria nova branch (uso: make branch TYPE=feature NAME=user-dashboard)
	@echo "🌿 Criando nova branch..."
	@if [ -z "$(TYPE)" ] || [ -z "$(NAME)" ]; then \
		echo "❌ Erro: Especifique TYPE e NAME"; \
		echo "Exemplo: make branch TYPE=feature NAME=user-dashboard"; \
		exit 1; \
	fi
	@./scripts/create-branch.sh $(TYPE) $(NAME)

commit: ## Faz commit padronizado (uso: make commit TYPE=feat MSG='sua mensagem')
	@echo "📝 Fazendo commit padronizado..."
	@if [ -z "$(TYPE)" ] || [ -z "$(MSG)" ]; then \
		echo "❌ Erro: Especifique TYPE e MSG"; \
		echo "Exemplo: make commit TYPE=feat MSG='implementar dashboard'"; \
		exit 1; \
	fi
	@./scripts/commit.sh $(TYPE) "$(MSG)"

# Git shortcuts
status: ## Mostra status do repositório
	@echo "📋 Status do repositório:"
	@git status

log: ## Mostra últimos commits
	@echo "📜 Últimos commits:"
	@git log --oneline -10

branches: ## Lista branches locais e remotas
	@echo "🌿 Branches locais:"
	@git branch
	@echo ""
	@echo "🌐 Branches remotas:"
	@git branch -r

clean-branches: ## Remove branches locais já merged
	@echo "🧹 Limpando branches locais já merged..."
	@git branch --merged main | grep -v main | xargs -n 1 git branch -d || echo "Nenhuma branch para limpar"

sync: ## Sincroniza com repositório remoto
	@echo "🔄 Sincronizando com remote..."
	@git fetch --prune
	@git pull origin main

# Development helpers
new-feature: ## Inicia nova feature (uso: make new-feature NAME=user-dashboard)
	@echo "🚀 Iniciando nova feature..."
	@if [ -z "$(NAME)" ]; then \
		echo "❌ Erro: Especifique NAME da feature"; \
		echo "Exemplo: make new-feature NAME=user-dashboard"; \
		exit 1; \
	fi
	@./scripts/create-branch.sh feature $(NAME)

fix-bug: ## Inicia correção de bug (uso: make fix-bug NAME=login-error)
	@echo "🐛 Iniciando correção de bug..."
	@if [ -z "$(NAME)" ]; then \
		echo "❌ Erro: Especifique NAME do bug"; \
		echo "Exemplo: make fix-bug NAME=login-error"; \
		exit 1; \
	fi
	@./scripts/create-branch.sh fix $(NAME)

hotfix: ## Inicia hotfix urgente (uso: make hotfix NAME=security-patch)
	@echo "🚨 Iniciando hotfix..."
	@if [ -z "$(NAME)" ]; then \
		echo "❌ Erro: Especifique NAME do hotfix"; \
		echo "Exemplo: make hotfix NAME=security-patch"; \
		exit 1; \
	fi
	@./scripts/create-branch.sh hotfix $(NAME)

# Comandos de deploy e produção
deploy-check: ## Verifica configuração de deploy
	@echo "🔍 Verificando configuração de deploy..."
	@python test_production_environment.py

production-test: ## Testa ambiente de produção
	@echo "🧪 Testando ambiente de produção..."
	@python test_production_environment.py