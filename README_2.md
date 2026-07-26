# IMETRO TFC v3 — Documentação Completa do Sistema

## Índice

1. [Visão Geral](#1-visão-geral)
2. [Funcionalidades](#2-funcionalidades)
3. [Arquitectura Técnica](#3-arquitectura-técnica)
4. [Base de Dados](#4-base-de-dados)
5. [Sistema de Autenticação e Permissões](#5-sistema-de-autenticação-e-permissões)
6. [Motor de Detecção de Plágio](#6-motor-de-deteção-de-plágio)
7. [Pesquisa Externa (Fase 0)](#7-pesquisa-externa-fase-0)
8. [Análise de Normas](#8-análise-de-normas)
9. [Interface e Design System](#9-interface-e-design-system)
10. [Configuração e Variáveis de Ambiente](#10-configuração-e-variáveis-de-ambiente)
11. [Instalação e Execução](#11-instalação-e-execução)
12. [Mapa de Rotas](#12-mapa-de-rotas)
13. [Scripts Úteis](#13-scripts-úteis)
14. [Tecnologias Utilizadas](#14-tecnologias-utilizadas)
15. [Segurança](#15-segurança)
16. [Migrações da Base de Dados](#16-migrações-da-base-de-dados)
17. [Notas de Desenvolvimento](#17-notas-de-desenvolvimento)

---

## 1. Visão Geral

O **IMETRO TFC v3** é uma plataforma Flask para gestão académica e detecção de plágio em Trabalhos de Conclusão de Curso (TCC). Desenvolvida para universidades angolanas, combina múltiplas fases de análise:

- **Fase 0**: Pesquisa externa (CORE, OpenAlex, Serper/Google)
- **Fase 1**: Embeddings semânticos via OpenRouter API (`qwen3-embedding-8b`)
- **Fase 2**: Análise profunda com LLM (Ollama/OpenAI/Anthropic)
- **Normas**: Verificação de conformidade (IMETRO 2014, ABNT, APA)

### Stack Actual

| Componente | Tecnologia |
|---|---|
| Backend | Python 3.12, Flask 3.x |
| Base de Dados | MySQL 8.x |
| Embeddings | OpenRouter API (`qwen/qwen3-embedding-8b`) |
| LLM (Fase 2) | Ollama / OpenAI / Anthropic |
| Frontend | Jinja2, CSS3, JavaScript, Chart.js, Boxicons |
| Autenticação | Flask-Login, Flask-Bcrypt |

---

## 2. Funcionalidades

### 2.1 Detecção de Plágio em 3 Fases

| Fase | Descrição | Motor |
|---|---|---|
| **Fase 0** | Pesquisa em repositórios académicos na internet | CORE, OpenAlex, Serper (Google) |
| **Fase 1** | Comparação semântica com embeddings | OpenRouter API (`qwen3-embedding-8b`) + MySQL |
| **Fase 2** | Análise profunda com LLM | Ollama / OpenAI GPT-4o / Anthropic Claude |

### 2.2 Sistema de Papéis (RBAC)

| Papel | Permissões |
|---|---|
| **Administrador** | Acesso total: gestão de utilizadores, cursos, orientadores, TCC, verificações, aprovações, configurações |
| **Carregador** | Submeter TCC suspeitos, ver apenas seus próprios envios |
| **Verificador** | Executar verificações, consultar resultados, normas, dashboard |
| **Aprovador** | Aprovar ou rejeitar TCC verificados com justificativa |

### 2.3 Gestão Académica

- CRUD de Cursos e Departamentos
- CRUD de Professores Orientadores
- Dashboard com estatísticas e gráficos (Chart.js)

### 2.4 Verificação de Normas

| Norma | Modo | Descrição |
|---|---|---|
| **IMETRO 2014** | Local + IA | 16 regras estruturais + análise semântica |
| **ABNT (NBR)** | Local | NBR 14724, 10520, 6024, 6028 |
| **APA 7ª Edição** | Local | Estrutura, citações, formatação |

### 2.5 Pesquisa Externa Individual

Módulo independente para consultas rápidas em repositórios académicos:
- CORE, OpenAlex, Semantic Scholar, RCAAP, arXiv
- Suporta busca por ficheiro, texto ou palavras-chave
- Exportação CSV/PDF

---

## 3. Arquitectura Técnica

### 3.1 Estrutura de Blueprints

| Blueprint | URL | Acesso | Descrição |
|---|---|---|---|
| `auth` | `/auth` | Público | Login, logout, perfil |
| `main` | `/` | Autenticado | Dashboard |
| `cursos` | `/cursos` | Admin | Cursos e departamentos |
| `orientadores` | `/orientadores` | Admin | Professores orientadores |
| `tcc_validos` | `/tcc-validos` | Admin | Repositório de referência |
| `tcc_suspeitos` | `/tcc-suspeitos` | Carregador+ | Submissão e listagem |
| `verificacoes` | `/verificacoes` | Verificador+ | Motor de plágio |
| `pesquisa_individual` | `/pesquisa-individual` | Verificador+ | Pesquisa externa |
| `normas` | `/normas` | Verificador+ | Verificação normativa |
| `aprovacoes` | `/aprovacoes` | Aprovador+ | Aprovação de TCC |
| `analise_ia` | `/ia` | Admin | Configuração IA |
| `configuracoes` | `/configuracoes` | Admin | Configurações gerais |
| `utilizadores` | `/utilizadores` | Admin | Gestão de contas |
| `api` | `/api` | Autenticado | Endpoints REST |

> O símbolo **+** indica que o administrador também tem acesso.

### 3.2 Estrutura de Directorios

```
sistema_plagio/
├── app/
│   ├── __init__.py              # Application Factory
│   ├── blueprints/              # 14 blueprints Flask
│   ├── database/
│   │   └── db.py                # Camada de acesso a dados (MySQL)
│   ├── services/
│   │   └── plagio_service.py    # Lógica de negócio
│   ├── static/                  # CSS, JS, imagens
│   └── templates/               # Templates Jinja2
├── core/
│   ├── auth_helpers.py          # Decoradores RBAC
│   ├── embeddings.py            # API OpenRouter (embeddings)
│   ├── detector.py              # Motor de detecção
│   ├── chunker.py               # Divisão em chunks
│   ├── ingestor.py              # Extração de texto (PDF/DOCX)
│   ├── pesquisa_externa.py      # APIs académicas externas
│   ├── llm_analyzer.py          # Análise LLM (Fase 2)
│   ├── relatorio.py             # Geração de relatórios HTML
│   └── normas_*.py              # Módulos de normas
├── db/migrations/               # Migrações SQL
├── scripts/                     # Scripts utilitários
├── uploads/                     # Ficheiros submetidos
├── .env                         # Variáveis de ambiente
├── requirements.txt             # Dependências
└── run.py                       # Ponto de entrada
```

---

## 4. Base de Dados

### 4.1 Schema Actual (MySQL — 20 tabelas)

```
cursos ← orientadores
   ↑         ↑
tcc_validos  tcc_suspeitos → verificacoes → matches → chunks_suspeitos
   ↑              ↑                            ↓            ↓
embeddings_chunks utilizadores           analises_ia   veredictos_finais
                                    fontes_externas → fontes_externas_resultados
                                    verificacoes_normas → verificacoes_normas_infracoes
```

### 4.2 Descrição das Tabelas

| Tabela | Descrição |
|---|---|
| `cursos` | Cursos e departamentos |
| `orientadores` | Professores orientadores |
| `tcc_validos` | Repositório de TCC aprovados (referência) |
| `tcc_suspeitos` | TCC submetidos para verificação |
| `utilizadores` | Contas de acesso (papéis RBAC) |
| `verificacoes` | Resultados de cada verificação de plágio |
| `matches` | Fontes de similaridade encontradas (com evidência) |
| `chunks_suspeitos` | Trechos comparados lado a lado |
| `analises_ia` | Resultados da Fase 2 (LLM) |
| `embeddings_chunks` | Vectores de embedding (OpenRouter API) |
| `fontes_externas` | Registo de pesquisas externas |
| `fontes_externas_resultados` | Resultados detalhados da Fase 0 |
| `verificacoes_normas` | Resultados da verificação normativa |
| `verificacoes_normas_infracoes` | Infracções normativas detectadas |
| `veredictos_finais` | Decisões de aprovação/rejeição |
| `configuracoes` | Configurações do sistema |
| `config_pesquisa_externa` | Configurações da Fase 0 |
| `pesquisas_avulsas` | Histórico de pesquisas individuais |
| `resultados_pesquisa` | Resultados de pesquisas avulsas |
| `sessoes_pesquisa` | Sessões de pesquisa externa |

### 4.3 Tabela `matches` — Campos de Evidência

Cada match inclui evidência completa para verificação:

| Campo | Tipo | Descrição |
|---|---|---|
| `fonte_origem` | VARCHAR(50) | `core`, `openalex`, `serper` ou `local` |
| `titulo_fonte` | VARCHAR(500) | Título do documento encontrado |
| `url_fonte` | VARCHAR(1000) | Link para a fonte externa |
| `trecho_similar` | TEXT | Trecho da fonte externa |
| `trecho_original` | TEXT | Trecho do TCC suspeito (comparação) |

---

## 5. Sistema de Autenticação e Permissões

### 5.1 Decoradores

```python
@requer_login        # Qualquer utilizador autenticado
@requer_admin        # Apenas administrador
@requer_carregador   # Carregador OU administrador
@requer_verificador  # Verificador OU administrador
@requer_aprovador    # Aprovador OU administrador
```

### 5.2 Fluxo de Login

1. Utilizador acede a `/auth/login`
2. Submete email + password
3. Sistema verifica hash bcrypt
4. Cria sessão Flask-Login (cookie)
5. Redireciona para dashboard conforme o papel

### 5.3 Restrições por Papel

| Accão | Admin | Carregador | Verificador | Aprovador |
|---|---|---|---|---|
| Ver dashboard completa | ✅ | ❌ | ✅ | ✅ |
| Submeter TCC | ✅ | ✅ | ❌ | ❌ |
| Ver seus envios | ✅ | ✅ | ❌ | ❌ |
| Executar verificação | ✅ | ❌ | ✅ | ❌ |
| Ver resultados | ✅ | ❌ | ✅ | ✅ |
| Aprovar/rejeitar TCC | ✅ | ❌ | ❌ | ✅ |
| Gerir utilizadores | ✅ | ❌ | ❌ | ❌ |
| Apagar TCC | ✅ | ❌ | ❌ | ❌ |

---

## 6. Motor de Detecção de Plágio

### 6.1 Pipeline de Verificação

```
1. Extração de texto (PDF/DOCX/TXT)
       ↓
2. Limpeza e normalização
       ↓
3. Divisão em chunks (200 palavras, overlap 50)
       ↓
4. Geração de embeddings via OpenRouter API
       ↓
5. Comparação com embeddings armazenados (MySQL)
       ↓
6. Cálculo de cosine similarity
       ↓
7. Classificação: Baixo (<10%), Moderado (10-30%), Alto (≥30%)
```

### 6.2 Configurações

| Parâmetro | Valor Padrão | Descrição |
|---|---|---|
| `LIMIAR_PLAGIO` | 0.85 | Limiar de similaridade para alerta |
| `CHUNK_SIZE` | 200 | Tamanho do chunk (palavras) |
| `CHUNK_OVERLAP` | 50 | Sobreposição entre chunks |

### 6.3 Ficheiros Principais

| Ficheiro | Responsabilidade |
|---|---|
| `core/embeddings.py` | Geração de embeddings via OpenRouter API |
| `core/detector.py` | Comparação semântica e cálculo de similaridade |
| `core/chunker.py` | Divisão de texto em blocos |
| `core/ingestor.py` | Extração de texto de PDF/DOCX |
| `app/services/plagio_service.py` | Orquestração do fluxo |

---

## 7. Pesquisa Externa (Fase 0)

### 7.1 Fontes Disponíveis

| Fonte | API | Tipo |
|---|---|---|
| **CORE** | API REST | Repositório académico aberto |
| **OpenAlex** | API REST | Base de dados de trabalhos académicos |
| **Serper** | Google Search API | Pesquisa geral na web |
| **Semantic Scholar** | API REST | Base de dados semântica |
| **RCAAP** | API REST | Repositório português |
| **arXiv** | API REST | Preprints científicos |

### 7.2 Fluxo

```
1. Recebe texto do chunk
       ↓
2. Pesquisa em paralelo nas APIs externas
       ↓
3. Receve resultados com: título, URL, resumo, autores
       ↓
4. Gera embeddings do resumo externo
       ↓
5. Compara com embedding do chunk original
       ↓
6. Filtra por limiar de similaridade
       ↓
7. Devolve resultados com evidência completa
```

### 7.3 Evidência Guardada

Cada resultado externo inclui:
- **Fonte**: CORE, OpenAlex, Google (Serper)
- **Título**: Título do documento encontrado
- **URL**: Link directo para o documento
- **Trecho**: Resumo ou excerto do texto
- **Score**: Percentagem de similaridade semântica

---

## 8. Análise de Normas

### 8.1 Normas IMETRO 2014

**Verificação Local (16 regras):**

| Categoria | Regras |
|---|---|
| Estrutura | Resumo, Palavras-chave, Sumário, Introdução, Conclusão, Bibliografia, Dedicatória, Agradecimentos |
| Formatação | Linguagem impessoal, formatação geral |
| Citações | Sistema autor-data, uso de "apud" |
| Metodologia | Problema como pergunta, objectivos, hipóteses |

**Análise IA (Fase 2):**
- Pontuação 0-100
- Classificação: CONFORME / COM RESSALVAS / NÃO CONFORME
- Infracções: Bloqueante, Grave, Moderada, Leve
- Códigos: IMETRO-001 a IMETRO-020

### 8.2 Normas ABNT

| Norma | objectivo |
|---|---|
| NBR 14724 | Estrutura de trabalhos académicos |
| NBR 10520 | Citações e recuos |
| NBR 6024 | Numeração sem ponto final |
| NBR 6028 | Tamanho do Resumo |

### 8.3 Normas APA 7ª Edição

- Estrutura geral
- Citações com ampersand (`&`)
- Formatação de blocos longos
- Uso de `et al.`

---

## 9. Interface e Design System

### 9.1 Design System

- **Glassmorphism**: Efeitos de vidro fosco
- **Cantos arredondados**: `border-radius` consistente
- **Badges coloridos**: Por papel e estado
- **Macros Jinja2**: `campo()`, `campo_upload()`, `campo_select()`

### 9.2 Componentes

| Componente | Descrição |
|---|---|
| KPI Cards | Cartões de estatísticas no dashboard |
| Data Tables | Tabelas com pesquisa e filtros |
| Progress Bars | Barras de progresso animadas |
| Modal de Confirmação | Diálogos de confirmação |
| Alert Cards | Alertas notificativos |
| Charts | Gráficos Chart.js (barras, linhas) |

### 9.3 Paleta de Cores

| Cor | Variável | Uso |
|---|---|---|
| Azul-marinho | `--accent: #002B5C` | Cor principal |
| Branco | `--white` | Fundo, texto em botões |
| Verde | `--success` | Aprovado, conformidade |
| Amarelo | `--warning` | Pendente, parcial |
| Vermelho | `--danger` | Reprovado, não conformidade |
| Cinza | `--text-muted` | Texto secundário |

---

## 10. Configuração e Variáveis de Ambiente

### 10.1 Ficheiro `.env`

```env
# Flask
FLASK_SECRET_KEY=sua-chave-secreta
FLASK_APP=run.py
FLASK_ENV=development

# Base de Dados MySQL
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=sua-password
MYSQL_DB=plagio

# OpenRouter API (Embeddings)
OPENROUTER_API_KEY=sua-chave-api
OPENROUTER_EMBEDDING_MODEL=qwen/qwen3-embedding-8b
OPENROUTER_EMBEDDING_URL=https://openrouter.ai/api/v1/embeddings
OPENROUTER_TIMEOUT_SECONDS=30
OPENROUTER_MAX_RETRIES=3

# Serper (Google Search)
SERPER_API_KEY=sua-chave-serper
SERPER_API_URL=https://google.serper.dev/search
SERPER_TIMEOUT_SECONDS=15
SERPER_MAX_RETRIES=2

# Detecção de Plágio
LIMIAR_PLAGIO=0.85
CHUNK_SIZE=200
CHUNK_OVERLAP=50
```

### 10.2 Configurações no MySQL (tabela `configuracoes`)

| Chave | Valor Padrão | Descrição |
|---|---|---|
| `LLM_ENABLED` | `false` | Activar/desactivar Fase 2 |
| `LLM_PROVIDER` | `ollama` | Provedor: ollama/openai/anthropic |
| `LLM_MODEL` | `llama3` | Modelo LLM a utilizar |
| `LLM_SCORE_THRESHOLD` | `0.75` | Limiar para activar Fase 2 |

---

## 11. Instalação e Execução

### 11.1 Pré-requisitos

- Python 3.10+
- MySQL 8.x
- pip

### 11.2 Passos de Instalação

```bash
# 1. Criar ambiente virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate      # Linux/macOS

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar variáveis de ambiente
# Editar .env com as vossas credenciais

# 4. Criar base de dados MySQL
mysql -u root -p -e "CREATE DATABASE plagio CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"

# 5. Executar migrações (ver db/migrations/)

# 6. Criar administrador
python scripts/criar_admin.py

# 7. Iniciar servidor
python run.py
```

### 11.3 URLs de Acesso

| URL | Descrição |
|---|---|
| `http://127.0.0.1:5000` | Página principal |
| `http://127.0.0.1:5000/auth/login` | Login |

---

## 12. Mapa de Rotas

### 12.1 Autenticação

| Método | Rota | Descrição |
|---|---|---|
| GET/POST | `/auth/login` | Login |
| GET | `/auth/logout` | Logout |
| GET | `/auth/perfil` | Perfil do utilizador |
| POST | `/auth/perfil` | Actualizar perfil |
| POST | `/auth/alterar-password` | Alterar password |

### 12.2 Dashboard

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Dashboard principal |

### 12.3 TCC Válidos

| Método | Rota | Descrição |
|---|---|---|
| GET | `/tcc-validos` | Listar TCC válidos |
| GET/POST | `/tcc-validos/adicionar` | Adicionar TCC válido |
| GET | `/tcc-validos/<id>` | Detalhe do TCC |
| POST | `/tcc-validos/<id>/remover` | Remover TCC |

### 12.4 TCC Suspeitos

| Método | Rota | Descrição |
|---|---|---|
| GET | `/tcc-suspeitos` | Listar TCC suspeitos |
| GET/POST | `/tcc-suspeitos/submeter` | Submeter TCC |
| GET | `/tcc-suspeitos/<id>` | Detalhe do TCC |
| POST | `/tcc-suspeitos/<id>/estado` | Mudar estado |
| POST | `/tcc-suspeitos/<id>/remover` | Remover TCC |

### 12.5 Verificações

| Método | Rota | Descrição |
|---|---|---|
| GET | `/verificacoes` | Histórico de verificações |
| POST | `/verificacoes/verificar/<id>` | Iniciar verificação |
| GET | `/verificacoes/resultado/<id>` | Ver resultado |
| GET | `/verificacoes/descarregar/<id>` | Descarregar relatório |
| POST | `/verificacoes/<id>/observacao` | Guardar observação |

### 12.6 Normas

| Método | Rota | Descrição |
|---|---|---|
| GET | `/normas` | Página de normas |
| POST | `/normas/verificar` | Verificar normas |

### 12.7 Aprovações

| Método | Rota | Descrição |
|---|---|---|
| GET | `/aprovacoes` | TCC para aprovação |
| POST | `/aprovacoes/<id>/decidir` | Aprovar/rejeitar |

### 12.8 Pesquisa Individual

| Método | Rota | Descrição |
|---|---|---|
| GET | `/pesquisa-individual` | Módulo de pesquisa |
| POST | `/pesquisa-individual/pesquisar` | Executar pesquisa |

### 12.9 Configurações

| Método | Rota | Descrição |
|---|---|---|
| GET | `/configuracoes` | Painel de configurações |
| POST | `/configuracoes/guardar` | Guardar configurações |
| GET | `/configuracoes/exportar-db` | Exportar base de dados |

### 12.10 Utilizadores

| Método | Rota | Descrição |
|---|---|---|
| GET | `/utilizadores` | Listar utilizadores |
| GET/POST | `/utilizadores/novo` | Criar utilizador |
| GET/POST | `/utilizadores/<id>/editar` | Editar utilizador |
| POST | `/utilizadores/<id>/remover` | Remover utilizador |
| POST | `/utilizadores/<id>/reset-password` | Redefinir password |

---

## 13. Scripts Úteis

| Script | Descrição |
|---|---|
| `scripts/criar_admin.py` | Criar primeiro administrador |
| `scripts/testar_openrouter_embeddings.py` | Testar API OpenRouter |
| `scripts/testar_serper.py` | Testar API Serper |
| `scripts/migrar_sqlite_para_mysql.py` | Migrar dados de SQLite para MySQL |

---

## 14. Tecnologias Utilizadas

### 14.1 Backend

| Tecnologia | Versão | Uso |
|---|---|---|
| Python | 3.12 | Linguagem principal |
| Flask | 3.x | Framework web |
| MySQL | 8.x | Base de dados |
| mysql-connector-python | 8.0+ | Driver MySQL |

### 14.2 Autenticação

| Tecnologia | Uso |
|---|---|
| Flask-Login | Gestão de sessões |
| Flask-Bcrypt | Hash de passwords |

### 14.3 Inteligência Artificial

| Tecnologia | Uso |
|---|---|
| OpenRouter API | Geração de embeddings (`qwen3-embedding-8b`) |
| Ollama | LLM local (Fase 2) |
| OpenAI | LLM na nuvem (Fase 2) |
| Anthropic | LLM na nuvem (Fase 2) |

### 14.4 Frontend

| Tecnologia | Uso |
|---|---|
| Jinja2 | Templates |
| CSS3 | Estilos (Glassmorphism) |
| JavaScript | Interatividade |
| Chart.js | Gráficos |
| Boxicons | Iconografia |

### 14.5 Dependências (requirements.txt)

```
Flask==3.0.3
Flask-Login==0.6.3
Flask-Bcrypt==1.0.1
python-dotenv==1.0.1
requests==2.32.3
PyMuPDF==1.24.5
python-docx==1.1.2
numpy<2
mysql-connector-python>=8.0
```

---

## 15. Segurança

### 15.1 Medidas Implementadas

- **Passwords**: Hash bcrypt (nunca em texto claro)
- **Sessões**: Cookies Flask com `SECRET_KEY`
- **Validação**: Password mínima de 8 caracteres
- **Proteção**: Impede desactivação do último admin
- **Logging**: Tentativas de acesso não autorizado
- **RBAC**: Controlo de acesso por papel

### 15.2 Única Rota Pública

- `/auth/login` — Todas as outras rotas exigem autenticação

---

## 16. Migrações da Base de Dados

| Migração | Descrição |
|---|---|
| `v4_add_users.sql` | Sistema RBAC (utilizadores, papéis) |
| `v5_fontes_externas.sql` | Tabelas para Fase 0 (pesquisa externa) |
| `v6_resultados_normas.sql` | Tabelas de verificação normativa |
| `v7_normas_na_verificacao.sql` | Integração de normas no fluxo de plágio |
| `v8_adicionar_campos.sql` | Campos adicionais |
| `v9_embeddings_mysql.sql` | Migração de embeddings para MySQL |
| `v10_evidencia_matches.sql` | Evidência de similaridade em matches |

---

## 17. Notas de Desenvolvimento

### 17.1 Migração de SQLite para MySQL

O sistema migrou de SQLite para MySQL. Algumas notas:
- Todas as queries usam `%s` (placeholder MySQL) em vez de `?` (SQLite)
- Conexões MySQL com `autocommit=False`
- Funções `get_db()` usam Flask `g` (request-scoped)

### 17.2 Embeddings

- Vector de 4096 dimensões (`qwen3-embedding-8b`)
- Serializado como JSON no MySQL
- Armazenado na tabela `embeddings_chunks`

### 17.3 Threading

- Verificações correm em threads separadas
- Usam `app.app_context()` para aceder a Flask `g`
- Funções de base de dados têm fallback para conexão direta quando fora de contexto Flask

### 17.4 Encoding

- Windows usa `cp1252` por padrão
- Evitar caracteres Unicode (✓, ✗) em prints
- Usar `encoding='utf-8'` em ficheiros

---

*Documentação gerada em Julho 2026 — IMETRO TFC v3*
