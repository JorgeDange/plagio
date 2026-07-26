# 🎓 IMETRO TFC v3 — Sistema de Gestão e Detecção de Plágio Académico

O **IMETRO TFC v3** é uma plataforma local completa de gestão académica e verificação inteligente de similaridade, desenvolvida especialmente para Universidades Angolanas. O sistema utiliza Inteligência Artificial avançada (modelos semânticos) para cruzar Trabalhos de Conclusão de Curso (TCC) submetidos contra um repositório seguro de trabalhos aprovados, operando nativamente em infraestruturas locais sem dependência da internet.

---

## 🌟 Principais Funcionalidades

### 1. Motor Analítico Híbrido em Três Fases (IA)
A detecção de plágio no IMETRO TFC opera de forma escalonada para máxima precisão e economia de processamento:
- **Fase 0 (Pesquisa Externa — Opcional):** Antes da verificação local, o sistema pesquisa blocos do texto em repositórios académicos na internet (como CORE, OpenAlex, Semantic Scholar, RCAAP e arXiv). Descarrega resumos de trabalhos suspeitos e compara semanticamente, permitindo detectar plágio de fontes que não estão na base da universidade.
- **Fase 1 (Motor Semântico Local):** Utiliza o modelo `Sentence-Transformers/LaBSE` do Google e a base de dados vectorial `ChromaDB` para comparar blocos de texto (chunks) vectorialmente. Detecta sinónimos e mudanças na ordem das palavras. Corre 100% offline e não necessita de placa gráfica.
- **Fase 2 (Análise Profunda LLM - Unimetro Analista):** O novo módulo integrado (`core/llm_analyzer.py`) actua como o "Unimetro Analista". Chunks com suspeita forte (score > 0.75 na Fase 1) são enviados para um modelo de linguagem avançado. Suporta nativamente integrações com **Anthropic Claude**, **OpenAI GPT-4o** ou modelos executados localmente (100% offline e sem custos) via **Ollama**. A IA atua com um *prompt* validado como perito universitário, exigindo o retorno estruturado (JSON robusto) com o veredicto exato (ex: *Cópia directa*, *Tradução disfarçada*, *Mosaico*), nível de gravidade, similaridade contextual e uma justificativa rigorosa baseada nas normas académicas.

### 2. Sistema de Autenticação e Controlo de Acesso (RBAC)
O IMETRO TFC v3 implementa um sistema completo de **Role-Based Access Control** com quatro papéis hierárquicos, garantindo que cada utilizador vê e executa apenas o que lhe compete:

| Papel | Cor do Badge | Permissões Principais |
|:------|:-------------|:----------------------|
| 🟣 **Administrador** | Roxo | Acesso total — gestão de utilizadores, cursos, orientadores, TCC, verificações, aprovações, configurações de IA, exportação de BD |
| 🟢 **Carregador** | Teal | Submeter TCC suspeitos para verificação e consultar os seus próprios envios |
| 🟠 **Verificador** | Âmbar | Executar verificações de plágio, consultar resultados, relatórios, normas ABNT/APA e dashboard de verificação |
| 🟩 **Aprovador** | Verde | Decisão final sobre TCC já verificados — aprovar ou rejeitar com nota justificativa |

**Detalhes técnicos:**
- Autenticação via sessões Flask (cookies) com `Flask-Login`
- Passwords com hash `bcrypt` (mínimo 8 caracteres)
- Protecção contra desactivação do último administrador activo
- Menu lateral dinâmico — adapta-se ao papel do utilizador autenticado
- Barra superior com nome, badge do papel e dropdown (perfil + sair)
- `/auth/login` é a **única rota pública** — todas as restantes exigem autenticação

### 3. Dualidade de Repositórios
O sistema organiza os documentos de forma inteligente e segura em dois silos distintos:
- **📗 TCC Válidos (Base de Dados):** Repositório de trabalhos que já foram aprovados e defendidos com sucesso pela universidade. Servem como base de referência e treino para o sistema.
- **📕 TCC Suspeitos (Para Verificação):** Trabalhos novos que os estudantes submetem e que estão pendentes de avaliação para ver se cometeram plágio em relação aos TCC Válidos.

### 4. Workflow de Verificação em Tempo Real (Multithreading)
- Quando um TCC é submetido para verificação, o sistema extrai o texto do PDF/DOCX, limpa-o e divide-o em blocos lógicos (*chunks*).
- O administrador visualiza uma barra de progresso interactiva enquanto o sistema executa cálculos matemáticos em segundo plano de forma assíncrona.
- Os utilizadores podem definir "Limiares de Plágio" personalizados (ex: emitir alerta apenas se a cópia for superior a 85% de similaridade semântica) e filtrar a verificação para comparar apenas contra um curso específico.

