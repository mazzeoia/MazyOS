import { expect, mock, test } from 'claude-code/testing'
import type { On } from 'claude-code'

const RAIZ = '/negocio'

/** O que o engine compõe um system prompt a partir de: os fatos de uma sessão comum. */
const COMPOSE = {
  model: 'claude',
  promptModel: 'claude',
  surfaces: ['terminal'],
  tools: [],
  outputStyle: null,
  traits: [],
} as const

const PANE = {
  plugin: 'mazyos',
  component: 'Pane',
  requestId: 'mazyos',
  props: {
    title: 'MazyOS',
    isFocused: false,
    bodyColumns: 48,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 30 },
    view: {},
  },
} as const

const ARQUIVOS: Record<string, string> = {
  [`${RAIZ}/_memoria/empresa.md`]:
    '# Empresa\n\n**Nome:** Acme Marcenaria\n**O que faz:** móveis planejados sob medida\n',
  [`${RAIZ}/_memoria/preferencias.md`]: '# Preferências\n\n## Tom de voz\n\nDireto, sem jargão\n',
  [`${RAIZ}/_memoria/estrategia.md`]:
    '# Estratégia\n\n## Prioridade principal\n\nFechar 3 clientes até dezembro\n',
}

/** O disco de um workspace instalado: `_memoria/` e três memórias preenchidas. */
function discoInstalado(on: On, arquivos: Record<string, string>) {
  on('fs.exists', (_, e) => ({ value: e.path === `${RAIZ}/_memoria` || e.path in arquivos }))
  on('fs.read', (_, e) => ({ value: arquivos[e.path] ?? '' }))
  on('fs.stat', () => ({ value: { kind: 'file', size: 10, mtimeMs: 1000, isLink: false } }))
}

