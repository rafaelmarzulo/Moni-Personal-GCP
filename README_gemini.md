# 1. Título do Projeto

**Moni-Personal GCP: Sistema de Gestão de Reavaliações Físicas**

---

## 2. Sobre o Projeto

O Moni-Personal GCP é uma aplicação web desenvolvida em Python com FastAPI, projetada para que personal trainers possam gerenciar as avaliações físicas e o progresso de seus alunos.

O sistema é otimizado para deploy em ambiente de nuvem, especificamente na Google Cloud Platform (GCP), utilizando tecnologias serverless como Cloud Run e bancos de dados gerenciados como o Cloud SQL.

### Funcionalidades Principais
- **Gestão de Alunos**: Cadastro e organização dos clientes.
- **Avaliações Físicas**: Formulário detalhado para registro de peso, medidas, dobras cutâneas, etc.
- **Histórico de Evolução**: Visualização completa do progresso de cada aluno ao longo do tempo.
- **Relatórios**: Geração de relatórios comparativos entre avaliações.
- **Autenticação Segura**: Sistema de login para personal trainers e acesso restrito para alunos.

---

## 3. Arquitetura

A arquitetura foi desenhada para ser escalável, segura e de baixo custo, aproveitando os serviços gerenciados da GCP.

- **Aplicação**: Container Docker executando uma aplicação FastAPI com Gunicorn.
- **Hospedagem**:
    - **Principal**: Google Cloud Run (Serverless), permitindo escalar de zero a N instâncias conforme a demanda.
    - **Alternativa**: Google Kubernetes Engine (GKE), conforme definido na infraestrutura como código (Terraform).
- **Banco de Dados**: Google Cloud SQL para PostgreSQL, com conexões seguras e privadas.
- **Segredos**: Google Secret Manager para armazenar credenciais de banco de dados, chaves de API e outras informações sensíveis.
- **CI/CD**: GitHub Actions para automação de testes, scan de segurança, build e deploy.

### Diagrama Textual (Cloud Run)
```
Usuário Final
      │
      ▼ (HTTPS)
[ Google Cloud Load Balancer ]
      │
      ▼
[ Cloud Run Service (Container FastAPI) ]
      │   ↑ (Auto-scaling 0-N)
      │
      ├─► [ Secret Manager ] (Leitura de segredos)
      │
      └─► [ Cloud SQL (PostgreSQL) ] (Conexão via Unix Socket)
```

---

## 4. Pré-requisitos

Para executar o projeto localmente ou realizar o deploy, você precisará de:
- **Python 3.11+**
- **Docker** e **Docker Compose**
- **Google Cloud SDK (`gcloud`)** configurado e autenticado.
- **Terraform 1.6+** (Opcional, para provisionar a infraestrutura via IaC).
- **Make** (Opcional, para usar os atalhos do `Makefile`).

---

## 5. Como Executar

### Ambiente de Desenvolvimento Local (Docker)
O método recomendado para o ambiente local é utilizando Docker Compose.

1.  **Copie as variáveis de ambiente:**
    ```bash
    cp .env.example .env
    ```
    *Ajuste as variáveis no arquivo `.env`, principalmente as de banco de dados local (`POSTGRES_*`).*

2.  **Inicie os serviços (aplicação + banco de dados):**
    ```bash
    make dev
    ```
    *Alternativamente, sem o `Makefile`:*
    ```bash
    docker-compose up --build
    ```

3.  **Acesse a aplicação:**
    A aplicação estará disponível em `http://localhost:8080`.

### Deploy na Google Cloud Platform (Cloud Run)
O repositório contém scripts para automatizar o deploy.

1.  **Clone o repositório:**
    ```bash
    git clone <URL_DO_REPOSITORIO>
    cd Moni-Personal-GCP
    ```

2.  **Execute o script de setup e deploy:**
    *TODO: Detalhar os passos dos scripts em `scripts/gcp/` ou referenciar o guia `DEPLOY-GUIDE.md`.*
    ```bash
    # Exemplo de comando (verificar scripts para a ordem correta)
    ./scripts/gcp/setup-secrets.sh
    ./scripts/gcp/setup-cloudsql.sh
    ./scripts/gcp/deploy-cloud-run.sh
    ```

