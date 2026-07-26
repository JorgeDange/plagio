from dataclasses import dataclass, field
from typing import Literal, List, Dict, Any
import re

@dataclass
class Regra:
    id: str
    norma: str
    sub_norma: str
    categoria: str
    descricao: str
    como_verificar: str
    severidade: Literal["erro", "aviso", "info"]
    referencia_oficial: str
    auto_detectavel: bool = True

REGRAS_ABNT: List[Regra] = [
    # NBR 14724 - Estrutura
    Regra(
        id="abnt_14724_resumo_pt",
        norma="ABNT",
        sub_norma="NBR 14724",
        categoria="Estrutura",
        descricao="O documento deve ter um 'Resumo' seguido de 'Palavras-chave'",
        como_verificar="Verifica se existe a palavra 'RESUMO' isolada seguida de 'Palavras-chave:'",
        severidade="erro",
        referencia_oficial="NBR 14724:2011, secção 4.1.15"
    ),
    Regra(
        id="abnt_14724_abstract",
        norma="ABNT",
        sub_norma="NBR 14724",
        categoria="Estrutura",
        descricao="O documento deve ter um 'Abstract' (resumo em Inglês) seguido de 'Keywords'",
        como_verificar="Verifica se existe a palavra 'ABSTRACT' seguida de 'Keywords:'",
        severidade="erro",
        referencia_oficial="NBR 14724:2011, secção 4.1.16"
    ),
    Regra(
        id="abnt_14724_sumario",
        norma="ABNT",
        sub_norma="NBR 14724",
        categoria="Estrutura",
        descricao="O documento deve ter a secção 'Sumário'",
        como_verificar="Verifica a existência do título 'SUMÁRIO'.",
        severidade="erro",
        referencia_oficial="NBR 14724:2011, secção 4.1.27"
    ),
    Regra(
        id="abnt_14724_introducao",
        norma="ABNT",
        sub_norma="NBR 14724",
        categoria="Estrutura",
        descricao="O documento deve ter a secção 'Introdução' com numeração (ex: 1 Introdução)",
        como_verificar="Verifica '1 INTRODUÇÃO' ou '1. INTRODUÇÃO'.",
        severidade="erro",
        referencia_oficial="NBR 14724:2011, secção 4.2.1"
    ),
    Regra(
        id="abnt_14724_conclusao",
        norma="ABNT",
        sub_norma="NBR 14724",
        categoria="Estrutura",
        descricao="O documento deve ter a secção 'Conclusão' ou 'Considerações Finais'",
        como_verificar="Verifica título 'CONCLUSÃO' ou 'CONSIDERAÇÕES FINAIS'.",
        severidade="erro",
        referencia_oficial="NBR 14724:2011, secção 4.2.3"
    ),
    Regra(
        id="abnt_14724_referencias",
        norma="ABNT",
        sub_norma="NBR 14724",
        categoria="Estrutura",
        descricao="O documento deve ter a secção 'Referências'",
        como_verificar="Verifica o título 'REFERÊNCIAS'.",
        severidade="erro",
        referencia_oficial="NBR 14724:2011, secção 4.3.1"
    ),
    Regra(
        id="abnt_14724_formatacao_geral",
        norma="ABNT",
        sub_norma="NBR 14724",
        categoria="Formatação",
        descricao="Verifique manualmente se as margens estão a 3cm/2cm e a fonte é Arial/Times tamanho 12",
        como_verificar="Requer análise visual do PDF original. Impossível detectar com texto plano.",
        severidade="aviso",
        referencia_oficial="NBR 14724:2011, secção 5",
        auto_detectavel=False
    ),
    Regra(
        id="abnt_14724_figuras_tabelas",
        norma="ABNT",
        sub_norma="NBR 14724",
        categoria="Formatação",
        descricao="Verifique se as tabelas e figuras têm número, título por cima e a fonte por baixo",
        como_verificar="Procura padrões como 'Tabela X — Título' seguido de 'Fonte: '. Depende da estrutura.",
        severidade="aviso",
        referencia_oficial="NBR 14724:2011, secções 5.8 e 5.9",
        auto_detectavel=False
    ),

    # NBR 10520 - Citações
    Regra(
        id="abnt_10520_citacao_longa",
        norma="ABNT",
        sub_norma="NBR 10520",
        categoria="Citações",
        descricao="Citações com mais de 3 linhas devem ter um recuo de 4cm e letra mais pequena",
        como_verificar="Identificar blocos recuados no layout original.",
        severidade="aviso",
        referencia_oficial="NBR 10520:2023",
        auto_detectavel=False
    ),
    Regra(
        id="abnt_10520_citacao_apud",
        norma="ABNT",
        sub_norma="NBR 10520",
        categoria="Citações",
        descricao="Foi usado o termo 'apud'. Tente ler os autores originais em vez de fazer 'citação de citação'",
        como_verificar="Verifica a ocorrência da palavra 'apud' no texto.",
        severidade="info",
        referencia_oficial="NBR 10520:2023"
    ),
    Regra(
        id="abnt_10520_citacao_padrao",
        norma="ABNT",
        sub_norma="NBR 10520",
        categoria="Citações",
        descricao="O texto deve ter citações com o nome do autor e o ano (ex: SILVA, 2020)",
        como_verificar="Verifica se existem citações no padrão.",
        severidade="aviso",
        referencia_oficial="NBR 10520:2023"
    ),

    # NBR 6024 - Numeração
    Regra(
        id="abnt_6024_numeracao",
        norma="ABNT",
        sub_norma="NBR 6024",
        categoria="Formatação",
        descricao="Não coloque ponto final no fim do número dos capítulos (escreva '1.1 Título' e não '1.1. Título')",
        como_verificar="Procura por '1.1. ' indicando ponto final a mais.",
        severidade="erro",
        referencia_oficial="NBR 6024:2012, secção 3"
    ),

    # NBR 6028 - Resumo
    Regra(
        id="abnt_6028_resumo_tamanho",
        norma="ABNT",
        sub_norma="NBR 6028",
        categoria="Estrutura",
        descricao="O 'Resumo' deve ter um tamanho adequado (entre 150 e 500 palavras)",
        como_verificar="Conta o número de palavras no bloco após 'RESUMO' até 'Palavras-chave'.",
        severidade="erro",
        referencia_oficial="NBR 6028:2021, secção 4.1.2"
    )
]

