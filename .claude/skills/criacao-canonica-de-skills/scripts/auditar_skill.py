#!/usr/bin/env python3
"""Auditor mecânico de skills canônicas.

Confere uma skill contra a especificação Agent Skills e contra a anatomia
canônica: frontmatter do SKILL.md, frontmatter dos documentos, vocabulários
fechados, links, Rede Sináptica (mínimos, máximos, reciprocidade semântica,
consistência de força, salto de camadas), documentos fora do mapa, palavras
de costura, nomes de arquivo com cara de versão e caracteres invisíveis.

Uso:
    python3 auditar_skill.py <diretório-da-skill> [--estrito]

Erros reprovam a skill. Avisos pedem leitura no contexto. Com --estrito,
avisos também reprovam. Usa apenas a biblioteca padrão do Python 3.8+.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

# ---------------------------------------------------------------------------
# Vocabulários (forma canônica em português; equivalentes em inglês aceitos)
# ---------------------------------------------------------------------------


def chave(texto: str) -> str:
    """Normaliza para comparação: minúsculas, sem acentos, espaços viram hífen."""
    texto = unicodedata.normalize("NFKD", texto.strip().lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", "-", texto)


TIPOS = {chave(v) for v in (
    "fundamento", "mecanismo", "padrão", "heurística", "ferramenta",
    "modelo-mental", "lei",
    "foundation", "mechanism", "pattern", "heuristic", "tool",
    "mental-model", "law",
)}

STATUS_ENTREGAVEL = {chave(v) for v in ("ativo", "maduro", "active", "mature")}
STATUS_NAO_ENTREGAVEL = {chave(v) for v in (
    "rascunho", "em-revisão", "draft", "under-review")}
STATUS_MORTO = {chave(v) for v in (
    "depreciado", "fundido", "deprecated", "merged")}

CERTEZAS = {chave(v) for v in (
    "estabelecido", "consensual", "debatido", "experimental", "especulativo",
    "established", "consensus", "debated", "speculative",
)}
MATURIDADES = {chave(v) for v in (
    "seminal", "consolidado", "em-evolução", "em-revisão",
    "consolidated", "evolving", "under-revision",
)}
ORIGENS = {chave(v) for v in (
    "empírica", "teórica", "heurística", "derivada",
    "empirical", "theoretical", "heuristic", "derived",
)}

FORCAS = {
    chave("forte"): 3, chave("moderada"): 2, chave("sutil"): 1,
    chave("strong"): 3, chave("moderate"): 2, chave("subtle"): 1,
}

# Relação semântica -> recíproca esperada no documento de destino.
INVERSAS = {}
for _a, _b in (
    ("complementa", "complementa"),
    ("contrasta-com", "contrasta-com"),
    ("é-análogo-a", "é-análogo-a"),
    ("é-caso-especial-de", "é-generalização-de"),
    ("é-pré-requisito-de", "pressupõe"),
    ("evolui-para", "é-evolução-de"),
    ("complements", "complements"),
    ("contrasts-with", "contrasts-with"),
    ("is-analogous-to", "is-analogous-to"),
    ("is-special-case-of", "is-generalization-of"),
    ("is-prerequisite-of", "presupposes"),
    ("evolves-into", "evolves-from"),
):
    INVERSAS[chave(_a)] = chave(_b)
    INVERSAS[chave(_b)] = chave(_a)

FUNCIONAIS = {chave(v) for v in (
    "habilita", "restringe", "valida", "amplifica", "mitiga", "contextualiza",
    "enables", "constrains", "validates", "amplifies", "mitigates",
    "contextualizes",
)}

# Chaves canônicas do frontmatter dos documentos e seus equivalentes.
CHAVES_DOC = {
    "id": ("id",),
    "nome": ("nome", "name"),
    "tipo": ("tipo", "type"),
    "camada": ("camada", "layer"),
    "status": ("status",),
    "essencia": ("essencia", "essência", "essence"),
    "em-uma-palavra": ("em-uma-palavra", "in-one-word"),
    "certeza": ("certeza", "certainty"),
    "maturidade": ("maturidade", "maturity"),
    "origem": ("origem", "origin"),
}

# Campos do SKILL.md: especificação Agent Skills e extensões do Claude Code.
CAMPOS_SPEC = {"name", "description", "license", "compatibility",
               "metadata", "allowed-tools"}
CAMPOS_CLAUDE_CODE = {
    "when_to_use", "argument-hint", "arguments", "disable-model-invocation",
    "user-invocable", "disallowed-tools", "model", "effort", "context",
    "agent", "background", "hooks", "paths", "shell",
}

SECAO_REDE = re.compile(r"^##\s+(rede\s+sin[aá]ptica|synaptic\s+network)\s*$",
                        re.IGNORECASE)
SUBSECOES = {
    "estruturais": "estrutural", "structural": "estrutural",
    "semanticas": "semantica", "semantic": "semantica",
    "funcionais": "funcional", "functional": "funcional",
    "tensoes": "tensao", "tensions": "tensao",
}
ROTULO_PAI = re.compile(r"\*\*\s*(pai|parent)\s*:?\s*\*\*", re.IGNORECASE)
LINHA_TIPADA = re.compile(r"^\s*[-*]\s+`([^`]+)`\s+\*\*([^*]+)\*\*")
LINK = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")

INVISIVEIS = {
    chr(0x200B): "espaço de largura zero (U+200B)",
    chr(0x200C): "não-união de largura zero (U+200C)",
    chr(0x200D): "união de largura zero (U+200D)",
    chr(0x2060): "junção de palavras (U+2060)",
    chr(0xFEFF): "marca de ordem de bytes (U+FEFF)",
    chr(0x00AD): "hífen suave (U+00AD)",
}

# Palavras-sintoma de costura: só formas de alta precisão.
COSTURAS = [re.compile(p, re.IGNORECASE) for p in (
    r"\banteriormente\b",
    r"\bantes\s+(era|eram|era\s+feito|se\s+fazia)\b",
    r"\bvers(ão|ões)\s+(anterior|anteriores|antiga|antigas)\b",
    r"\b(nova|novas)\s+vers(ão|ões)\b",
    r"\bn[ãa]o\s+(é|são|está|estão|existe|existem|vale|valem)\s+mais\b",
    r"\bagora\s+(é|são)\b",
    r"\bpassou\s+a\s+ser\b",
    r"\batualizad[oa]s?\s+(de|a\s+partir\s+de)\b",
    r"\breformulad[oa]s?\b",
    r"\breenquadrad[oa]s?\b",
    r"\bem\s+vez\s+d[oa]s?\s+antig[oa]s?\b",
    r"\bpreviously\b",
    r"\bused\s+to\s+be\b",
    r"\bno\s+longer\b",
    r"\bnow\s+is\b",
    r"\bis\s+now\b",
    r"\bupdated\s+from\b",
    r"\breframed\b",
    r"\bformerly\b",
    r"\bthe\s+(old|new)\s+version\b",
)]
TITULOS_DE_HISTORICO = re.compile(
    r"^#{1,6}\s+.*\b(changelog|mudan[cç]as|o\s+que\s+mudou|what\s+changed|"
    r"hist[oó]rico\s+de\s+vers[oõ]es)\b",
    re.IGNORECASE,
)
NOME_DE_VERSAO = re.compile(
    r"(^|[-_.])(v\d+|novo|nova|new|old|antigo|antiga|legacy|vs|changelog|"
    r"mudancas)([-_.]|$)",
    re.IGNORECASE,
)
AUXILIARES = {"readme.md", "changelog.md", "changes.md", "history.md",
              "installation.md", "install.md"}


# ---------------------------------------------------------------------------
# Leitura de frontmatter (subconjunto de YAML suficiente para skills)
# ---------------------------------------------------------------------------


def separar_frontmatter(texto: str):
    """Retorna (linhas_do_frontmatter, linha_inicial_do_corpo) ou (None, 0)."""
    linhas = texto.split("\n")
    if not linhas or linhas[0].rstrip("\r") != "---":
        return None, 0
    for i in range(1, len(linhas)):
        if linhas[i].rstrip("\r") == "---":
            return [l.rstrip("\r") for l in linhas[1:i]], i + 1
    return None, 0


def ler_escalar(valor: str) -> str:
    valor = valor.strip()
    if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
        return valor[1:-1]
    if " #" in valor:
        valor = valor.split(" #", 1)[0].rstrip()
    return valor


def ler_yaml(linhas):
    """Lê chaves de primeiro nível, blocos > e |, mapas e listas simples."""
    dados, erros = {}, []
    i = 0
    while i < len(linhas):
        linha = linhas[i]
        if not linha.strip() or linha.lstrip().startswith("#"):
            i += 1
            continue
        if "\t" in linha[: len(linha) - len(linha.lstrip())]:
            erros.append(f"tabulação na indentação do frontmatter: {linha!r}")
        if linha[0] in " \t":
            erros.append(f"linha indentada fora de bloco: {linha.strip()!r}")
            i += 1
            continue
        m = re.match(r"^([A-Za-z0-9_\-ãáàâéêíóôõúçÃÁÀÂÉÊÍÓÔÕÚÇ]+):(.*)$", linha)
        if not m:
            erros.append(f"linha sem formato chave: valor: {linha!r}")
            i += 1
            continue
        nome, resto = m.group(1), m.group(2)
        if resto and not resto.startswith(" "):
            erros.append(f"falta espaço depois de '{nome}:'")
        resto = resto.strip()
        filhos = []
        j = i + 1
        while j < len(linhas) and (not linhas[j].strip()
                                   or linhas[j][:1] in (" ", "\t")):
            filhos.append(linhas[j])
            j += 1
        while filhos and not filhos[-1].strip():
            filhos.pop()
        if resto in (">", ">-", ">+", "|", "|-", "|+"):
            partes = [f.strip() for f in filhos]
            if resto.startswith(">"):
                dados[nome] = " ".join(p for p in partes if p)
            else:
                dados[nome] = "\n".join(partes)
        elif resto == "":
            itens = [f.strip() for f in filhos if f.strip()]
            if itens and all(t.startswith("- ") for t in itens):
                dados[nome] = [ler_escalar(t[2:]) for t in itens]
            elif itens:
                mapa = {}
                for t in itens:
                    mm = re.match(r"^([^:]+):(.*)$", t)
                    if mm:
                        mapa[mm.group(1).strip()] = ler_escalar(mm.group(2))
                    else:
                        erros.append(f"item inválido em '{nome}': {t!r}")
                dados[nome] = mapa
            else:
                dados[nome] = ""
        else:
            if (resto[0] not in "\"'[{" and re.search(r":\s", resto)):
                erros.append(
                    f"valor de '{nome}' contém ': ' sem aspas — YAML inválido")
            dados[nome] = ler_escalar(resto)
        i = j
    return dados, erros


def campo(dados: dict, canonico: str):
    for nome in CHAVES_DOC[canonico]:
        if nome in dados:
            return dados[nome]
    return None


# ---------------------------------------------------------------------------
# Texto: zonas a ignorar (código) e varredura de links
# ---------------------------------------------------------------------------


def linhas_de_prosa(texto: str, inicio: int):
    """Gera (número_da_linha, linha_sem_código_inline) fora de blocos cercados."""
    em_bloco = False
    for n, linha in enumerate(texto.split("\n")[inicio:], start=inicio + 1):
        if re.match(r"^\s*(```|~~~)", linha):
            em_bloco = not em_bloco
            continue
        if em_bloco:
            continue
        yield n, re.sub(r"`[^`]*`", "", linha)


def links_da_linha(linha: str):
    for m in LINK.finditer(linha):
        alvo = m.group(2)
        if re.match(r"^[a-z][a-z0-9+.\-]*:", alvo, re.IGNORECASE):
            continue  # http:, https:, mailto: e afins
        if alvo.startswith("#"):
            continue
        yield alvo.split("#", 1)[0]


# ---------------------------------------------------------------------------
# Auditoria
# ---------------------------------------------------------------------------


class Relatorio:
    def __init__(self, raiz: Path):
        self.raiz = raiz
        self.erros = []
        self.avisos = []

    def _loc(self, arquivo, linha):
        if arquivo is None:
            return ""
        rel = arquivo.relative_to(self.raiz).as_posix()
        return f"{rel}:{linha}" if linha else rel

    def erro(self, msg, arquivo=None, linha=None):
        self.erros.append((self._loc(arquivo, linha), msg))

    def aviso(self, msg, arquivo=None, linha=None):
        self.avisos.append((self._loc(arquivo, linha), msg))


class Documento:
    def __init__(self, caminho: Path, rel: str):
        self.caminho = caminho
        self.rel = rel
        self.texto = ""
        self.frontmatter = {}
        self.inicio_corpo = 0
        self.camada = None
        self.semanticas = []   # (relação, força, destino_rel, linha)
        self.funcionais = []
        self.tem_pai = False
        self.tem_rede = False


def auditar(raiz: Path, rel: Relatorio):
    nome_dir = raiz.name
    md_arquivos = sorted(p for p in raiz.rglob("*.md")
                         if "__pycache__" not in p.parts)
    todos = sorted(p for p in raiz.rglob("*") if p.is_file()
                   and "__pycache__" not in p.parts)

    # --- Arquivos: invisíveis, nomes de versão, auxiliares, SKILL.md aninhado
    for p in todos:
        relp = p.relative_to(raiz).as_posix()
        if p.name == ".DS_Store":
            rel.aviso("arquivo de sistema .DS_Store dentro da skill", p)
        for parte in p.relative_to(raiz).parts:
            base = parte.rsplit(".", 1)[0] if "." in parte else parte
            if NOME_DE_VERSAO.search(base):
                rel.aviso(f"nome com cara de versão ou histórico: '{parte}'", p)
                break
        if p.name.lower() in AUXILIARES:
            rel.aviso("arquivo auxiliar dentro da skill — o agente pode lê-lo "
                      "como parte do substrato; o lugar dele é fora da skill",
                      p)
        if p.name == "SKILL.md" and p.parent != raiz:
            rel.erro(f"SKILL.md aninhado em '{relp}' — uma skill tem um único "
                     "SKILL.md, na raiz", p)
        if p.suffix.lower() in (".md", ".py", ".sh", ".txt", ".json",
                                ".yaml", ".yml"):
            try:
                conteudo = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                rel.erro("arquivo de texto que não é UTF-8 válido", p)
                continue
            for n, linha in enumerate(conteudo.split("\n"), start=1):
                for c, descricao in INVISIVEIS.items():
                    if c in linha:
                        rel.aviso(f"caractere invisível: {descricao}", p, n)

    # --- SKILL.md
    skill_md = raiz / "SKILL.md"
    if not skill_md.exists():
        rel.erro("SKILL.md não encontrado na raiz da skill")
        return None
    texto_skill = skill_md.read_text(encoding="utf-8")
    fm_linhas, corpo_skill = separar_frontmatter(texto_skill)
    if fm_linhas is None:
        rel.erro("o SKILL.md não começa com '---' na primeira linha — o "
                 "frontmatter não será lido pelo runtime", skill_md, 1)
        fm = {}
    else:
        fm, erros_yaml = ler_yaml(fm_linhas)
        for e in erros_yaml:
            rel.erro(e, skill_md)
    for k in fm:
        if k in CAMPOS_SPEC:
            continue
        if k in CAMPOS_CLAUDE_CODE:
            rel.aviso(f"campo '{k}' é específico do Claude Code; o validador "
                      "de upload do claude.ai e da API recusa campos fora da "
                      "especificação", skill_md)
        else:
            rel.erro(f"campo '{k}' fora da especificação Agent Skills — "
                     "campos extras vão dentro de 'metadata'", skill_md)
    nome = fm.get("name")
    if not isinstance(nome, str) or not nome:
        rel.erro("campo obrigatório 'name' ausente ou vazio", skill_md)
    else:
        if len(nome) > 64:
            rel.erro(f"'name' tem {len(nome)} caracteres (máximo 64)", skill_md)
        if not re.fullmatch(r"[a-z0-9-]+", nome):
            rel.erro("'name' só admite letras minúsculas a-z, dígitos e hífen",
                     skill_md)
        if nome.startswith("-") or nome.endswith("-") or "--" in nome:
            rel.erro("'name' não pode começar nem terminar com hífen nem ter "
                     "hífens consecutivos", skill_md)
        if nome != nome_dir:
            rel.erro(f"'name' ({nome}) difere do nome do diretório "
                     f"({nome_dir})", skill_md)
    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        rel.erro("campo obrigatório 'description' ausente ou vazio", skill_md)
    else:
        if len(desc) > 1024:
            rel.erro(f"'description' tem {len(desc)} caracteres (máximo 1024)",
                     skill_md)
        if "<" in desc or ">" in desc:
            rel.erro("'description' contém '<' ou '>' — o validador da "
                     "Anthropic rejeita", skill_md)
        if len(desc) < 120:
            rel.aviso("'description' curta: ela é o gatilho de ativação e "
                      "precisa dizer o que a skill faz, quando usar e os "
                      "sinais", skill_md)
    compat = fm.get("compatibility")
    if isinstance(compat, str) and len(compat) > 500:
        rel.erro("'compatibility' passa de 500 caracteres", skill_md)
    meta = fm.get("metadata")
    if meta is not None and not isinstance(meta, dict):
        rel.erro("'metadata' precisa ser um mapa de chave para valor", skill_md)
    n_linhas_skill = texto_skill.count("\n") + 1
    if n_linhas_skill > 500:
        rel.aviso(f"SKILL.md com {n_linhas_skill} linhas (recomendação: menos "
                  "de 500)", skill_md)

    # --- Documentos
    docs = {}
    for p in md_arquivos:
        relp = p.relative_to(raiz).as_posix()
        if p == skill_md or p.name.lower() in AUXILIARES:
            continue
        d = Documento(p, relp)
        d.texto = p.read_text(encoding="utf-8")
        linhas_fm, d.inicio_corpo = separar_frontmatter(d.texto)
        if linhas_fm is None:
            rel.erro("documento sem frontmatter na primeira linha", p, 1)
        else:
            d.frontmatter, erros_yaml = ler_yaml(linhas_fm)
            for e in erros_yaml:
                rel.erro(e, p)
            # Linhas em branco que agrupam campos não contam.
            n_conteudo = sum(1 for l in linhas_fm if l.strip())
            if n_conteudo > 20:
                rel.erro(f"frontmatter com {n_conteudo} linhas de conteúdo "
                         "(máximo 20)", p)
            elif n_conteudo > 15:
                rel.aviso(f"frontmatter com {n_conteudo} linhas de conteúdo "
                          "(alvo: de 10 a 15)", p)
        docs[relp] = d

    ids = {}
    for relp, d in docs.items():
        f = d.frontmatter
        if not f:
            continue
        for canonico in CHAVES_DOC:
            if campo(f, canonico) in (None, ""):
                rel.erro(f"campo '{canonico}' ausente no frontmatter",
                         d.caminho)
        ident = campo(f, "id")
        esperado = relp[:-3].replace("/", ".")
        if isinstance(ident, str) and ident:
            if ident in ids:
                rel.erro(f"id '{ident}' repetido (também em {ids[ident]})",
                         d.caminho)
            ids[ident] = relp
            if ident != esperado:
                rel.aviso(f"id '{ident}' não espelha o caminho (esperado: "
                          f"'{esperado}')", d.caminho)
        tipo = campo(f, "tipo")
        if isinstance(tipo, str) and tipo and chave(tipo) not in TIPOS:
            rel.erro(f"tipo desconhecido: '{tipo}'", d.caminho)
        camada = campo(f, "camada")
        if isinstance(camada, str) and camada:
            m = re.match(r"^\s*([1-8])\b", camada)
            if not m:
                rel.erro(f"camada sem número de 1 a 8: '{camada}'", d.caminho)
            else:
                d.camada = int(m.group(1))
                if d.camada == 1:
                    rel.erro("camada 1 é exclusiva do SKILL.md", d.caminho)
        status = campo(f, "status")
        if isinstance(status, str) and status:
            s = chave(status)
            if s in STATUS_MORTO:
                rel.erro(f"status '{status}': documento superado não fica na "
                         "skill — dissolva ou remova", d.caminho)
            elif s in STATUS_NAO_ENTREGAVEL:
                rel.aviso(f"status '{status}': documento ainda não pronto para "
                          "entrega", d.caminho)
            elif s not in STATUS_ENTREGAVEL:
                rel.erro(f"status desconhecido: '{status}'", d.caminho)
        for canonico, vocabulario in (("certeza", CERTEZAS),
                                      ("maturidade", MATURIDADES),
                                      ("origem", ORIGENS)):
            valor = campo(f, canonico)
            if isinstance(valor, str) and valor and \
                    chave(valor) not in vocabulario:
                rel.erro(f"{canonico} desconhecida: '{valor}'", d.caminho)
        essencia = campo(f, "essencia")
        if isinstance(essencia, str) and essencia:
            nome_doc = campo(f, "nome")
            if isinstance(nome_doc, str) and \
                    chave(essencia).strip(".") == chave(nome_doc):
                rel.aviso("a essência repete o nome em vez de afirmar algo",
                          d.caminho)

    raizes = [d for d in docs.values() if d.camada == 2]
    if docs and not raizes:
        rel.aviso("nenhum documento raiz (camada 2) — aceitável só se o "
                  "SKILL.md declara executor-alvo, função objetivo e axiomas")
    if len(raizes) > 1:
        rel.aviso("mais de um documento na camada 2: "
                  + ", ".join(d.rel for d in raizes))

    # --- Links (todos os .md) e mapa do SKILL.md
    alcancados_pelo_mapa = set()
    for p in md_arquivos:
        texto = p.read_text(encoding="utf-8")
        _, inicio = separar_frontmatter(texto)
        for n, linha in linhas_de_prosa(texto, inicio):
            for alvo in links_da_linha(linha):
                if not alvo:
                    continue
                destino = (p.parent / alvo).resolve()
                if not destino.exists():
                    rel.erro(f"link quebrado: '{alvo}'", p, n)
                    continue
                try:
                    destino_rel = destino.relative_to(raiz.resolve()).as_posix()
                except ValueError:
                    rel.aviso(f"link aponta para fora da skill: '{alvo}' — o "
                              "executor-alvo não tem esse arquivo", p, n)
                    continue
                if p == skill_md:
                    alcancados_pelo_mapa.add(destino_rel)
    for relp in docs:
        if relp not in alcancados_pelo_mapa:
            rel.aviso("documento fora do mapa: nenhum link direto a partir do "
                      "SKILL.md", docs[relp].caminho)
    for p in todos:
        relp = p.relative_to(raiz).as_posix()
        if p.suffix in (".py", ".sh") and relp not in alcancados_pelo_mapa \
                and relp not in texto_skill:
            rel.aviso("script não mencionado no SKILL.md — o agente não saberá "
                      "que ele existe", p)

    # --- Rede Sináptica
    for relp, d in docs.items():
        dentro, sub = False, None
        linhas_brutas = d.texto.split("\n")
        for n, _ in linhas_de_prosa(d.texto, d.inicio_corpo):
            bruta = linhas_brutas[n - 1]
            if re.match(r"^##\s", bruta):
                dentro = bool(SECAO_REDE.match(bruta.strip()))
                if dentro:
                    d.tem_rede = True
                sub = None
                continue
            if not dentro:
                continue
            m = re.match(r"^###\s+(.+?)\s*$", bruta)
            if m:
                sub = SUBSECOES.get(chave(m.group(1)).split("-")[0])
                if sub is None:
                    rel.aviso(f"subseção desconhecida na Rede Sináptica: "
                              f"'{m.group(1)}'", d.caminho, n)
                continue
            if sub == "estrutural" and ROTULO_PAI.search(bruta):
                d.tem_pai = True
            if sub not in ("semantica", "funcional"):
                continue
            mt = LINHA_TIPADA.match(bruta)
            if not mt:
                if bruta.strip().startswith(("-", "*")):
                    rel.erro("conexão sem tipo em código e força em negrito",
                             d.caminho, n)
                continue
            relacao, forca = chave(mt.group(1)), chave(mt.group(2))
            if forca not in FORCAS:
                rel.erro(f"força desconhecida: '{mt.group(2)}'", d.caminho, n)
                continue
            alvos = []
            for alvo in links_da_linha(bruta):
                destino = (d.caminho.parent / alvo).resolve()
                try:
                    alvos.append(destino.relative_to(raiz.resolve()).as_posix())
                except ValueError:
                    pass
            if not alvos:
                rel.erro("conexão tipada sem link para outro documento",
                         d.caminho, n)
                continue
            for alvo_rel in alvos:
                if alvo_rel == relp:
                    rel.erro("documento conectado a si mesmo", d.caminho, n)
                    continue
                if sub == "semantica":
                    if relacao in FUNCIONAIS:
                        rel.erro(f"'{mt.group(1)}' é papel funcional e está "
                                 "entre as semânticas", d.caminho, n)
                    elif relacao not in INVERSAS:
                        rel.erro(f"relação semântica desconhecida: "
                                 f"'{mt.group(1)}'", d.caminho, n)
                    else:
                        d.semanticas.append((relacao, FORCAS[forca], alvo_rel,
                                             n))
                else:
                    if relacao in INVERSAS:
                        rel.erro(f"'{mt.group(1)}' é relação semântica e está "
                                 "entre as funcionais", d.caminho, n)
                    elif relacao not in FUNCIONAIS:
                        rel.erro(f"papel funcional desconhecido: "
                                 f"'{mt.group(1)}'", d.caminho, n)
                    else:
                        d.funcionais.append((relacao, FORCAS[forca], alvo_rel,
                                             n))

    for relp, d in docs.items():
        if not d.tem_rede:
            rel.erro("documento sem seção '## Rede Sináptica'", d.caminho)
            continue
        if d.camada != 2 and not d.tem_pai:
            rel.aviso("Rede Sináptica sem pai declarado em Estruturais",
                      d.caminho)
        n_sem = len({a for _, _, a, _ in d.semanticas})
        n_fun = len({a for _, _, a, _ in d.funcionais})
        if n_sem < 2:
            rel.erro(f"{n_sem} conexão(ões) semântica(s) — mínimo 2 "
                     "(documento órfão)", d.caminho)
        if n_fun < 1:
            rel.erro("nenhuma conexão funcional — mínimo 1", d.caminho)
        total = len(d.semanticas) + len(d.funcionais)
        if total > 15 and d.camada != 2:
            rel.aviso(f"{total} conexões tipadas — sinal de hub (escopo amplo "
                      "demais)", d.caminho)

    # Reciprocidade semântica e consistência de força
    for relp, d in docs.items():
        for relacao, forca, alvo, n in d.semanticas:
            destino = docs.get(alvo)
            if destino is None:
                rel.erro(f"conexão semântica para '{alvo}', que não é um "
                         "documento auditável da skill", d.caminho, n)
                continue
            reciprocas = [(r, f) for r, f, a, _ in destino.semanticas
                          if a == relp]
            if not reciprocas:
                rel.erro(f"conexão semântica unidirecional: '{alvo}' não "
                         f"registra a recíproca ('{INVERSAS[relacao]}')",
                         d.caminho, n)
                continue
            esperada = INVERSAS[relacao]
            if not any(r == esperada for r, _ in reciprocas):
                achadas = ", ".join(sorted({r for r, _ in reciprocas}))
                rel.erro(f"recíproca inconsistente: '{alvo}' registra "
                         f"'{achadas}', esperado '{esperada}'", d.caminho, n)
            forca_volta = max(f for _, f in reciprocas)
            if abs(forca - forca_volta) > 1:
                rel.aviso(f"força assimétrica com '{alvo}' (forte de um lado, "
                          "sutil do outro)", d.caminho, n)

    # Salto de camadas: um documento da camada 5 em diante precisa de pelo
    # menos uma conexão com uma camada intermediária (da 3 até a anterior à
    # dele); ligar-se só à raiz é aplicar axioma direto ao concreto.
    ha_mediacao = any(d.camada in (3, 4) for d in docs.values())
    if ha_mediacao:
        for relp, d in docs.items():
            if d.camada is None or d.camada < 5:
                continue
            camadas_tocadas = {docs[a].camada for _, _, a, _ in
                               d.semanticas + d.funcionais
                               if a in docs and docs[a].camada}
            if not any(3 <= c < d.camada for c in camadas_tocadas):
                rel.aviso("nenhuma conexão com uma camada intermediária "
                          f"(3 a {d.camada - 1}) — possível salto de camadas",
                          d.caminho)

    # --- Costuras de Nível 2 (fora de código e do frontmatter)
    for p in md_arquivos:
        texto = p.read_text(encoding="utf-8")
        _, inicio = separar_frontmatter(texto)
        for n, linha in linhas_de_prosa(texto, inicio):
            if TITULOS_DE_HISTORICO.match(linha):
                rel.aviso("título de histórico de mudanças dentro da skill",
                          p, n)
            for padrao in COSTURAS:
                m = padrao.search(linha)
                if m:
                    rel.aviso(f"possível costura de Nível 2: '{m.group(0)}' — "
                              "leia no contexto", p, n)

    return docs


def main():
    parser = argparse.ArgumentParser(
        description="Audita uma skill contra a especificação Agent Skills e "
                    "a anatomia canônica.")
    parser.add_argument("skill", help="diretório da skill (contém o SKILL.md)")
    parser.add_argument("--estrito", action="store_true",
                        help="avisos também reprovam a skill")
    args = parser.parse_args()

    raiz = Path(args.skill).expanduser()
    if not raiz.is_dir():
        print(f"erro: '{raiz}' não é um diretório", file=sys.stderr)
        return 2
    raiz = raiz.resolve()
    rel = Relatorio(raiz)
    docs = auditar(raiz, rel) or {}

    print(f"Auditoria canônica — {raiz.name}")
    if docs:
        por_camada = {}
        for d in docs.values():
            por_camada[d.camada] = por_camada.get(d.camada, 0) + 1
        camadas = ", ".join(f"{c}: {q}" for c, q in
                            sorted(por_camada.items(),
                                   key=lambda x: (x[0] is None, x[0] or 0)))
        n_sem = sum(len(d.semanticas) for d in docs.values())
        n_fun = sum(len(d.funcionais) for d in docs.values())
        print(f"  documentos: {len(docs)} (por camada — {camadas})")
        print(f"  conexões tipadas: {n_sem} semânticas, {n_fun} funcionais")
    print()
    for titulo, itens in (("ERROS", rel.erros), ("AVISOS", rel.avisos)):
        print(f"{titulo} ({len(itens)})")
        for loc, msg in itens:
            print(f"  {loc + ' — ' if loc else ''}{msg}")
        print()
    reprovada = bool(rel.erros) or (args.estrito and bool(rel.avisos))
    print("Resultado:", "REPROVADA" if reprovada else "APROVADA")
    return 1 if reprovada else 0


if __name__ == "__main__":
    sys.exit(main())
