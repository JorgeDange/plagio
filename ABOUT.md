# IMETRO TFC v3 — Sistema de Gestão e Detecção de Plágio Académico

## Visão Geral

O **IMETRO TFC v3** é uma plataforma web completa desenvolvida para universidades angolanas, projectada para gerir Trabalhos de Conclusão de Curso (TCC) e detectar plágio académico através de múltiplas fases de análise com Inteligência Artificial.

O sistema opera num modelo de verificação escalonada em três fases, combinando pesquisa externa em repositórios académicos, comparação semântica com embeddings e análise profunda com modelos de linguagem avançados (LLM).

---

## Arquitectura do Sistema

### Stack Tecnológico

| Componente | Tecnologia |
|---|---|
| Backend | Python 3.12, Flask 3.x |
| Base de Dados | PostgreSQL 14+ (Render Managed) |
| Embeddings | OpenRouter API (qwen3-embedding-8b) |
| LLM (Fase 2) | Ollama / OpenAI GPT-4o / Anthropic Claude |
| Frontend | Jinja2, CSS3, JavaScript, Chart.js, Boxicons |
| Autenticação | Flask-Login, Flask-Bcrypt |
| Servidor WSGI | Gunicorn |

### Blueprints (13 módulos)

| Blueprint | URL | Acesso |
|---|---|---|
| `auth` | `/auth` | Público |
| `main` | `/` | Autenticado |
| `cursos` | `/cursos` | Administrador |
| `orientadores` | `/orientadores` | Administrador |
| `tcc_validos` | `/tcc-validos` | Administrador |
| `tcc_suspeitos` | `/tcc-suspeitos` | Carregador+ |
| `verificacoes` | `/verificacoes` | Verificador+ |
| `pesquisa_individual` | `/pesquisa-individual` | Verificador+ |
| `normas` | `/normas` | Verificador+ |
| `aprovacoes` | `/aprovacoes` | Aprovador+ |
| `analise_ia` | `/ia` | Administrador |
| `configuracoes` | `/configuracoes` | Administrador |
| `utilizadores` | `/utilizadores` | Administrador |
| `api` | `/api` | Autenticado |

### Base de Dados (PostgreSQL — 20 tabelas)

| Tabela | Descrição |
|---|---|
| `cursos` | Cursos e departamentos |
| `orientadores` | Professores orientadores |
| `tcc_validos` | Repositório de referência |
| `tcc_suspeitos` | TCC submetidos para verificação |
| `utilizadores` | Contas de acesso (RBAC) |
| `verificacoes` | Resultados de cada verificação |
| `matches` | Fontes de similaridade encontradas |
| `chunks_suspeitos` | Trechos comparados lado a lado |
| `analises_ia` | Resultados da Fase 2 (LLM) |
| `embeddings_chunks` | Vectores de embedding |
| `fontes_externas` | Registo de pesquisas externas |
| `fontes_externas_resultados` | Resultados da Fase 0 |
| `verificacoes_normas` | Verificação normativa |
| `verificacoes_normas_infracoes` | Infracções normativas |
| `veredictos_finais` | Decisões de aprovação/rejeição |
| `configuracoes` | Configurações do sistema |
| `config_pesquisa_externa` | Configurações da Fase 0 |
| `pesquisas_avulsas` | Histórico de pesquisas |
| `resultados_pesquisa` | Resultados de pesquisas |
| `sessoes_pesquisa` | Sessões de pesquisa |

---

## Motor de Detecção de Plágio

### Pipeline de Verificação (3 Fases)

```
Fase 0: Pesquisa Externa (Opcional)
   │  CORE, OpenAlex, Serper (Google), Semantic Scholar, RCAAP, arXiv
   ▼
Fase 1: Embeddings Semânticos
   │  OpenRouter API (qwen3-embedding-8b) + PostgreSQL
   ▼
Fase 2: Análise Profunda LLM (Opcional)
      Ollama / OpenAI GPT-4o / Anthropic Claude
```

### Configurações do Motor

| Parâmetro | Valor Padrão | Descrição |
|---|---|---|
| `LIMIAR_PLAGIO` | 0.85 | Limiar de similaridade para alerta |
| `CHUNK_SIZE` | 200 | Tamanho do chunk (palavras) |
| `CHUNK_OVERLAP` | 50 | Sobreposição entre chunks |
| `OPENROUTER_EMBEDDING_MODEL` | qwen3-embedding-8b | Modelo de embeddings |

### Classificação de Plágio