REGRAS_APA: List[Regra] = [
    # Estrutura Geral APA 7
    Regra(
        id="apa_7_margens_fonte",
        norma="APA",
        sub_norma="APA 7",
        categoria="Formatação",
        descricao="Verifique se o documento tem margens de 2.54cm, letra tamanho 11 ou 12, e espaço duplo entre as linhas",
        como_verificar="Necessita leitura do formato original.",
        severidade="aviso",
        referencia_oficial="APA 7, Seção 2",
        auto_detectavel=False
    ),
    Regra(
        id="apa_7_referencias_titulo",
        norma="APA",
        sub_norma="APA 7",
        categoria="Estrutura",
        descricao="A secção no final do documento deve chamar-se 'Referências'",
        como_verificar="Procura pelo título 'Referências'.",
        severidade="erro",
        referencia_oficial="APA 7, Seção 2.12"
    ),
    
    # Citações APA 7
    Regra(
        id="apa_7_citacao_ampersand",
        norma="APA",
        sub_norma="APA 7",
        categoria="Citações",
        descricao="Dentro de parênteses com 2 autores, use '&' em vez de 'e' (ex: Silva & Santos, 2020)",
        como_verificar="Procura padrão (Autor e Autor, Ano) para sinalizar erro.",
        severidade="aviso",
        referencia_oficial="APA 7, Seção 8.17"
    ),
    Regra(
        id="apa_7_citacao_etal",
        norma="APA",
        sub_norma="APA 7",
        categoria="Citações",
        descricao="Se a obra tiver 3 ou mais autores, use 'et al.' para não ter de escrever os nomes todos",
        como_verificar="Verifica uso de 'et al.' no texto.",
        severidade="info",
        referencia_oficial="APA 7, Seção 8.17"
    ),
    Regra(
        id="apa_7_citacao_longa",
        norma="APA",
        sub_norma="APA 7",
        categoria="Citações",
        descricao="Citações longas (+40 palavras) devem ser separadas do texto e ter o ponto final antes dos parênteses",
        como_verificar="Verificação manual necessária devido à formatação de bloco.",
        severidade="aviso",
        referencia_oficial="APA 7, Seção 8.27",
        auto_detectavel=False
    ),
    Regra(
        id="apa_7_como_citado",
        norma="APA",
        sub_norma="APA 7",
        categoria="Citações",
        descricao="Foi usado o termo 'como citado em'. Se possível, vá ler o documento original do autor",
        como_verificar="Verifica presença de 'como citado em'.",
        severidade="info",
        referencia_oficial="APA 7, Seção 8.6"
    )
]