### 5. Fluxo de Aprovação de TCC
Após a verificação de plágio, os TCC passam por um fluxo de estados controlado:

```
pendente → em_verificação → verificado → aprovado / rejeitado
```

- O **verificador** executa a análise — ao concluir, o estado muda automaticamente para `verificado`
- O **aprovador** revê os resultados e emite decisão final (`aprovado` ou `rejeitado`) com nota justificativa obrigatória na rejeição
- Todo o histórico de decisões fica registado com nome do aprovador, data e justificativa

### 6. Análise de Conformidade Normativa (IMETRO 2014 + ABNT + APA)
O sistema oferece um motor de verificação normativa com **três normas académicas** e **dois modos de análise** (local + IA), cobrindo integralmente as necessidades dos TFC submetidos ao IMETRO.

#### 6.1 Normas IMETRO 2014 — Integradas na Verificação Principal
O **Regulamento e Manual de Normatização de Trabalhos Académicos do IMETRO (edição 2014)** encontra-se agora nativamente embebido no fluxo principal de anti-plágio. Sempre que um TCC é submetido, o avaliador pode com um clique acionar a validação normativa simultânea.

**Verificação Local Estrutural (Expressões Regulares):**
O motor regex (`core/normas_regras.py`) aplica **16 regras IMETRO** organizadas em 4 categorias de forma ultra-rápida, reportando falhas na estrutura (ex: ausência de Resumo, Palavras-chave ou Conclusão) e formatação geral.

| Categoria | Regras Verificadas |
|:----------|:-------------------|
| **Estrutura** | Resumo (120–150 palavras), Palavras-chave (exatamente 3), Sumário, Introdução, Conclusão, Bibliografia, Dedicatória, Agradecimentos |
| **Formatação** | Linguagem impessoal (proibição da 1ª pessoa do singular), formatação geral (manual) |
| **Citações** | Sistema autor-data, uso restrito de "apud" |
| **Metodologia** | Problema formulado como pergunta (?), objetivo geral + específicos, hipótese(s) |

**Análise Semântica Aprofundada (IA):**
De forma opcional, o **Unimetro Inspector** (`core/normas_imetro_checker.py`) envia o TFC para um LLM (Ollama/OpenAI/Anthropic). A IA atua como um professor exigente e entrega uma tabela rica:
- Pontuação 0–100 e Classificação Final (**CONFORME**, **COM RESSALVAS** ou **NÃO CONFORME**)
- Detecção de Infracções (Bloqueante/Grave/Moderada/Leve) referenciando os códigos (IMETRO-001 a IMETRO-020)
- Análise semântica da Metodologia Científica e coerência estrutural

> Os resultados da avaliação normativa (Local e IA) aparecem num **separador dedicado** diretamente na página de resultados da verificação de originalidade, bem como no histórico e no dashboard de Aprovações.

#### 6.2 Normas ABNT e APA — Verificação Local
- **Análise Simultânea Dupla:** Ao submeter um documento em `/normas/verificar`, o motor audita automaticamente as regras da **Norma ABNT (NBR)** e da **Norma APA (7ª Edição)** ao mesmo tempo, emitindo um relatório lado a lado em duas colunas.
- **Dicionário ABNT Rigoroso:** Cobre a NBR 14724 (Estrutura de Capa, Introdução, Sumário), NBR 10520 (Citações e recuos), NBR 6024 (Regras de Numeração sem ponto final) e NBR 6028 (Tamanho exato do Resumo).
- **Dicionário APA 7:** Valida estrutura geral, obrigatoriedade de ampersand (`&`) em citações dentro de parênteses, formatação de blocos longos de texto e restrições de uso do `et al.`.
- **Relatórios Integrados:** Os índices percentuais de conformidade de ambas as normas acompanham o processo de plágio e são incluídos nos Relatórios PDF/HTML.
- **Linguagem Amigável:** Marcadores diretos ("Obrigatório corrigir", "Sugestões de melhoria") e mensagens explicativas.
- **Central de Referência:** Guia rápido de ambas as normas com exemplos estruturais em `Referência Rápida`.

