# 🚀 Deploy no Render.com (Plano Gratuito - PostgreSQL)

Guia passo a passo para hospedar o IMETRO TFC v3 no Render.com.

---

## Pré-requisitos

- Conta no [GitHub](https://github.com)
- Conta no [Render.com](https://render.com)
- Chave de API [OpenRouter](https://openrouter.ai/keys) (para embeddings)

---

## Passo 1: Preparar o Repositório GitHub

1. Criar um repositório no GitHub
2. Copiar todos os ficheiros da pasta `deploy_render/` para o repositório
3. Fazer push para o GitHub

**Ficheiros importantes que devem estar no repositório:**
```
├── render.yaml          ← Configuração do Render
├── build.sh             ← Script de build
├── requirements.txt     ← Dependências Python
├── run.py               ← Ponto de entrada
├── app/                 ← Código da aplicação
├── core/                ← Módulos core
├── db/                  ← Migrações SQL
└── scripts/             ← Scripts utilitários
```

---

## Passo 2: Criar a Base de Dados PostgreSQL no Render

1. Login no [Render.com](https://render.com)
2. Clicar em **"New +"** → **"PostgreSQL"**
3. Configurar:
   - **Name**: `imetro-db`
   - **Database**: `plagio`
   - **Plan**: Free
4. Clicar em **"Create Database"**
5. **Anotar** as credenciais geradas:
   - Internal Database URL
   - Database Name
   - User
   - Password

---

## Passo 3: Criar o Web Service

1. Clicar em **"New +"** → **"Web Service"**
2. Conectar ao repositório GitHub
3. Configurar:
   - **Name**: `imetro-tfc`
   - **Runtime**: Python
   - **Plan**: Free
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:app`

---

## Passo 4: Configurar Variáveis de Ambiente

No painel do Web Service, ir à secção **"Environment"** e adicionar:

### Variáveis Obrigatórias

| Chave | Valor | Descrição |
|---|---|---|
| `FLASK_APP` | `run.py` | Ponto de entrada |
| `FLASK_ENV` | `production` | Ambiente |
| `FLASK_SECRET_KEY` | *(gerar aleatória)* | Chave secreta |
| `DATABASE_URL` | *(copiar do Render)* | URL de conexão PostgreSQL |
| `PGHOST` | *(da BD)* | Host PostgreSQL |
| `PGUSER` | *(da BD)* | Utilizador |
| `PGPASSWORD` | *(da BD)* | Password |
| `PGDATABASE` | `plagio` | Nome da BD |
| `PGPORT` | `5432` | Porta |

### Variáveis de API (Obrigatórias)

| Chave | Valor | Descrição |
|---|---|---|
| `OPENROUTER_API_KEY` | `sk-or-v1-xxxxx` | Chave OpenRouter |
| `OPENROUTER_EMBEDDING_MODEL` | `qwen/qwen3-embedding-8b` | Modelo embeddings |
| `OPENROUTER_EMBEDDING_URL` | `https://openrouter.ai/api/v1/embeddings` | Endpoint |
| `OPENROUTER_TIMEOUT_SECONDS` | `30` | Timeout |
| `OPENROUTER_MAX_RETRIES` | `3` | Tentativas |

### Variáveis Opcionais

| Chave | Valor | Descrição |
|---|---|---|
| `LIMIAR_PLAGIO` | `0.85` | Limiar de plágio |
| `CHUNK_SIZE` | `200` | Tamanho do chunk |
| `CHUNK_OVERLAP` | `50` | Sobreposição |
| `SERPER_API_KEY` | `xxxxx` | Chave Serper (opcional) |

---

## Passo 5: Criar o Administrador

Após o primeiro deploy, aceder ao terminal do Render:

1. No painel do Web Service, ir a **"Shell"**
2. Executar:
   ```bash
   python scripts/criar_admin.py
   ```
3. Inserir email e password do administrador

---

## Passo 6: Aceder ao Sistema

1. No painel do Web Service, copiar a URL (ex: `https://imetro-tfc.onrender.com`)
2. Abrir no navegador
3. Fazer login com as credenciais do administrador

---

## ⚠️ Limitações do Plano Gratuito

| Limitação | Impacto | Solução |
|---|---|---|
| **Spin down after inactivity** | App pára após 15 min sem tráfego | Primeiro pedido demora ~30s |
| **512 MB RAM** | Pode ser insuficiente para PDFs grandes | Otimizar processamento |
| **750 horas/mês** | Limite de tempo de execução | Monitorizar uso |
| **100 GB transferência** | Limite de dados | Monitorizar uso |

---

## 🔧 Resolver Problemas Comuns

### Erro: "Application failed to respond"
- Verificar logs no painel do Render
- Confirmar que `gunicorn run:app` está correto
- Verificar variáveis de ambiente

### Erro: "Database connection refused"
- Confirmar que a BD PostgreSQL está a correr
- Verificar credenciais PG* e DATABASE_URL
- Verificar se o IP está na whitelist

### Erro: "Module not found"
- Verificar se todos os ficheiros estão no repositório
- Confirmar que requirements.txt está atualizado

### Primeiro pedido demora muito
- **Normal no plano gratuito** - a app "adormece" após inatividade
- O Render "acorda" a app automaticamente quando há tráfego
- Considere usar um "ping" periódico para manter ativo

---

## 📋 Checklist de Deploy

- [ ] Repositório GitHub criado e com todos os ficheiros
- [ ] Base de Dados PostgreSQL criada no Render
- [ ] Web Service criado e conectado ao GitHub
- [ ] Variáveis de ambiente configuradas
- [ ] Build executado com sucesso
- [ ] Administrador criado via Shell
- [ ] Sistema acessível e funcional

---

## 🔗 Links Úteis

- [Render.com](https://render.com)
- [Documentação Render](https://render.com/docs)
- [OpenRouter API](https://openrouter.ai)
- [PostgreSQL no Render](https://render.com/docs/databases)

---

*Guia atualizado em Julho 2026 — IMETRO TFC v3*
