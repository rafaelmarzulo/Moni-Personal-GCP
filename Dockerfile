# ====================================
# Dockerfile para Google Cloud Platform
# Moni-Personal GCP Edition
# ====================================

FROM python:3.11-slim

# Definir variáveis de ambiente para produção
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ENVIRONMENT=production \
    FORCE_HTTPS=true

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar requirements primeiro (para aproveitar cache do Docker)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação com nova estrutura
COPY app/ ./app/
COPY templates/ ./templates/
COPY static/ ./static/
COPY main.py .
COPY database.py .
COPY models.py .
COPY config.py .

# Criar usuário não-root para segurança
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser \
    && chown -R appuser:appuser /app

# Trocar para usuário não-root
USER appuser

# Expor porta padrão do GCP Cloud Run
EXPOSE 8080

# Health check para Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Comando de inicialização otimizado para GCP
# Cloud Run injeta a variável PORT automaticamente
CMD exec uvicorn main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8080} \
    --workers 2 \
    --log-level info \
    --access-log \
    --proxy-headers \
    --forwarded-allow-ips "*"