/** O que a sessão responde às chamadas do mod em `session.start`. */
function sessao(on: On) {
  on('command.register', (_, e) => ({ value: { command: e.name } }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.status', () => ({ value: undefined }))
  on('ui.toast', () => ({ value: undefined }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.root', () => ({ value: RAIZ }))
}

test('o painel mostra o negócio e os atalhos em toda surface', async ($, on) => {
  discoInstalado(on, ARQUIVOS)
  mock.clock(on, { now: 100_000 })
  mock.store(on)
  sessao(on)

  await $.session.start({ cwd: RAIZ, surface: 'terminal', isInteractive: true })

  for (const surface of ['terminal', 'desktop', 'vscode', 'mobile'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect(await ui.find({ type: 'Text', text: /Acme Marcenaria/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /Fechar 3 clientes/ })).toBeDefined()
    expect(await ui.find({ key: 'abrir' })).toBeDefined()
    expect(await ui.find({ key: 'salvar' })).toBeDefined()
    await ui.unmount()
  }
})

test('sem workspace: aviso uma vez por pasta, sem status, painel oferece instalar', async ($, on) => {
  on('fs.exists', () => ({ value: false }))
  on('fs.read', () => ({ value: '' }))
  on('fs.stat', () => ({ value: { kind: 'file', size: 0, mtimeMs: 0, isLink: false } }))
  mock.clock(on)
  mock.store(on)
  const status: (string | undefined)[] = []
  on('ui.status', (_, e) => {
    status.push(e.text)
    return { value: undefined }
  })
  const toasts: string[] = []
  on('ui.toast', (_, e) => {
    toasts.push(e.text)
    return { value: undefined }
  })
  on('command.register', (_, e) => ({ value: { command: e.name } }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))

  await $.session.start({ cwd: '/outro-projeto', surface: 'terminal', isInteractive: true })
  expect(toasts.length).toBe(1)
  expect(status.at(-1)).toBe(undefined)

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ key: 'instalar' })).toBeDefined()
  await ui.unmount()

  // A mesma pasta de novo: o aviso não se repete.
  await $.session.start({ cwd: '/outro-projeto', surface: 'terminal', isInteractive: true })
  expect(toasts.length).toBe(1)
})

test('a seção do MazyOS entra no fim do system prompt, mesmo antes de session.start', async ($, on) => {
  discoInstalado(on, ARQUIVOS)
  mock.clock(on)
  on('session.root', () => ({ value: RAIZ }))
  on('prompt.compose', () => ({
    sections: [{ id: 'intro', text: 'engine', scope: 'shared' }],
  }))

  const { sections } = await $.prompt.compose(COMPOSE)
  const ultima = sections.at(-1)

  expect(sections[0]?.id).toBe('intro')
  expect(ultima?.id).toBe('mazyos:sistema')
  expect(ultima?.scope).toBe('session')
  expect(/Acme Marcenaria/.test(ultima?.text ?? '')).toBe(true)
  expect(/\/mazyos:instalar/.test(ultima?.text ?? '')).toBe(true)
})

test('a memória preenchida entra como arquivo de instrução, sem duplicar', async ($, on) => {
  discoInstalado(on, ARQUIVOS)
  mock.clock(on)
  on('session.root', () => ({ value: RAIZ }))
  on('prompt.context', () => ({
    blocks: [],
    instructionFiles: [
      { path: `${RAIZ}/_memoria/empresa.md`, kind: 'project', content: 'já estava' },
    ],
  }))

  const { instructionFiles } = await $.prompt.context({ blocks: [], instructionFiles: [] })
  const caminhos = (instructionFiles ?? []).map(arquivo => arquivo.path)

  expect(caminhos.length).toBe(3)
  expect(caminhos.filter(caminho => caminho.endsWith('empresa.md')).length).toBe(1)
  expect(caminhos.some(caminho => caminho.endsWith('estrategia.md'))).toBe(true)
  expect(caminhos.some(caminho => caminho.endsWith('design-guide.md'))).toBe(false)
})

test('git destrutivo sem como confirmar é negado; o resto passa', async ($, on) => {
  discoInstalado(on, ARQUIVOS)
  mock.clock(on)
  mock.store(on)
  sessao(on)
  on('tool.call', (_, e) => {
    if (e.tool === 'AskUserQuestion') throw new Error('ninguém pra perguntar')
    return { result: {} }
  })

  await $.session.start({ cwd: RAIZ, surface: 'terminal', isInteractive: true })

  const forcado = await $.tool.call({ tool: 'Bash', command: 'git push --force origin main' })
  expect(forcado.deny).toBeDefined()

  const duro = await $.tool.call({ tool: 'Bash', command: 'git reset --hard HEAD~1' })
  expect(duro.deny).toBeDefined()

  const normal = await $.tool.call({ tool: 'Bash', command: 'git push origin main' })
  expect(normal.deny).toBe(undefined)
})

test('git destrutivo passa com protegerGit desligado', { options: { protegerGit: false } }, async ($, on) => {
  discoInstalado(on, ARQUIVOS)
  mock.clock(on)
  mock.store(on)
  sessao(on)
  on('tool.call', () => ({ result: {} }))

  await $.session.start({ cwd: RAIZ, surface: 'terminal', isInteractive: true })
  const forcado = await $.tool.call({ tool: 'Bash', command: 'git push --force origin main' })
  expect(forcado.deny).toBe(undefined)
})

test('editar a memória recarrega o estado, a linha de status e avisa', async ($, on) => {
  const arquivos = { ...ARQUIVOS }
  discoInstalado(on, arquivos)
  mock.clock(on)
  mock.store(on)
  on('command.register', (_, e) => ({ value: { command: e.name } }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.root', () => ({ value: RAIZ }))
  on('ui.invalidate', () => ({ value: undefined }))
  const status: (string | undefined)[] = []
  on('ui.status', (_, e) => {
    status.push(e.text)
    return { value: undefined }
  })
  const toasts: string[] = []
  on('ui.toast', (_, e) => {
    toasts.push(e.text)
    return { value: undefined }
  })
  on('tool.call', (_, e) => {
    if (e.tool === 'Write') arquivos[e.file_path] = e.content
    return { result: {} }
  })

  await $.session.start({ cwd: RAIZ, surface: 'terminal', isInteractive: true })
  expect(status.at(-1)).toBe('MazyOS · Acme Marcenaria · foco: Fechar 3 clientes até dezembro')

  await $.tool.call({
    tool: 'Write',
    file_path: `${RAIZ}/_memoria/estrategia.md`,
    content: '# Estratégia\n\n## Prioridade principal\n\nLançar o site novo\n',
  })
  expect(status.at(-1)).toBe('MazyOS · Acme Marcenaria · foco: Lançar o site novo')
  expect(toasts.some(toast => toast.includes('estrategia.md'))).toBe(true)

  // Um arquivo qualquer não mexe em nada.
  const antes = toasts.length
  await $.tool.call({ tool: 'Write', file_path: `${RAIZ}/saidas/email.md`, content: 'oi' })
  expect(toasts.length).toBe(antes)
})

test('um valor guardado por uma versão anterior é recusado e relido', async ($, on) => {
  discoInstalado(on, ARQUIVOS)
  mock.clock(on)
  on('session.root', () => ({ value: RAIZ }))
  on('prompt.compose', () => ({ sections: [] }))
  on('state.get', () => ({ value: { value: { raiz: RAIZ, instalado: true }, version: 1 } }))

  const { sections } = await $.prompt.compose(COMPOSE)
  expect(/Acme Marcenaria/.test(sections.at(-1)?.text ?? '')).toBe(true)
})
