import { atom, read, update } from 'claude-code'
import type { EngineInterface, InstructionFile, Register } from 'claude-code'

import type { MazyosArquivo, MazyosWorkspace } from '../types'
import { arquivoVigiado, lerTexto, lerWorkspace } from './memoria'
import { secaoSistema } from './sistema'

const PAINEL = 'mazyos'
const COMANDO = 'mazyos'
const SIM = 'Sim, pode rodar'
const NAO = 'Não, cancela'

// Troque a tag quando os campos de MazyosWorkspace mudarem: o valor que uma
// versão anterior guardou sobrevive ao reload e seria lido com a forma antiga.
const workspace = atom({ plugin: 'mazyos', key: 'workspace' } as const, null, {
  shape: 'workspace-1',
})

/** Comandos git que apagam histórico ou mudanças sem volta. */
const PERIGOSOS: readonly { regra: RegExp; nome: string }[] = [
  {
    regra: /\bgit\s+push\b(?:[^|;&\n]*\s)?(?:--force(?:-with-lease)?|-f)\b/,
    nome: 'git push --force',
  },
  { regra: /\bgit\s+reset\s+(?:[^|;&\n]*\s)?--hard\b/, nome: 'git reset --hard' },
  { regra: /\bgit\s+clean\b[^|;&\n]*\s-[a-zA-Z]*f/, nome: 'git clean -f' },
  { regra: /\bgit\s+checkout\s+--\s+\.(?:\s|$)/, nome: 'git checkout -- .' },
  { regra: /\bgit\s+restore\s+(?:[^|;&\n]*\s)?\.(?:\s|$)/, nome: 'git restore .' },
  { regra: /\bgit\s+branch\s+(?:[^|;&\n]*\s)?-D\b/, nome: 'git branch -D' },
]

const DIA = 24 * 60 * 60 * 1000

function haQuanto(agora: number, mtimeMs: number): string {
  const dias = Math.floor(Math.max(0, agora - mtimeMs) / DIA)
  if (dias === 0) return 'hoje'
  if (dias === 1) return 'ontem'
  if (dias < 14) return `há ${dias} dias`
  if (dias < 60) return `há ${Math.floor(dias / 7)} semanas`
  return `há ${Math.floor(dias / 30)} meses`
}

function estadoDoArquivo(arquivo: MazyosArquivo, agora: number): string {
  if (!arquivo.existe) return 'não existe'
  if (!arquivo.preenchido) return 'em branco'
  return arquivo.mtimeMs > 0 ? `atualizado ${haQuanto(agora, arquivo.mtimeMs)}` : 'preenchido'
}

function linhaDeStatus(ws: MazyosWorkspace): string {
  const partes = ['MazyOS', ws.nome ?? 'negócio sem nome']
  if (ws.foco !== null) partes.push(`foco: ${ws.foco}`)
  return partes.join(' · ')
}

function resumo(ws: MazyosWorkspace, painelColocado: boolean): string {
  if (!ws.instalado) {
    return `MazyOS: a pasta ${ws.raiz} ainda não tem workspace. Rode /mazyos:instalar pra ligar o sistema aqui.`
  }
  const memoria = ws.arquivos
    .map(arquivo => `${arquivo.rotulo} ${arquivo.preenchido ? '●' : '○'}`)
    .join(' · ')
  return [
    linhaDeStatus(ws),
    `Memória: ${memoria}`,
    painelColocado
      ? 'Painel aberto ao lado.'
      : 'Painel aberto; ele aparece quando o terminal tiver largura pra ele.',
  ].join('\n')
}

function mostrarStatus($: EngineInterface, ws: MazyosWorkspace | null, comLinha: boolean): void {
  $.ui.status(comLinha && ws !== null && ws.instalado ? linhaDeStatus(ws) : undefined)
}

/** Relê o workspace, guarda em `$.state` (o painel redesenha) e atualiza a linha de status. */
async function recarregar(
  $: EngineInterface,
  comLinha: boolean,
  raiz?: string,
): Promise<MazyosWorkspace> {
  const atual = await read($, workspace)
  const base = raiz ?? atual?.raiz ?? (await $.session.root())
  const novo = await lerWorkspace($, base)
  await update($, workspace, () => novo)
  mostrarStatus($, novo, comLinha)
  return novo
}