---

## 6. Estrutura de Pastas

```
/
├── app/                  # Código-fonte da aplicação FastAPI
│   ├── core/             # Configurações centrais (DB, settings)
│   ├── middleware/       # Middlewares (autenticação, rate limit)
│   ├── models/           # Modelos de dados (SQLAlchemy ORM)
│   ├── routes/           # Endpoints da API (rotas)
│   ├── schemas/          # Schemas de validação (Pydantic)
│   ├── services/         # Lógica de negócio
│   └── utils/            # Funções utilitárias
├── infrastructure/       # Infraestrutura como Código (IaC)
│   ├── kubernetes/       # Manifestos para deploy em GKE
│   └── terraform/        # Código Terraform para provisionar GCP
├── scripts/              # Scripts de automação (deploy, commit, etc.)
├── static/               # Arquivos estáticos (CSS, JS, imagens)
├── templates/            # Templates HTML (Jinja2)
├── .github/workflows/    # Pipelines de CI/CD (GitHub Actions)
├── app.yaml              # Configuração para deploy no App Engine
├── Dockerfile            # Definição do container da aplicação
├── main.py               # Ponto de entrada da aplicação FastAPI
├── Makefile              # Atalhos para comandos comuns
├── requirements.txt      # Dependências Python
└── .env.example          # Exemplo de variáveis de ambiente
```

---

## 7. Configuração/Variáveis

As configurações da aplicação são gerenciadas por variáveis de ambiente. Copie o arquivo `.env.example` para `.env` para desenvolvimento local. Em produção (GCP), estas variáveis devem ser configuradas no **Google Secret Manager**.

| Variável | Descrição | Exemplo |
|---|---|---|
| `DATABASE_URL` | URL de conexão com o banco de dados PostgreSQL. | `postgresql://user:pass@host:port/db` |
| `SECRET_KEY` | Chave secreta para operações criptográficas gerais. | `your-strong-secret-key` |
| `JWT_SECRET_KEY` | Chave secreta específica para assinar tokens JWT. | `your-strong-jwt-secret-key` |
| `GCP_PROJECT_ID` | ID do projeto na Google Cloud. | `my-gcp-project-12345` |
| `GCP_REGION` | Região padrão para os recursos GCP. | `southamerica-east1` |
| `LOG_LEVEL` | Nível de log da aplicação (INFO, DEBUG, ERROR). | `INFO` |
| `RATE_LIMIT_PER_MINUTE` | Limite de requisições por minuto por cliente. | `60` |

---

## 8. Testes

O projeto está configurado para usar `pytest`. O pipeline de CI/CD executa os testes automaticamente.

Para rodar os testes localmente:
```bash
make test
```
*Saída atual do comando: `Testes não implementados ainda`*

**TODO:** Implementar os testes unitários e de integração na pasta `tests/` e atualizar o comando `make test` para executar `pytest`. O workflow do GitHub Actions já tenta executar `pytest tests/`, mas o diretório parece não existir ou estar vazio.

---

## 9. CI/CD

O projeto utiliza **GitHub Actions** para integração e deploy contínuos. O workflow principal está em `.github/workflows/deploy-gcp-free-tier.yml` e executa os seguintes passos em cada push para a branch `main`:

1.  **Testes e Qualidade**:
    - Instala dependências.
    - Executa linters (`black`, `flake8`).
    - Roda a suíte de testes com `pytest`.
2.  **Scan de Segurança**:
    - Utiliza o **Trivy** para escanear o código em busca de vulnerabilidades conhecidas.
3.  **Build & Deploy**:
    - Autentica-se no GCP.
    - Faz o build da imagem Docker usando o **Cloud Build**.
    - Envia a imagem para o **Artifact Registry**.
    - Realiza o deploy de uma nova revisão no **Cloud Run**, buscando os segredos do Secret Manager.
4.  **Smoke Tests**:
    - Verifica se os endpoints `/health` e `/ping` da nova versão estão respondendo corretamente.
5.  **Notificação**:
    - Informa o status final do deploy.

---

## 10. Licença

**TODO:** Definir e adicionar um arquivo de licença ao projeto. O `README.md` original sugere uma licença para fins educacionais e de portfólio, como a MIT License.