| Nível | Faixa | Acção |
|---|---|---|
| Baixo | 0% — 10% | Sem indiciação significativa |
| Moderado | 10% — 30% | Revisão manual recomendada |
| Alto | 30% — 70% | Investigação obrigatória |
| Crítico | > 70% | Bloqueio automático |

---

## Sistema de Autenticação e Permissões (RBAC)

### Papéis

| Papel | Permissões |
|---|---|
| **Administrador** | Acesso total ao sistema |
| **Carregador** | Submeter TCC, ver seus envios |
| **Verificador** | Executar verificações, ver resultados |
| **Aprovador** | Aprovar/rejeitar TCC verificados |

### Fluxo de Login

1. Utilizador acede a `/auth/login`
2. Submete email + password
3. Sistema verifica hash bcrypt
4. Cria sessão Flask-Login (cookie)
5. Redireciona para dashboard conforme o papel

---

## Verificação de Normas

### Normas Suportadas

| Norma | Modo | Descrição |
|---|---|---|
| IMETRO 2014 | Local + IA | 16 regras estruturais + análise semântica |
| ABNT (NBR) | Local | NBR 14724, 10520, 6024, 6028 |
| APA 7ª Edição | Local | Estrutura, citações, formatação |

---

## Variáveis de Ambiente

### Obrigatórias

| Variável | Descrição | Exemplo |
|---|---|---|
| `FLASK_APP` | Ponto de entrada | `run.py` |
| `FLASK_ENV` | Ambiente | `production` |
| `FLASK_SECRET_KEY` | Chave secreta (auto-gerada) | `xxxxx` |
| `DATABASE_URL` | URL PostgreSQL (auto-gerada) | `postgresql://...` |
| `PGHOST` | Host PostgreSQL (auto-gerado) | `dpg-xxx.render.com` |
| `PGUSER` | Utilizador PostgreSQL (auto) | `plagio_user` |
| `PGPASSWORD` | Password PostgreSQL (auto) | `xxxxx` |
| `PGDATABASE` | Nome da BD PostgreSQL (auto) | `plagio` |
| `PGPORT` | Porta PostgreSQL (auto) | `5432` |

### API (Obrigatórias)

| Variável | Descrição |
|---|---|
| `OPENROUTER_API_KEY` | Chave OpenRouter para embeddings |

### API (Opcionais)

| Variável | Descrição |
|---|---|
| `SERPER_API_KEY` | Chave Serper para pesquisa Google |
| `LLM_PROVIDER` | Provedor LLM (ollama/openai/anthropic) |
| `LLM_MODEL` | Modelo LLM a utilizar |
| `LLM_API_KEY` | Chave API do LLM |

### Motor de Plágio

| Variável | Valor Padrão |
|---|---|
| `LIMIAR_PLAGIO` | `0.85` |
| `CHUNK_SIZE` | `200` |
| `CHUNK_OVERLAP` | `50` |

---

## Métricas de Deploy no Render

### Configuração do Serviço

| Parâmetro | Valor Recomendado |
|---|---|
| **Runtime** | Python |
| **Plan** | Free (para testes) / Starter (produção) |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn run:app` |
| **Health Check Path** | `/auth/login` |

### Limitações do Plano Gratuito

| Recurso | Limite | Notas |
|---|---|---|
| RAM | 512 MB | Suficiente para operação básica |
| CPU | Shared | Processos podem ser lentos |
| Tempo de execução | 750 h/mês | App dorme após 15 min de inatividade |
| Transferência | 100 GB/mês | Monitorizar uso |
| Deploy | Automático a cada push | GitHub integration |
| Spin down | Após 15 min sem tráfego | Primeiro pedido demora ~30s |

### Limitações do Plano Starter ($7/mês)

| Recurso | Limite | Notas |
|---|---|---|
| RAM | 512 MB | Igual ao free |
| CPU | Shared | Igual ao free |
| Tempo de execução | Ilimitado | App sempre activa |
| Transferência | 100 GB/mês | Suficiente para maioria |
| Custom domains | Sim | HTTPS automático |
| Keep alive | Sim | Não adormece |

### Métricas de Performance Esperadas

| Métrica | Plano Gratuito | Plano Starter |
|---|---|---|
| Tempo de resposta (login) | 30s (cold) / 2s (warm) | 2s (sempre) |
| Tempo de resposta (dashboard) | 10s (cold) / 1s (warm) | 1s (sempre) |
| Tempo de verificação (1 TCC) | 60-120s | 30-60s |
| Tempo de verificação normas | 10-30s | 5-15s |
| Throughput simultâneo | 1-2 pedidos | 5-10 pedidos |

### Variáveis de Ambiente Obrigatórias para Deploy

```env
# Flask
FLASK_APP=run.py
FLASK_ENV=production