/** O workspace como está no estado, ou lido agora quando a sessão ainda não o leu. */
async function workspaceAtual($: EngineInterface): Promise<MazyosWorkspace> {
  return (await read($, workspace)) ?? (await lerWorkspace($, await $.session.root()))
}

/** As memórias preenchidas como arquivos de instrução, fora as que já estão na lista. */
async function arquivosDeMemoria(
  $: EngineInterface,
  ws: MazyosWorkspace,
  presentes: ReadonlySet<string>,
): Promise<InstructionFile[]> {
  const novos: InstructionFile[] = []
  for (const arquivo of ws.arquivos) {
    if (arquivo.chave === 'design' || !arquivo.preenchido || presentes.has(arquivo.caminho)) {
      continue
    }
    const content = await lerTexto($, arquivo.caminho)
    if (content.trim() !== '') novos.push({ path: arquivo.caminho, kind: 'project', content })
  }
  return novos
}

/** Depois de uma escrita que deu certo num arquivo vigiado: relê, avisa e pede o contexto de novo. */
async function aposEditar(
  $: EngineInterface,
  caminho: string,
  ran: { deny?: string; isError?: boolean },
  comLinha: boolean,
): Promise<void> {
  if (ran.deny !== undefined || ran.isError === true) return
  const ws = await read($, workspace)
  const raiz = ws?.raiz ?? (await $.session.root())
  const relativo = arquivoVigiado(raiz, caminho)
  if (relativo === undefined) return
  const novo = await recarregar($, comLinha, raiz)
  $.ui.invalidate('prompt.context')
  $.ui.toast(
    novo.instalado
      ? `MazyOS: ${relativo} atualizado. Memória recarregada.`
      : `MazyOS: ${relativo} atualizado.`,
  )
}