### 7. Gestão Académica (Cursos e Orientadores)
O IMETRO TFC v3 deixou de ser apenas um "script de terminal" e tornou-se um ecossistema. Permite:
- Gerir Cursos, Departamentos e Professores Orientadores.
- Obter estatísticas globais (Dashboard com gráficos `Chart.js`) sobre os níveis de originalidade média por curso.
- Saber que professores estão a orientar os trabalhos com maiores taxas de plágio.

### 8. Gestão de Utilizadores (apenas Administrador)
O administrador tem acesso a um painel completo de gestão de contas:
- Criar, editar e desactivar utilizadores
- Atribuir papéis (administrador, carregador, verificador, aprovador)
- Redefinir passwords de qualquer utilizador
- Protecção automática: o sistema impede a desactivação do último administrador activo

### 9. Relatórios Dinâmicos e Detalhados
Gera relatórios HTML exportáveis e exibe no *dashboard* web a secção exata (lado a lado) onde o sistema acusou a cópia:
- **Texto do Suspeito** vs **Texto do Autor Original**.
- **Justificativas do Unimetro Analista:** Se a IA (Fase 2) estiver activa, cada trecho exibe um crachá com o tipo de plágio (Ex: *Tradução disfarçada*) e uma justificação técnica detalhada por baixo dos textos comparados.

### 10. Interface Moderna e Design System de Formulários
- Implementação de um **Design System de Formulários** unificado, suportado por macros Jinja2 avançadas (`campo`, `campo_upload`, `campo_select`) que garantem consistência total no layout, interatividade (contadores de caracteres e estado de botões dinâmicos) e feedback visual em todo o portal.
- Áreas inteligentes de *Drag & Drop* para submissão e processamento em lote de múltiplos ficheiros.
- Interface de classe empresarial baseada nos princípios de Glassmorphism e cantos arredondados, partilhando o aspecto estético de painéis educativos contemporâneos.
- Painel de Configurações dedicado à IA, permitindo ligar/desligar o LLM, seleccionar o motor (Ollama/OpenAI) e ajustar limiares de verificação.
- Construído com `Jinja2`, CSS Customizado (`forms.css`), Javascript optimizado (`forms.js`), Animações e iconografia da biblioteca `Boxicons`.

### 11. Adequação Linguística e Exportação em PDF
- **Simplificação de Linguagem:** Toda a interface do sistema foi atualizada para substituir jargões técnicos por linguagem institucional simples em PT-PT. Termos como "TCC", "Histórico", "Chunks" e "LLM" foram substituídos por "Trabalho", "Resultados Anteriores", "Trechos" e "Inteligência Artificial", garantindo uma experiência intuitiva para todos os perfis (especialmente secretaria e aprovadores sem formação técnica).
- **Exportação Otimizada:** Foi implementada a exportação rápida para PDF dos relatórios IMETRO (via CSS `@media print` elegante), alinhada com a lógica de exportação dos demais módulos, gerando documentos PDF limpos e prontos para arquivo académico.

### 12. Módulo de Pesquisa Externa Individual
O IMETRO TFC v3 oferece um módulo independente de "Pesquisa Externa Individual", ideal para consultas rápidas na internet fora do fluxo oficial de avaliação de TCC.
- **Entrada Flexível:** Aceita submissão por ficheiros (PDF, DOCX, TXT), texto colado ou pesquisa direta por títulos/palavras-chave (via tabs intuitivas).
- **Múltiplas Fontes Académicas:** Pesquisa de forma agregada e paralela nas APIs do CORE, OpenAlex, Semantic Scholar, RCAAP e arXiv.
- **Resultados Consolidados:** Retorna os trabalhos filtrados por ano, idioma e percentagem de semelhança, com opções rápidas para abrir a fonte original ou copiar a sua citação.
- **Exportação e Histórico:** O módulo guarda o histórico das sessões de pesquisa e permite exportar relatórios diretos em CSV ou PDF.

---

## 🏗️ Arquitectura Técnica

### Blueprints (12 módulos)

Foi implementada uma arquitectura *Application Factory* (Flask Modular) estruturada em **12 Blueprints** independentes para manter o código escalável:

