import type { EngineInterface } from 'claude-code'

import type { MazyosArquivo, MazyosChave, MazyosWorkspace } from '../types'

type Fonte = { chave: MazyosChave; relativo: string; rotulo: string }

/** Os arquivos de memória de um workspace MazyOS, na ordem em que o painel os lista. */
export const FONTES: readonly Fonte[] = [
  { chave: 'empresa', relativo: '_memoria/empresa.md', rotulo: 'empresa.md' },
  { chave: 'preferencias', relativo: '_memoria/preferencias.md', rotulo: 'preferencias.md' },
  { chave: 'estrategia', relativo: '_memoria/estrategia.md', rotulo: 'estrategia.md' },
  { chave: 'design', relativo: 'identidade/design-guide.md', rotulo: 'design-guide.md' },
]

/** Editado um destes, o contexto do negócio mudou: a memória, a identidade e o CLAUDE.md do workspace. */
const VIGIADOS: readonly string[] = [...FONTES.map(fonte => fonte.relativo), 'CLAUDE.md']

/** Títulos dos templates: um H1 igual a um deles não é o nome do negócio. */
const TITULOS_DE_TEMPLATE = new Set([
  'empresa',
  'preferências',
  'preferencias',
  'estratégia',
  'estrategia',
  'identidade visual',
])

type Leitor = Pick<EngineInterface, 'fs' | 'clock' | 'plugin'>

/** Barras no padrão `/` e sem barra final, pra comparar caminhos de qualquer sistema. */
export function normalizar(caminho: string): string {
  return caminho.replace(/\\/g, '/').replace(/\/+$/, '')
}

export function juntar(raiz: string, relativo: string): string {
  return `${normalizar(raiz)}/${relativo}`
}

/**
 * O caminho relativo (`_memoria/empresa.md`) quando `caminho` é um arquivo
 * vigiado do workspace em `raiz`; undefined pra qualquer outro arquivo.
 */
export function arquivoVigiado(raiz: string, caminho: string): string | undefined {
  const base = `${normalizar(raiz).toLowerCase()}/`
  const alvo = normalizar(caminho)
  if (!alvo.toLowerCase().startsWith(base)) return undefined
  const relativo = alvo.slice(base.length).toLowerCase()
  return VIGIADOS.find(vigiado => vigiado.toLowerCase() === relativo)
}

/** O texto do arquivo, ou vazio quando ele não existe ou não pôde ser lido. */
export async function lerTexto($: Leitor, caminho: string): Promise<string> {
  try {
    const lido = await $.fs.read(caminho)
    return typeof lido === 'string' ? lido : ''
  } catch {
    return ''
  }
}

/** Lê o workspace em `raiz`: se está instalado, o estado de cada memória e o resumo do negócio. */
export async function lerWorkspace($: Leitor, raiz: string): Promise<MazyosWorkspace> {
  const instalado = await $.fs.exists(juntar(raiz, '_memoria'))
  const arquivos: MazyosArquivo[] = []
  const textos: Partial<Record<MazyosChave, string>> = {}

  for (const fonte of FONTES) {
    const caminho = juntar(raiz, fonte.relativo)
    const existe = instalado && (await $.fs.exists(caminho))
    let texto = ''
    let mtimeMs = 0
    if (existe) {
      texto = await lerTexto($, caminho)
      mtimeMs = await $.fs.stat(caminho).then(stat => stat.mtimeMs, () => 0)
    }
    const modelo = existe
      ? await lerTexto($, `${normalizar($.plugin.root)}/templates/workspace/${fonte.relativo}`)
      : ''
    const preenchido = existe && temConteudo(texto) && !mesmoTexto(texto, modelo)
    textos[fonte.chave] = texto
    arquivos.push({ chave: fonte.chave, rotulo: fonte.rotulo, caminho, existe, preenchido, mtimeMs })
  }

  const empresa = textos.empresa ?? ''
  return {
    raiz: normalizar(raiz),
    instalado,
    nome: campo(empresa, ['Nome', 'Empresa', 'Negócio']) ?? tituloProprio(empresa),
    negocio: campo(empresa, ['O que faz', 'O que entrega', 'Negócio']),
    foco: campo(textos.estrategia ?? '', [
      'Prioridade principal',
      'Próximas prioridades',
      'Foco atual',
      'Foco',
      'Gargalo atual',
    ]),
    tom: campo(textos.preferencias ?? '', ['Tom de voz', 'Tom']),
    arquivos,
    lidoEm: await $.clock.now(),
  }
}

/** Uma linha diz algo quando não é título, citação, régua, campo vazio nem placeholder. */
function dizAlgo(linha: string): boolean {
  const limpa = linha.trim()
  if (limpa === '' || limpa.startsWith('#') || limpa.startsWith('>') || /^-{3,}$/.test(limpa)) {
    return false
  }
  const campoComValor = /^(?:[-*]\s+)?(?:\*\*[^*]+:\*\*|[^:*`]+:)\s*(.*)$/.exec(limpa)
  const valor = campoComValor === null ? limpa : (campoComValor[1] ?? '')
  return valor !== '' && !/^\*\(.*\)\*$/.test(valor) && !/^\[.*\]$/.test(valor)
}

/** O texto tem conteúdo real (alguma linha que diz algo). */
export function temConteudo(texto: string): boolean {
  return texto.split(/\r?\n/).some(dizAlgo)
}

function mesmoTexto(a: string, b: string): boolean {
  const normal = (texto: string) => texto.replace(/\r\n/g, '\n').replace(/[ \t]+/g, ' ').trim()
  return b !== '' && normal(a) === normal(b)
}

function escapar(texto: string): string {
  return texto.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/** Tira marcação de markdown, junta espaços e corta em `maximo` caracteres. */
export function limpar(texto: string, maximo = 90): string {
  const plano = texto
    .replace(/\*\*|__|`/g, '')
    .replace(/^[-*]\s+/, '')
    .replace(/\s+/g, ' ')
    .trim()
  return plano.length > maximo ? `${plano.slice(0, maximo - 1).trimEnd()}…` : plano
}

/**
 * O valor de um campo, pelo primeiro rótulo que achar: `**Rótulo:** valor`
 * numa linha, ou a primeira linha com conteúdo da seção `## Rótulo`.
 */
export function campo(texto: string, rotulos: readonly string[]): string | null {
  for (const rotulo of rotulos) {
    const r = escapar(rotulo)
    const inline = new RegExp(`^\\s*(?:[-*]\\s+)?\\*\\*${r}:?\\*\\*:?\\s*(.+?)\\s*$`, 'im').exec(texto)
    const valorInline = inline?.[1]
    if (valorInline !== undefined && dizAlgo(valorInline)) return limpar(valorInline)

    const secao = new RegExp(
      `^#{1,6}[ \\t]*${r}[ \\t]*\\r?\\n([\\s\\S]*?)(?=^#{1,6}[ \\t]|(?![\\s\\S]))`,
      'im',
    ).exec(texto)
    const corpo = secao?.[1]
    if (corpo !== undefined) {
      const linha = corpo.split(/\r?\n/).find(dizAlgo)
      if (linha !== undefined) return limpar(linha)
    }
  }
  return null
}

/** O H1 do arquivo quando ele é um nome próprio, não o título do template. */
function tituloProprio(texto: string): string | null {
  const h1 = /^#\s+(.+?)\s*$/m.exec(texto)?.[1]
  if (h1 === undefined) return null
  const limpo = limpar(h1)
  return TITULOS_DE_TEMPLATE.has(limpo.toLowerCase()) ? null : limpo
}