REGRAS_IMETRO: List[Regra] = [
    # ── Estrutura obrigatória (Artigo 6º + Secção V) ──
    Regra(
        id="imetro_resumo",
        norma="IMETRO",
        sub_norma="IMETRO 2014",
        categoria="Estrutura",
        descricao="O documento deve ter um 'RESUMO' seguido de 'PALAVRAS-CHAVE'",
        como_verificar="Verifica se existe 'RESUMO' seguido de 'PALAVRAS-CHAVE' ou 'Palavras-chave'.",
        severidade="erro",
        referencia_oficial="Manual IMETRO 2014, Secção V — Resumo"
    ),
    Regra(
        id="imetro_resumo_tamanho",
        norma="IMETRO",
        sub_norma="IMETRO 2014",
        categoria="Estrutura",
        descricao="O resumo deve ter entre 120 e 150 palavras (norma IMETRO)",
        como_verificar="Conta o número de palavras no bloco após 'RESUMO' até 'PALAVRAS-CHAVE'.",
        severidade="erro",
        referencia_oficial="Manual IMETRO 2014, Secção V — Resumo"
    ),
    Regra(
        id="imetro_palavras_chave_3",
        norma="IMETRO",
        sub_norma="IMETRO 2014",
        categoria="Estrutura",
        descricao="O trabalho deve ter exactamente 3 palavras-chave, separadas por ponto final e em ordem alfabética",
        como_verificar="Identifica a linha de palavras-chave e conta os termos separados por ponto.",
        severidade="aviso",
        referencia_oficial="Manual IMETRO 2014, Secção V — Resumo"
    ),
    Regra(
        id="imetro_sumario",
        norma="IMETRO",
        sub_norma="IMETRO 2014",
        categoria="Estrutura",
        descricao="O documento deve ter a secção 'SUMÁRIO'",
        como_verificar="Verifica a existência do título 'SUMÁRIO'.",
        severidade="erro",
        referencia_oficial="Manual IMETRO 2014, Secção V — Sumário"
    ),
    Regra(
        id="imetro_introducao",
        norma="IMETRO",
        sub_norma="IMETRO 2014",
        categoria="Estrutura",
        descricao="O documento deve ter a secção 'Introdução' com numeração",
        como_verificar="Verifica '1 INTRODUÇÃO' ou 'INTRODUÇÃO'.",
        severidade="erro",
        referencia_oficial="Manual IMETRO 2014, Secção V — Elementos Textuais"
    ),
    Regra(
        id="imetro_conclusao",
        norma="IMETRO",
        sub_norma="IMETRO 2014",
        categoria="Estrutura",
        descricao="O documento deve ter a secção 'Conclusão'",
        como_verificar="Verifica título 'CONCLUSÃO' ou 'CONCLUSAO'.",
        severidade="erro",
        referencia_oficial="Manual IMETRO 2014, Secção V — Elementos Textuais"
    ),
    Regra(
        id="imetro_bibliografia",
        norma="IMETRO",
        sub_norma="IMETRO 2014",
        categoria="Estrutura",
        descricao="O documento deve ter a secção 'Bibliografia' (não 'Referências')",
        como_verificar="Verifica o título 'BIBLIOGRAFIA'.",
        severidade="erro",
        referencia_oficial="Manual IMETRO 2014, Secção V — Elementos Pós-Textuais"
    ),
    Regra(
        id="imetro_dedicatoria",
        norma="IMETRO",
        sub_norma="IMETRO 2014",
        categoria="Estrutura",
        descricao="Verifica se existe secção de 'Dedicatória' (opcional)",
        como_verificar="Procura pela palavra 'DEDICATÓRIA' ou 'Dedicatória'.",
        severidade="info",
        referencia_oficial="Manual IMETRO 2014, Secção V — Elementos Pré-Textuais"
    ),
    Regra(
        id="imetro_agradecimentos",
        norma="IMETRO",
        sub_norma="IMETRO 2014",
        categoria="Estrutura",
        descricao="Verifica se existe secção de 'Agradecimentos' (opcional)",
        como_verificar="Procura pela palavra 'AGRADECIMENTOS' ou 'Agradecimentos'.",
        severidade="info",
        referencia_oficial="Manual IMETRO 2014, Secção V — Elementos Pré-Textuais"
    ),

    # ── Formatação (Secção III) ──
    Regra(
        id="imetro_lingua_impessoal",
        norma="IMETRO",
        sub_norma="IMETRO 2014",
        categoria="Formatação",
        descricao="O texto deve usar linguagem impessoal (3ª pessoa). Proibido uso da 1ª pessoa do singular",
        como_verificar="Procura por padrões de 1ª pessoa: 'eu fiz', 'eu analisei', 'realizei', 'minha pesquisa', etc.",
        severidade="erro",
        referencia_oficial="Manual IMETRO 2014, Secção III — Redacção"
    ),
    Regra(
        id="imetro_formatacao_geral",
        norma="IMETRO",
        sub_norma="IMETRO 2014",
        categoria="Formatação",
        descricao="Verifique manualmente se a fonte é Times New Roman 12, margens 3cm/2cm e espaçamento 1,5",
        como_verificar="Requer análise visual do PDF original. Impossível detectar com texto plano.",
        severidade="aviso",
        referencia_oficial="Manual IMETRO 2014, Secção III — Papel e Fonte",
        auto_detectavel=False
    ),

    # ── Citações (Secção 3.16) ──
    Regra(
        id="imetro_citacao_padrao",
        norma="IMETRO",
        sub_norma="IMETRO 2014",
        categoria="Citações",
        descricao="O texto deve ter citações com o sistema autor-data, ex: Silva (2020) ou (SILVA, 2020)",
        como_verificar="Verifica se existem citações no padrão autor-data.",
        severidade="aviso",
        referencia_oficial="Manual IMETRO 2014, Secção 3.16 — Citações"
    ),
    Regra(
        id="imetro_citacao_apud",
        norma="IMETRO",
        sub_norma="IMETRO 2014",
        categoria="Citações",
        descricao="O uso de 'apud' (citação de citação) deve ser restrito a obras de difícil acesso",
        como_verificar="Verifica a ocorrência da palavra 'apud' no texto.",
        severidade="info",
        referencia_oficial="Manual IMETRO 2014, Secção 3.16 — Citação de Citação"
    ),

    # ── Metodologia (Secção IV) ──
    Regra(
        id="imetro_problema_pergunta",
        norma="IMETRO",
        sub_norma="IMETRO 2014",
        categoria="Metodologia",
        descricao="O problema de investigação deve estar formulado como pergunta (com '?')",
        como_verificar="Procura por frases interrogativas próximas aos termos 'problema' ou 'problemática'.",
        severidade="erro",
        referencia_oficial="Manual IMETRO 2014, Secção IV — Problema"
    ),
    Regra(
        id="imetro_objectivos",
        norma="IMETRO",
        sub_norma="IMETRO 2014",
        categoria="Metodologia",
        descricao="O trabalho deve declarar objectivo geral e objectivos específicos",
        como_verificar="Procura por 'objectivo geral' e 'objectivos específicos'.",
        severidade="erro",
        referencia_oficial="Manual IMETRO 2014, Secção IV — Objectivos"
    ),
    Regra(
        id="imetro_hipotese",
        norma="IMETRO",
        sub_norma="IMETRO 2014",
        categoria="Metodologia",
        descricao="O trabalho deve apresentar hipótese(s) de investigação",
        como_verificar="Procura por 'hipótese', 'hipóteses' ou 'hipotese'.",
        severidade="erro",
        referencia_oficial="Manual IMETRO 2014, Secção IV — Hipótese"
    ),
]