| Blueprint | Prefixo URL | Acesso | Descrição |
|:----------|:------------|:-------|:----------|
| `auth` | `/auth` | 🌐 Público | Login, logout, perfil e alteração de password |
| `main` | `/` | 🔒 Autenticado | Dashboard e estatísticas globais |
| `cursos` | `/cursos` | 🟣 Admin | CRUD de cursos e departamentos |
| `orientadores` | `/orientadores` | 🟣 Admin | CRUD de orientadores |
| `tcc_validos` | `/tcc-validos` | 🟣 Admin | Repositório seguro + indexação ChromaDB |
| `tcc_suspeitos` | `/tcc-suspeitos` | 🟢 Carregador+ | Submissão e listagem de TCC para verificação |
| `verificacoes` | `/verificacoes` | 🟠 Verificador+ | Motor de processamento de chunks e similaridade |
| `pesquisa_individual` | `/pesquisa-individual` | 🟠 Verificador+ | Módulo de consulta rápida em repositórios externos (APIs) |
| `normas` | `/normas` | 🟠 Verificador+ | Auditoria de normas IMETRO 2014, ABNT e APA (local + IA) |
| `aprovacoes` | `/aprovacoes` | 🟩 Aprovador+ | Aprovar/rejeitar TCC verificados |
| `analise_ia` | `/ia` | 🟣 Admin | Configuração da IA e Fase 2 (LLM) |
| `configuracoes` | `/configuracoes` | 🟣 Admin | Afinação do sistema e exportação |
| `utilizadores` | `/utilizadores` | 🟣 Admin | Gestão de contas de utilizadores |
| `api` | `/api` | 🔒 Autenticado | Endpoints REST JSON |

> **Nota:** O símbolo **+** indica que o administrador também tem acesso a esse blueprint.

### Base de Dados (SQLite — Schema v4)

Utiliza **9 tabelas** rigidamente normalizadas e interligadas:

```
cursos ← orientadores
   ↑         ↑
tcc_validos  tcc_suspeitos → verificacoes → matches → chunks_suspeitos
                  ↑                             ↓
            utilizadores                  analises_ia
```

| Tabela | Descrição |
|:-------|:----------|
| `cursos` | Cursos e departamentos |
| `orientadores` | Professores orientadores |
| `tcc_validos` | Repositório de TCC aprovados (com `chroma_id` para ChromaDB) |
| `tcc_suspeitos` | TCC submetidos para verificação (com `estado`, `aprovado_por`, `aprovado_em`, `nota_aprovacao`) |
| `verificacoes` | Resultados de cada execução de plágio |
| `matches` | Fontes de similaridade encontradas |
| `chunks_suspeitos` | Trechos de texto comparados lado a lado |
| `analises_ia` | Resultados da Fase 2 (LLM) por chunk |
| `utilizadores` | Contas de acesso com papéis RBAC |

### Decoradores de Permissão

O sistema utiliza 5 decoradores customizados definidos em `core/auth_helpers.py`:

```python
@requer_login        # Qualquer utilizador autenticado
@requer_admin        # Apenas administrador
@requer_carregador   # Carregador OU administrador
@requer_verificador  # Verificador OU administrador
@requer_aprovador    # Aprovador OU administrador
```

Cada tentativa de acesso negado é registada no log com o email do utilizador e a rota tentada.

---

## 📁 Estrutura de Directórios