# PostgreSQL (auto-geradas pelo Render)
DATABASE_URL=<auto>
PGHOST=<auto>
PGUSER=<auto>
PGPASSWORD=<auto>
PGDATABASE=plagio
PGPORT=5432

# API OpenRouter (obrigatório)
OPENROUTER_API_KEY=sk-or-v1-xxxxx

# Motor de Plágio (opcionais)
LIMIAR_PLAGIO=0.85
CHUNK_SIZE=200
CHUNK_OVERLAP=50
```

### Estrutura de Pastas Esperada no Repositório

```
repositorio/
├── render.yaml              # Configuração Render
├── build.sh                 # Script de build
├── requirements.txt         # Dependências Python
├── run.py                   # Ponto de entrada
├── app/                     # Código da aplicação
│   ├── __init__.py
│   ├── blueprints/
│   ├── database/
│   ├── services/
│   ├── static/
│   └── templates/
├── core/                    # Módulos core
├── db/                      # Schema e migrações
│   ├── schema_postgresql.sql
│   └── migrations/
└── scripts/                 # Scripts utilitários
    └── criar_admin.py
```

### Comandos Úteis para Monitorização

```bash
# Ver logs no Render
# Aceder ao painel > Logs

# Verificar estado da BD
# Aceder ao Shell > psql

# Criar administrador
python scripts/criar_admin.py

# Testar conexão BD
python -c "from app.database.db import get_db; db=get_db(); print('OK')"
```

### Checklist de Deploy

- [ ] Repositório GitHub criado com todos os ficheiros
- [ ] `.gitignore` configurado (sem `__pycache__`, `.env`, `uploads/`)
- [ ] Base de Dados PostgreSQL criada no Render
- [ ] Web Service criado e conectado ao GitHub
- [ ] Variáveis de ambiente configuradas
- [ ] `OPENROUTER_API_KEY` adicionada
- [ ] Build executado com sucesso
- [ ] Schema PostgreSQL criado automaticamente
- [ ] Administrador criado via Shell
- [ ] Login funcional testado
- [ ] Verificação de plágio testada

### Passos de Deploy

1. **Criar repositório GitHub**
   ```bash
   cd deploy_render
   git init
   git add .
   git commit -m "feat: IMETRO TFC v3 - Deploy Render"
   git remote add origin https://github.com/USER/imetro-tfc.git
   git push -u origin main
   ```

2. **Criar PostgreSQL no Render**
   - New + → PostgreSQL
   - Name: `imetro-db`
   - Database: `plagio`
   - Plan: Free

3. **Criar Web Service no Render**
   - New + → Web Service
   - Conectar repositório GitHub
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn run:app`

4. **Configurar Variáveis de Ambiente**
   - Copiar variáveis do PostgreSQL para o Web Service
   - Adicionar `OPENROUTER_API_KEY`

5. **Criar Administrador**
   ```bash
   # No Shell do Render
   python scripts/criar_admin.py
   ```

6. **Testar Sistema**
   - Aceder à URL do Web Service
   - Fazer login com credenciais do administrador
   - Testar funcionalidades principais

### Troubleshooting

| Erro | Causa | Solução |
|---|---|---|
| `TemplateNotFound` | Templates não commitados | Verificar `.gitignore`, fazer push |
| `Database connection refused` | BD não existe ou credenciais erradas | Verificar variáveis PG* |
| `Module not found` | Dependência em falta | Verificar `requirements.txt` |
| `Application failed to respond` | Build falhou | Verificar logs do Render |
| `502 Bad Gateway` | App crashou | Verificar logs, variáveis |
| `Spin down` | App adormeceu | Normal no plano gratuito |
| `H12 Request Timeout` | Request demorou >30s | Otimizar código ou usar plano pago |

### Notas Importantes

- **NÃO** committar ficheiros `.env` com senhas reais
- **NÃO** committar `uploads/`, `relatorios/`, `chroma_data/`
- **NÃO** committar `__pycache__/`, `.venv/`
- **NÃO** usar `debug=True` em produção
- **SIM** usar `gunicorn` como servidor WSGI
- **SIM** usar variáveis de ambiente para configuração
- **SIM** criar backup regular da base de dados

---

*Documentação gerada em Julho 2026 — IMETRO TFC v3*