TODAS_REGRAS = REGRAS_ABNT + REGRAS_APA + REGRAS_IMETRO

def _avaliar_regex(texto: str, padroes: List[str]) -> bool:
    """Função auxiliar para avaliar padrões regex no texto."""
    for padrao in padroes:
        if re.search(padrao, texto, re.IGNORECASE):
            return True
    return False

def _verificar_abnt_resumo_tamanho(texto: str) -> bool:
    """Verifica se o tamanho do resumo (se encontrado) está entre 150 e 500 palavras."""
    match = re.search(r'(?i)resumo\s*(.*?)\s*palavras-chave', texto, re.DOTALL)
    if match:
        conteudo = match.group(1).strip()
        palavras = len(conteudo.split())
        return 150 <= palavras <= 500
    return False


def _verificar_imetro_resumo_tamanho(texto: str) -> bool:
    """Verifica se o tamanho do resumo IMETRO está entre 120 e 150 palavras."""
    match = re.search(r'(?i)resumo\s*(.*?)\s*palavras[\s-]*chave', texto, re.DOTALL)
    if match:
        conteudo = match.group(1).strip()
        palavras = len(conteudo.split())
        return 120 <= palavras <= 150
    return False


def _contar_palavras_chave_imetro(texto: str) -> int:
    """Conta o número de palavras-chave após 'PALAVRAS-CHAVE:' no texto."""
    match = re.search(r'(?i)palavras[\s-]*chave[:\s]+(.*?)(?:\n\n|\n[A-Z])', texto, re.DOTALL)
    if match:
        linha = match.group(1).strip()
        # Separadas por ponto final ou ponto e vírgula
        termos = [t.strip() for t in re.split(r'[.;]', linha) if t.strip()]
        return len(termos)
    return -1