```
sistema_plagio/
├── app/
│   ├── __init__.py              ← Application Factory (Flask-Login + Bcrypt)
│   ├── extensions.py            ← Variáveis globais partilhadas
│   ├── blueprints/
│   │   ├── auth/                ← Login, logout, perfil
│   │   ├── main/                ← Dashboard
│   │   ├── cursos/              ← CRUD cursos
│   │   ├── orientadores/        ← CRUD orientadores
│   │   ├── tcc_validos/         ← Repositório seguro
│   │   ├── tcc_suspeitos/       ← Submissão de TCC
│   │   ├── verificacoes/        ← Motor de plágio
│   │   ├── normas/              ← Normas IMETRO 2014 / ABNT / APA
│   │   ├── aprovacoes/          ← Aprovação final de TCC
│   │   ├── utilizadores/        ← Gestão de utilizadores
│   │   ├── configuracoes/       ← Painel de configurações
│   │   ├── api/                 ← Endpoints REST
│   │   └── analise_ia.py        ← Módulo IA (Fase 2)
│   ├── database/
│   │   └── db.py                ← Camada SQLite (queries centralizadas)
│   ├── models/                  ← Modelos (LaBSE armazenado aqui)
│   ├── services/                ← Lógica de negócio
│   ├── static/                  ← CSS, JS, assets
│   └── templates/               ← Templates Jinja2 (por blueprint)
├── core/
│   ├── auth_helpers.py          ← Decoradores RBAC
│   ├── models/
│   │   └── utilizador.py        ← Modelo de utilizador (UserMixin)
│   ├── embeddings.py            ← Carregamento offline do LaBSE
│   ├── detector.py              ← Motor de detecção semântica
│   ├── chunker.py               ← Divisão de texto em chunks
│   ├── ingestor.py              ← Extracção de texto (PDF/DOCX)
│   ├── pesquisa_externa.py      ← Fase 0 — Pesquisa em repositórios académicos na internet
│   ├── llm_analyzer.py          ← Fase 2 — Análise LLM
│   ├── normas_regras.py         ← Regras ABNT/APA/IMETRO (verificação local regex)
│   ├── abnt_checker.py          ← Wrapper de verificação (ABNT, APA, IMETRO)
│   ├── normas_imetro_prompt.py  ← Prompts do Unimetro Inspector (IA)
│   ├── normas_imetro_checker.py ← Orquestrador LLM para normas IMETRO
│   ├── normas_verificacao_integrada.py ← Workflow integrado de normas (Local+IA)
│   └── relatorio.py             ← Gerador de relatórios HTML
├── db/
│   └── migrations/
│       ├── v4_add_users.sql             ← Migração RBAC
│       ├── v5_fontes_externas.sql       ← Migração Fase 0 (Pesquisa Externa)
│       ├── v6_resultados_normas.sql     ← Migração de módulos de normas isolados
│       └── v7_normas_na_verificacao.sql ← Migração Integração de Normas no fluxo de plágio
├── scripts/
│   ├── instalar_modelo.py       ← Download do modelo LaBSE
│   └── criar_admin.py           ← Criação do administrador
├── instance/                    ← Base de dados SQLite (plagio.db)
├── uploads/                     ← Ficheiros submetidos
├── relatorios/                  ← Relatórios HTML gerados
├── chroma_data/                 ← Base vectorial ChromaDB
├── requirements.txt             ← Dependências Python
├── run.py                       ← Ponto de entrada
└── .env                         ← Variáveis de ambiente
```

---

## 🚀 Como Executar

### Pré-requisitos
- Python 3.10 ou superior
- Recomendado: Criar e activar um ambiente virtual (`venv`)

### Instalação

1. Criar e activar o ambiente virtual:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

2. Instalar as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. **Instalação do Modelo de IA (execução única):**
   ```bash
   python scripts/instalar_modelo.py
   ```
   > **Nota:** O modelo LaBSE (~1.88GB) é descarregado uma única vez e guardado na pasta `app/models/labse/`. Após essa instalação inicial, o sistema funciona **100% offline**, sem qualquer dependência da internet.

4. **Criar o administrador do sistema (obrigatório):**
   ```bash
   python scripts/criar_admin.py
   ```
   > Este comando pede email e password pelo terminal e cria a conta de administrador com hash `bcrypt`. Sem este passo, **não é possível fazer login**.

5. Iniciar o Servidor Flask:
   ```bash
   python run.py
   ```

6. Aceda à plataforma no seu navegador: `http://127.0.0.1:5000`
   - Será redireccionado para a página de login
   - Use as credenciais definidas no passo 4

7. (Opcional) Aceda ao separador "Inteligência Artificial" para inserir a sua chave de API (OpenAI/Anthropic) ou configurar o seu servidor local Ollama para desbloquear a Fase 2 de análises LLM.

### Criar utilizadores adicionais

Após o primeiro login como administrador, aceda a **Utilizadores → Novo Utilizador** para criar contas com os papéis desejados (carregador, verificador, aprovador).

---

## 🛠️ Tecnologias Utilizadas

| Categoria | Tecnologias |
|:----------|:------------|
| **Backend** | Python 3.12, Flask 3.x, SQLite 3 |
| **Autenticação** | Flask-Login (sessões), Flask-Bcrypt (hash de passwords) |
| **Inteligência Artificial** | Sentence-Transformers (LaBSE), PyTorch, ChromaDB |
| **LLM (Fase 2 + Normas IA)** | Anthropic Claude, OpenAI GPT-4o, Ollama (local) |
| **Frontend** | HTML5, CSS3, JS Vanilla, Chart.js, Boxicons, Jinja2 |

---

## 🔐 Segurança

- Todas as passwords são armazenadas com hash `bcrypt` (nunca em texto claro)
- Sessões seguras via cookies Flask com `SECRET_KEY`
- Validação de password mínima de 8 caracteres no servidor
- Protecção contra desactivação do último administrador activo
- Tentativas de acesso não autorizado são registadas no log do servidor
- A rota `/auth/login` é a única rota pública do sistema

---

*IMETRO TFC v3 — Garantindo o Rigor e a Honestidade Académica.*