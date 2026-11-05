/**
 * Contrato do estado do MazyOS em `$.state`: o que o painel, a linha de
 * status e os hooks leem sobre o workspace do negócio na sessão.
 */

export type MazyosChave = 'empresa' | 'preferencias' | 'estrategia' | 'design'

export type MazyosArquivo = {
  /** Qual memória é: empresa, preferencias, estrategia ou design (identidade). */
  chave: MazyosChave
  /** Como o painel chama o arquivo (`empresa.md`). */
  rotulo: string
  /** Caminho absoluto no workspace. */
  caminho: string
  /** O arquivo existe no disco. */
  existe: boolean
  /** Tem conteúdo real, além do template em branco. */
  preenchido: boolean
  /** Última modificação, em milissegundos desde a época; 0 quando não há. */
  mtimeMs: number
}

export type MazyosWorkspace = {
  /** A raiz do workspace (a pasta do negócio), absoluta. */
  raiz: string
  /** A pasta tem `_memoria/`: é um workspace MazyOS. */
  instalado: boolean
  /** Nome do negócio, lido de `_memoria/empresa.md`; null se não achou. */
  nome: string | null
  /** O que o negócio faz, em uma linha; null se não achou. */
  negocio: string | null
  /** Prioridade principal de `_memoria/estrategia.md`; null se não achou. */
  foco: string | null
  /** Resumo do tom de voz de `_memoria/preferencias.md`; null se não achou. */
  tom: string | null
  /** Os arquivos de memória, na ordem do painel. */
  arquivos: MazyosArquivo[]
  /** Quando essa leitura foi feita (`$.clock.now()`). */
  lidoEm: number
}

declare module 'claude-code' {
  interface PluginState {
    mazyos: { workspace: Shaped<MazyosWorkspace | null> }
  }
}