def verificar_normas(texto: str, norma: str = "ABNT") -> Dict[str, Any]:
    """
    Verifica o texto contra as regras da norma especificada.
    Retorna um relatório com: aprovadas, avisos, erros, info.
    """
    if norma == "IMETRO":
        regras = REGRAS_IMETRO
    elif norma == "APA":
        regras = REGRAS_APA
    else:
        regras = REGRAS_ABNT
    resultados: Dict[str, Any] = {
        "norma": norma,
        "total_regras": len(regras),
        "erros":   [],
        "avisos":  [],
        "info":    [],
        "aprovadas": [],
        "pontuacao": 0.0
    }

    if not texto:
        return resultados

    for regra in regras:
        if not regra.auto_detectavel:
            resultados["info"].append({
                "id": regra.id,
                "descricao": regra.descricao,
                "mensagem": "Verificação manual necessária",
                "referencia": regra.referencia_oficial
            })
            continue

        # Lógica de verificação específica por regra
        aprovado = False
        mensagem_erro = ""

        if regra.id == "abnt_14724_resumo_pt":
            aprovado = _avaliar_regex(texto, [r'(?i)\bresumo\b[\s\S]{1,2000}palavras-chave'])
            mensagem_erro = "Resumo ou Palavras-chave não encontrados no texto."
            
        elif regra.id == "abnt_14724_abstract":
            aprovado = _avaliar_regex(texto, [r'(?i)\babstract\b[\s\S]{1,2000}keywords'])
            mensagem_erro = "Abstract ou Keywords não encontrados no texto."
            
        elif regra.id == "abnt_14724_sumario":
            aprovado = _avaliar_regex(texto, [r'(?i)\bsum[aá]rio\b'])
            mensagem_erro = "Secção 'Sumário' não encontrada."
            
        elif regra.id == "abnt_14724_introducao":
            aprovado = _avaliar_regex(texto, [r'(?i)\b1\.?\s*introdu[cç][aã]o\b', r'(?i)\bintrodu[cç][aã]o\b'])
            mensagem_erro = "Secção de Introdução não encontrada."
            
        elif regra.id == "abnt_14724_conclusao":
            aprovado = _avaliar_regex(texto, [r'(?i)\bconclus[aã]o\b', r'(?i)\bconsidera[cç][õo]es finais\b'])
            mensagem_erro = "Secção de Conclusão ou Considerações Finais não encontrada."
            
        elif regra.id == "abnt_14724_referencias":
            aprovado = _avaliar_regex(texto, [r'(?i)\brefer[êe]ncias\b'])
            mensagem_erro = "Secção 'Referências' não encontrada."
            
        elif regra.id == "abnt_10520_citacao_apud":
            aprovado = not _avaliar_regex(texto, [r'(?i)\bapud\b'])
            if not aprovado:
                mensagem_erro = "Foi encontrado o uso de 'apud' (citação de citação). Evite usar se possível."
                
        elif regra.id == "abnt_10520_citacao_padrao":
            # Procura de forma genérica citações no texto para ABNT (qualquer ano)
            aprovado = _avaliar_regex(texto, [r'\([A-ZÀ-Úa-zà-ú]+[A-ZÀ-Úa-zà-ú\s;]+,\s*(?:19|20)\d{2}\)'])
            if not aprovado:
                 mensagem_erro = "Padrão de citação Autor-data ausente ou mal formatado."
            
        elif regra.id == "abnt_6024_numeracao":
            tem_ponto_final = bool(re.search(r'\b\d+\.\d+\.\s+[A-Z]', texto))
            aprovado = not tem_ponto_final
            if not aprovado:
                 mensagem_erro = "Encontrada secção numerada com ponto final (ex: 1.1. Título). A norma proíbe o ponto final no indicativo."
            
        elif regra.id == "abnt_6028_resumo_tamanho":
            aprovado = _verificar_abnt_resumo_tamanho(texto)
            if not aprovado:
                 mensagem_erro = "O resumo parece ter menos de 150 ou mais de 500 palavras, ou não foi encontrado."
            
        elif regra.id == "apa_7_referencias_titulo":
            aprovado = _avaliar_regex(texto, [r'(?i)\brefer[êe]ncias\b'])
            mensagem_erro = "Secção 'Referências' não encontrada."
            
        elif regra.id == "apa_7_citacao_ampersand":
            usou_e = bool(re.search(r'\([A-Za-z]+ e [A-Za-z]+, \d{4}\)', texto))
            aprovado = not usou_e
            if not aprovado:
                 mensagem_erro = "Citação APA entre parênteses usou 'e' em vez de '&' para múltiplos autores."
            
        elif regra.id == "apa_7_citacao_etal":
            aprovado = _avaliar_regex(texto, [r'(?i)et al\.'])
            mensagem_erro = "Não foi encontrado 'et al.'. Verifique se existem citações com 3 ou mais autores."
            
        elif regra.id == "apa_7_como_citado":
            aprovado = not _avaliar_regex(texto, [r'(?i)como citado em'])
            if not aprovado:
                mensagem_erro = "Foi encontrado o uso de 'como citado em'. Tente recorrer às fontes originais."

        # ── Regras IMETRO ──
        elif regra.id == "imetro_resumo":
            aprovado = _avaliar_regex(texto, [r'(?i)\bresumo\b[\s\S]{1,3000}palavras[\s-]*chave'])
            mensagem_erro = "Secção 'RESUMO' seguida de 'PALAVRAS-CHAVE' não encontrada."

        elif regra.id == "imetro_resumo_tamanho":
            aprovado = _verificar_imetro_resumo_tamanho(texto)
            if not aprovado:
                mensagem_erro = "O resumo deve ter entre 120 e 150 palavras (norma IMETRO). Verifique a extensão."

        elif regra.id == "imetro_palavras_chave_3":
            qtd = _contar_palavras_chave_imetro(texto)
            aprovado = qtd == 3
            if not aprovado:
                mensagem_erro = f"Encontradas {qtd} palavras-chave (esperado exactamente 3, em ordem alfabética)."

        elif regra.id == "imetro_sumario":
            aprovado = _avaliar_regex(texto, [r'(?i)\bsum[aá]rio\b'])
            mensagem_erro = "Secção 'SUMÁRIO' não encontrada."

        elif regra.id == "imetro_introducao":
            aprovado = _avaliar_regex(texto, [r'(?i)\b1\.?\s*introdu[cç][aã]o\b', r'(?i)\bintrodu[cç][aã]o\b'])
            mensagem_erro = "Secção 'Introdução' não encontrada."

        elif regra.id == "imetro_conclusao":
            aprovado = _avaliar_regex(texto, [r'(?i)\bconclus[aã]o\b'])
            mensagem_erro = "Secção 'Conclusão' não encontrada."

        elif regra.id == "imetro_bibliografia":
            aprovado = _avaliar_regex(texto, [r'(?i)\bbibliografia\b'])
            if not aprovado:
                mensagem_erro = "Secção 'BIBLIOGRAFIA' não encontrada. (IMETRO usa 'Bibliografia', não 'Referências'.)"

        elif regra.id == "imetro_dedicatoria":
            aprovado = _avaliar_regex(texto, [r'(?i)\bdedicat[oó]ria\b'])
            mensagem_erro = "Secção 'Dedicatória' não encontrada (elemento opcional)."

        elif regra.id == "imetro_agradecimentos":
            aprovado = _avaliar_regex(texto, [r'(?i)\bagradecimentos\b'])
            mensagem_erro = "Secção 'Agradecimentos' não encontrada (elemento opcional)."

        elif regra.id == "imetro_lingua_impessoal":
            tem_1a_pessoa = _avaliar_regex(texto, [
                r'(?i)\beu\s+(fiz|analisei|realizei|observei|conclui|verifiquei|escolhi|optei|decidi|pesquisei|estudei|elaborei|utilizei|abordei|investiguei)',
                r'(?i)\b(minha|meu|minhas|meus)\s+(pesquisa|trabalho|estudo|análise|investigação|monografia|tese)',
                r'(?i)\brealizo\b',
                r'(?i)\bna minha\b',
            ])
            aprovado = not tem_1a_pessoa
            if not aprovado:
                mensagem_erro = "Detectado uso da 1ª pessoa do singular. A norma IMETRO exige linguagem impessoal (3ª pessoa)."

        elif regra.id == "imetro_citacao_padrao":
            aprovado = _avaliar_regex(texto, [r'\([A-ZÀ-Úa-zà-ú]+[A-ZÀ-Úa-zà-ú\s;]+,\s*(?:19|20)\d{2}\)'])
            if not aprovado:
                mensagem_erro = "Padrão de citação autor-data não detectado (ex: SILVA, 2020)."

        elif regra.id == "imetro_citacao_apud":
            aprovado = not _avaliar_regex(texto, [r'(?i)\bapud\b'])
            if not aprovado:
                mensagem_erro = "Uso de 'apud' detectado. Restrito a obras de difícil acesso."

        elif regra.id == "imetro_problema_pergunta":
            # Procura por '?' perto de 'problema' ou 'problemática'
            tem_pergunta = _avaliar_regex(texto, [
                r'(?i)(problema|problem[aá]tica)[^.]{0,500}\?',
                r'(?i)\?[^.]{0,200}(problema|problem[aá]tica)',
            ])
            aprovado = tem_pergunta
            if not aprovado:
                mensagem_erro = "Problema de investigação não formulado como pergunta (deve conter '?')."

        elif regra.id == "imetro_objectivos":
            tem_geral = _avaliar_regex(texto, [r'(?i)ob[jc]ectivo\s+geral', r'(?i)ob[jc]etivo\s+geral'])
            tem_especificos = _avaliar_regex(texto, [r'(?i)ob[jc]ectivos\s+espec[ií]ficos', r'(?i)ob[jc]etivos\s+espec[ií]ficos'])
            aprovado = tem_geral and tem_especificos
            if not aprovado:
                partes = []
                if not tem_geral: partes.append("objectivo geral")
                if not tem_especificos: partes.append("objectivos específicos")
                mensagem_erro = f"Não encontrado: {', '.join(partes)}."

        elif regra.id == "imetro_hipotese":
            aprovado = _avaliar_regex(texto, [r'(?i)\bhip[oó]tese', r'(?i)\bhip[oó]teses\b'])
            if not aprovado:
                mensagem_erro = "Hipótese(s) de investigação não encontrada(s) no texto."

        else:
            # Caso fallback para qualquer regra
            aprovado = True

        # Processar resultado
        if aprovado:
            resultados["aprovadas"].append(regra.id)
        else:
            item = {
                "id": regra.id,
                "descricao": regra.descricao,
                "mensagem": mensagem_erro,
                "referencia": regra.referencia_oficial
            }
            if regra.severidade == "erro":
                resultados["erros"].append(item)
            elif regra.severidade == "aviso":
                resultados["avisos"].append(item)
            else:
                resultados["info"].append(item)

    # Calcular pontuação baseada em erros e avisos
    total_verificaveis = len(regras) - len([r for r in regras if not r.auto_detectavel])
    if total_verificaveis > 0:
        peso_erros = len(resultados["erros"]) * 1.5
        peso_avisos = len(resultados["avisos"]) * 0.5
        score_reducao = (peso_erros + peso_avisos) / total_verificaveis
        
        raw_score = 100.0 * (1.0 - score_reducao)
        resultados["pontuacao"] = max(0.0, min(100.0, round(raw_score, 1)))
    else:
        resultados["pontuacao"] = 100.0

    return resultados