export const register: Register = (on, options) => {
  const abrirPainel = options.abrirPainel !== false
  const comLinha = options.linhaDeStatus !== false
  const protegerGit = options.protegerGit !== false

  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: COMANDO,
      description: 'Abre o painel do MazyOS: memória do negócio, foco atual e atalhos das skills.',
    })
    const ws = await recarregar($, comLinha, e.cwd)

    if (ws.instalado) {
      if (abrirPainel && e.isInteractive) void $.ui.open({ id: PAINEL, title: 'MazyOS' })
    } else if (e.isInteractive) {
      // Um aviso por pasta, uma vez só: o plugin pode estar instalado no
      // escopo do usuário e aparecer em projetos que nada têm a ver com ele.
      const chave = `avisado:${ws.raiz}`
      if ((await $.store.get(chave)) === undefined) {
        await $.store.set(chave, true)
        $.ui.toast('MazyOS instalado. Pra ligar o sistema nessa pasta, rode /mazyos:instalar.')
      }
    }

    return next(e)
  })

  on('command.run', { command: COMANDO }, async $ => {
    const ws = await recarregar($, comLinha)
    const aberto = await $.ui.open({ id: PAINEL, title: 'MazyOS' })
    return { text: resumo(ws, aberto.isPlaced) }
  })

  // As regras de operação do MazyOS entram no fim do system prompt.
  on('prompt.compose', async ($, e, next) => {
    const composto = await next(e)
    if (e.traits.includes('bare')) return composto
    const ws = await workspaceAtual($)
    return {
      sections: [
        ...composto.sections,
        { id: 'mazyos:sistema', text: secaoSistema(ws, $.plugin.root), scope: 'session' },
      ],
    }
  })

  // A memória do negócio entra como arquivo de instrução, ao lado do CLAUDE.md:
  // o engine a reenvia quando o arquivo muda, como faz com o CLAUDE.md.
  on('prompt.context', async ($, e, next) => {
    const composto = await next(e)
    const ws = await workspaceAtual($)
    if (!ws.instalado || composto.instructionFiles === undefined) return composto
    const presentes = new Set(composto.instructionFiles.map(arquivo => arquivo.path))
    const novos = await arquivosDeMemoria($, ws, presentes)
    if (novos.length === 0) return composto
    return { ...composto, instructionFiles: [...composto.instructionFiles, ...novos] }
  })

  on('tool.call', { tool: 'Write' }, async ($, e, next) => {
    const ran = await next(e)
    await aposEditar($, e.file_path, ran, comLinha).catch(() => undefined)
    return ran
  })

  on('tool.call', { tool: 'Edit' }, async ($, e, next) => {
    const ran = await next(e)
    await aposEditar($, e.file_path, ran, comLinha).catch(() => undefined)
    return ran
  })

  // Guarda: um comando git que apaga trabalho só roda com o sim do usuário.
  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    if (!protegerGit) return next(e)
    const perigo = PERIGOSOS.find(candidato => candidato.regra.test(e.command))
    if (perigo === undefined) return next(e)
    const ws = await read($, workspace)
    if (ws === null || !ws.instalado) return next(e)

    const resposta = await $.ui.ask(
      `O MazyOS vai rodar "${perigo.nome}", que apaga histórico ou mudanças sem volta. Pode seguir?`,
      [SIM, NAO],
    )
    if (resposta !== SIM) {
      return {
        deny: `MazyOS: "${perigo.nome}" cancelado pelo usuário. Explique a situação e proponha um caminho que não perca trabalho.`,
      }
    }
    return next(e)
  }).catch(($, e, next) =>
    next.called
      ? next(e)
      : {
          deny: 'MazyOS: não deu pra confirmar com o usuário um comando git que apaga trabalho, então ele não rodou. Peça confirmação explícita antes de tentar de novo.',
        },
  )

  on('ui.render', { component: 'Pane', requestId: PAINEL }, async ($, e) => {
    const { Box, Text, Button } = $.ui.resolve(e)
    const ws = await read($, workspace)
    const agora = await $.clock.now()
    const preencher = (texto: string) => () => $.prompt.fill({ text: texto, mode: 'replace' })

    if (ws === null || !ws.instalado) {
      return (
        <Box flexDirection="column" gap={1}>
          <Text weight="bold">MazyOS</Text>
          <Text dimColor wrap="wrap">
            Essa pasta ainda não tem um workspace MazyOS. O /mazyos:instalar cria aqui a memória
            do negócio, a identidade visual e as pastas de saída, e faz a entrevista de setup.
          </Text>
          <Box gap={1} flexWrap="wrap">
            <Button
              key="instalar"
              label="Instalar aqui"
              variant="primary"
              hotkey="i"
              onPress={preencher('/mazyos:instalar')}
            />
            <Button
              key="recarregar"
              label="Recarregar"
              hotkey="r"
              onPress={() => recarregar($, comLinha)}
            />
          </Box>
        </Box>
      )
    }

    const maiorRotulo = Math.max(...ws.arquivos.map(arquivo => arquivo.rotulo.length))

    return (
      <Box flexDirection="column" gap={1}>
        <Box flexDirection="column">
          <Text weight="bold">MazyOS · {ws.nome ?? 'negócio sem nome'}</Text>
          {ws.negocio !== null && (
            <Text dimColor wrap="wrap">
              {ws.negocio}
            </Text>
          )}
        </Box>

        <Box flexDirection="column">
          <Text wrap="wrap">
            <Text weight="semibold">Foco: </Text>
            {ws.foco ?? 'em branco'}
          </Text>
          <Text wrap="wrap">
            <Text weight="semibold">Tom: </Text>
            {ws.tom ?? 'em branco'}
          </Text>
        </Box>

        <Box flexDirection="column">
          <Text weight="semibold">Memória</Text>
          {ws.arquivos.map(arquivo => (
            <Text wrap="truncate-end">
              <Text color={arquivo.preenchido ? 'success' : 'warning'}>
                {arquivo.preenchido ? '●' : '○'}
              </Text>{' '}
              {arquivo.rotulo.padEnd(maiorRotulo)}{' '}
              <Text dimColor>{estadoDoArquivo(arquivo, agora)}</Text>
            </Text>
          ))}
        </Box>

        <Box gap={1} flexWrap="wrap">
          <Button key="abrir" label="Abrir sessão" hotkey="a" onPress={preencher('/mazyos:abrir')} />
          <Button
            key="atualizar"
            label="Atualizar memória"
            hotkey="m"
            onPress={preencher('/mazyos:atualizar')}
          />
          <Button
            key="salvar"
            label="Salvar no GitHub"
            hotkey="s"
            onPress={preencher('/mazyos:salvar')}
          />
          <Button key="recarregar" label="Recarregar" hotkey="r" onPress={() => recarregar($, comLinha)} />
        </Box>

        <Text dimColor>Lido {haQuanto(agora, ws.lidoEm)} · /mazyos reabre este painel</Text>
      </Box>
    )
  })
}
