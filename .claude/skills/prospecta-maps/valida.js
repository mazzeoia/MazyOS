// Índice: bases públicas (baixarBase, porCnpj) · casamento (avaliar) · site fora da ficha (checarSite) · critérios e veredito (laço principal) · saída
// Acha o CNPJ de cada candidata sem busca paga: baixa da Receita as empresas do ramo na cidade e casa por telefone, CEP e nome.
// Uso: node valida.js <candidatos.json> <validados.json> --cidade "Curitiba" --cnae 3101200,3329501
//      [--uf PR] [--anos 3] [--aceita-mei] [--buscas buscas.json] [--genericas "marcenar|moveis"] [--sem-receita]
// buscas.json (opcional, pra quem ficou sem CNPJ): { "Nome da empresa": { "cnpjs": ["..."], "links": ["..."] } }
// Veredito: aprovado · revisar (precisa de olho humano) · reprovado · sem_cnpj
const fs = require('fs');
const path = require('path');
const { args, lerJSON, gravarJSON, sleep, digits, norm, UA, telBR } = require('./comum');

const opt = args();
const [inPath, outPath] = opt._;
if (!inPath || !outPath) { console.error('Uso: node valida.js <candidatos.json> <validados.json> --cidade "X" --cnae 123,456'); process.exit(1); }
const entrada = lerJSON(inPath);
const candidatos = entrada.candidatos || entrada;
const CIDADE = norm(opt.cidade || '');
const CNAES = String(opt.cnae || '').split(',').map(digits).filter(Boolean);
const ANOS = Number(opt.anos ?? 3);
const buscas = opt.buscas && fs.existsSync(opt.buscas) ? lerJSON(opt.buscas) : {};
const pastaBase = path.join(path.dirname(path.resolve(outPath)), '.base-receita');
const MAX_POR_CNAE = Number(opt['max-por-cnae'] || 80000);

const PALAVRAS_VAZIAS = new Set(['ltda', 'eireli', 'epp', 'cia', 'comercio', 'servicos', 'servico', 'industria', 'empresa', 'grupo', 'para', 'com', 'dos', 'das', 'the', 'and', 'solucoes', 'brasil', 'loja', 'unidade']);
const GENERICAS = opt.genericas ? new RegExp(norm(opt.genericas)) : null;
const DIRETORIOS = /google\.|facebook|instagram|linkedin|youtube|tiktok|cnpj|guiafacil|solutudo|econodata|apontador|telelistas|empresaqui|guiapj|cnpja|casadosdados|speedio|consultas|wikipedia|reclameaqui|jusbrasil|waze|yelp|tripadvisor|olx|mercadolivre|encontra|guiamais|listamais|infobel|cylex|hotfrog|tudosobre|doctoralia|glassdoor|indeed|catho|infojobs|kompass|dnb\.com|bing\.|yahoo|wa\.me|whatsapp|linktr|threads|twitter|gov\.br|serasa|zoominfo/i;
const EMAIL_GRATIS = /gmail|hotmail|outlook|yahoo|uol|bol\.com|terra\.com|ig\.com|live\.|icloud|globo|msn|contabil|contab/i;

const palavras = s => norm(s).split(/[^a-z0-9]+/).filter(Boolean);
const compacto = s => norm(s).replace(/[^a-z0-9]/g, '');

// Palavra que aparece em muitas candidatas ("marcenaria", "móveis") não identifica ninguém.
const frequencia = new Map();
for (const c of candidatos) for (const p of new Set(palavras(c.title))) frequencia.set(p, (frequencia.get(p) || 0) + 1);
const frequenciaBase = new Map();
const porPalavra = new Map();
let totalBase = 0;
const generica = p => PALAVRAS_VAZIAS.has(p) || (GENERICAS && GENERICAS.test(p)) || (candidatos.length >= 8 && frequencia.get(p) / candidatos.length > 0.1) || (totalBase > 200 && (frequenciaBase.get(p) || 0) / totalBase > 0.015);

async function pegarJSON(url, tentativas = 6) {
  for (let t = 0; t < tentativas; t++) {
    let r;
    try { r = await fetch(url, { headers: UA, signal: AbortSignal.timeout(60000) }); } catch { await sleep(3000); continue; }
    if (r.ok) return r.json();
    if (r.status === 404) return null;
    await sleep(r.status === 429 ? 4000 * (t + 1) : 2000);
  }
  throw new Error('sem resposta: ' + url);
}

// Minha Receita primeiro; a BrasilAPI usa os mesmos campos e entra de reserva.
async function porCnpj(cnpj) {
  try { const d = await pegarJSON('https://minhareceita.org/' + cnpj, 2); if (d) return d; } catch {}
  try { return await pegarJSON('https://brasilapi.com.br/api/cnpj/v1/' + cnpj, 2); } catch { return null; }
}

async function codigoMunicipio() {
  const todos = await pegarJSON('https://servicodados.ibge.gov.br/api/v1/localidades/municipios?view=nivelado');
  let achados = todos.filter(m => norm(m['municipio-nome']) === CIDADE);
  if (opt.uf) achados = achados.filter(m => m['UF-sigla'] === String(opt.uf).toUpperCase());
  // Erro de digitação ou cidade repetida a pessoa resolve agora: não adianta seguir sem a base.
  const parar = msg => { const e = new Error(msg); e.parar = true; throw e; };
  if (!achados.length) parar(`Município "${opt.cidade}" não encontrado no IBGE. Confira o nome.`);
  if (achados.length > 1) parar(`Há ${achados.length} municípios chamados "${opt.cidade}" (${achados.map(m => m['UF-sigla']).join(', ')}). Passe --uf.`);
  return achados[0]['municipio-id'];
}

// Baixa o ramo inteiro na cidade e guarda só o necessário pra casar. Sem sócio e sem e-mail aqui: dado pessoal fica de fora do cache.
async function baixarBase(municipio, cnae) {
  fs.mkdirSync(pastaBase, { recursive: true });
  const arq = path.join(pastaBase, `${municipio}-${cnae}.json`);
  if (fs.existsSync(arq) && Date.now() - fs.statSync(arq).mtimeMs < 7 * 864e5) return lerJSON(arq);
  const lista = [];
  let cursor = '';
  while (lista.length < MAX_POR_CNAE) {
    const j = await pegarJSON(`https://minhareceita.org/?municipio=${municipio}&cnae=${cnae}&limit=1000${cursor ? '&cursor=' + cursor : ''}`);
    if (!j || !j.data || !j.data.length) break;
    for (const d of j.data) lista.push({
      cnpj: d.cnpj, r: d.razao_social, f: d.nome_fantasia,
      t: [d.ddd_telefone_1, d.ddd_telefone_2].map(digits).filter(Boolean),
      c: digits(d.cep), n: digits(d.numero), s: d.descricao_situacao_cadastral
    });
    process.stdout.write(`\r  CNAE ${cnae}: ${lista.length} empresas`);
    if (!j.cursor) break;
    cursor = j.cursor;
  }
  process.stdout.write('\n');
  fs.writeFileSync(arq, JSON.stringify(lista));
  return lista;
}

// Compara uma candidata com uma empresa da Receita e diz o que bateu.
function avaliar(c, e, tokens, razoesNasAvaliacoes) {
  const tel = telBR(c.phone);
  const cep = digits(c.complete_address?.postal_code);
  const numeroFicha = digits((c.complete_address?.street || c.address || '').split(/[,-]/)[1]);
  const porTel = tel.length >= 10 && e.t.some(t => t.slice(-8) === tel.slice(-8));
  const porCep = cep.length === 8 && e.c === cep;
  const porEndereco = !porCep && cep.length === 8 && numeroFicha && e.n === numeroFicha && e.c.slice(0, 5) === cep.slice(0, 5);
  // CEP pode diferir no final (02542-000 na Receita, 02542-110 na ficha): início igual conta como região.
  const porRegiao = !porCep && !porEndereco && cep.length === 8 && e.c.slice(0, 5) === cep.slice(0, 5);
  const nomeReceita = palavras(`${e.r} ${e.f}`);
  const compactoReceita = compacto(`${e.r} ${e.f}`);
  const porNome = tokens.some(w => nomeReceita.includes(w) || (w.length >= 4 && nomeReceita.some(n => n.startsWith(w))) || (w.length >= 5 && compactoReceita.includes(w)));
  // Firma no nome do dono: "Souza Design" é "ERINALDO ...", e as avaliações citam o Erinaldo.
  const primeiro = palavras(e.r).find(w => w.length >= 4 && !generica(w));
  const porAvaliacao = !porNome && Boolean(primeiro) && razoesNasAvaliacoes.includes(` ${primeiro} `);
  return { porTel, porCep, porEndereco, porRegiao, porNome, porAvaliacao };
}

async function checarDominio(dominio, tel, tokens, ramo) {
  for (const base of [`https://www.${dominio}`, `https://${dominio}`]) {
    try {
      const r = await fetch(base, { headers: UA, redirect: 'follow', signal: AbortSignal.timeout(8000) });
      if (!r.ok) continue;
      const html = (await r.text()).slice(0, 600000);
      const destino = new URL(r.url).hostname.replace(/^www\./, '');
      const texto = norm(html);
      const soDigitos = html.replace(/\D/g, '');
      return {
        dominio, destino, tamanho: html.length,
        telefone_bate: tel.length >= 10 && soDigitos.includes(tel.slice(-8)),
        // O nome sozinho engana: um domínio com a mesma palavra pode ser de outro negócio. Precisa falar do ramo também.
        nome_bate: tokens.some(w => texto.includes(w)) && (!ramo.length || ramo.some(w => texto.includes(w)))
      };
    } catch {}
  }
  return null;
}

// "Sem site" é só o que a ficha diz. Testa os domínios óbvios, o do e-mail na Receita e os que vieram da busca web.
async function checarSite(c, tokens, rec, linksBusca) {
  const tel = telBR(c.phone);
  const nome = compacto(c.title.replace(/\s*[|(].*$/, ''));
  const palpites = new Set();
  if (nome.length >= 4) for (const t of ['.com.br', '.com']) palpites.add(nome + t);
  if (tokens.length) { palpites.add(tokens.join('') + '.com.br'); }
  if (rec?.f) { const f = compacto(rec.f); if (f.length >= 4) palpites.add(f + '.com.br'); }
  let dominioEmail = null;
  if (rec?.email && !EMAIL_GRATIS.test(rec.email)) { dominioEmail = rec.email.split('@')[1]?.toLowerCase(); if (dominioEmail) palpites.add(dominioEmail); }
  for (const l of linksBusca) {
    const d = String(l).replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0].toLowerCase();
    if (d && !DIRETORIOS.test(d) && tokens.some(w => compacto(d).includes(w.slice(0, 6)))) palpites.add(d);
  }
  const lista = [...palpites].slice(0, 10);
  const ramo = palavras(c.title).filter(w => w.length >= 5 && generica(w) && !PALAVRAS_VAZIAS.has(w));
  const resultados = (await Promise.all(lista.map(d => checarDominio(d, tel, tokens, ramo)))).filter(Boolean);
  const confirmado = resultados.filter(r => r.telefone_bate);
  const possivel = resultados.filter(r => !r.telefone_bate && r.nome_bate && r.tamanho > 1500);
  return {
    testados: lista.length,
    confirmado: confirmado.map(r => r.dominio),
    possivel: possivel.map(r => r.dominio),
    dominio_do_email_fora_do_ar: dominioEmail && !resultados.some(r => r.dominio === dominioEmail) ? dominioEmail : null
  };
}

async function matrizDe(cnpj) {
  const corpo = cnpj.slice(0, 8) + '0001';
  const p1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2], p2 = [6, ...p1];
  let s1 = 0, s2 = 0;
  for (let i = 0; i < 12; i++) s1 += corpo[i] * p1[i];
  const d1 = s1 % 11 < 2 ? 0 : 11 - s1 % 11;
  for (let i = 0; i < 13; i++) s2 += (corpo + d1)[i] * p2[i];
  const d2 = s2 % 11 < 2 ? 0 : 11 - s2 % 11;
  return porCnpj(corpo + d1 + d2);
}

const anosDesde = data => (Date.now() - new Date(data).getTime()) / (365.25 * 864e5);

(async () => {
  const usarBase = !opt['sem-receita'] && CNAES.length && CIDADE;
  let base = [];
  let avisoBase = '';
  if (usarBase) {
    try {
      const municipio = await codigoMunicipio();
      const mapa = new Map();
      for (const cnae of CNAES) for (const e of await baixarBase(municipio, cnae)) mapa.set(e.cnpj, e);
      base = [...mapa.values()];
      totalBase = base.length;
      for (const e of base) for (const p of new Set(palavras(e.r + ' ' + e.f))) {
        frequenciaBase.set(p, (frequenciaBase.get(p) || 0) + 1);
        if (!porPalavra.has(p)) porPalavra.set(p, []);
        porPalavra.get(p).push(e);
      }
      console.log(`Base da Receita: ${base.length} empresas em ${opt.cidade}, CNAEs ${CNAES.join(', ')}`);
    } catch (e) {
      if (e.parar) throw e;
      avisoBase = e.message;
      console.error('Base por ramo indisponível:', e.message, '\nSeguindo só com buscas.json. Rode de novo mais tarde.');
    }
  }
  const porTelefone = new Map(), porCepMapa = new Map();
  base.forEach(e => {
    e.t.forEach(t => { const k = t.slice(-8); if (!porTelefone.has(k)) porTelefone.set(k, []); porTelefone.get(k).push(e); });
    if (!porCepMapa.has(e.c)) porCepMapa.set(e.c, []);
    porCepMapa.get(e.c).push(e);
  });

  const out = [];
  for (const c of candidatos) {
    const nomeBusca = c.title.replace(/\s*[|(].*$/, '').trim();
    const tokens = [...new Set(palavras(nomeBusca))].filter(w => w.length >= 2 && !generica(w) && !CIDADE.split(/\s+/).includes(w));
    const achado = buscas[c.title] || {};
    const cnpjsWeb = (Array.isArray(achado) ? achado : achado.cnpjs || []).map(digits).filter(x => x.length === 14);
    const linksWeb = Array.isArray(achado) ? [] : achado.links || [];
    const avaliacoesTexto = ' ' + palavras([c.dono, ...(c.user_reviews || []).map(r => r.text)].join(' ')).join(' ') + ' ';

    // Quem pode ser: mesmo telefone, mesmo CEP ou CNPJ vindo da busca web.
    const tel = telBR(c.phone), cep = digits(c.complete_address?.postal_code);
    const pool = new Map();
    (porTelefone.get(tel.slice(-8)) || []).forEach(e => pool.set(e.cnpj, e));
    (porCepMapa.get(cep) || []).forEach(e => pool.set(e.cnpj, e));
    const numeroFicha = digits((c.complete_address?.street || c.address || '').split(/[,-]/)[1]);
    if (cep.length === 8 && numeroFicha) base.forEach(e => { if (e.n === numeroFicha && e.c.slice(0, 5) === cep.slice(0, 5)) pool.set(e.cnpj, e); });
    // Nome raro no ramo e na cidade também traz candidata, mesmo com telefone e CEP diferentes.
    const nomesRaros = new Set();
    for (const w of tokens) {
      const achadas = porPalavra.get(w) || [];
      if (achadas.length && achadas.length <= 30) achadas.forEach(e => { pool.set(e.cnpj, e); nomesRaros.add(e.cnpj); });
    }
    for (const n of cnpjsWeb) {
      if (pool.has(n)) continue;
      const d = await porCnpj(n);
      await sleep(500);
      if (d) pool.set(n, { cnpj: n, r: d.razao_social, f: d.nome_fantasia, t: [d.ddd_telefone_1, d.ddd_telefone_2].map(digits).filter(Boolean), c: digits(d.cep), n: digits(d.numero), s: d.descricao_situacao_cadastral });
    }

    const casados = [...pool.values()].map(e => ({ e, ...avaliar(c, e, tokens, avaliacoesTexto) }))
      .filter(m => m.porTel || m.porCep || m.porEndereco || m.porNome)
      .map(m => {
        const local = m.porTel || m.porCep || m.porEndereco || m.porRegiao;
        // Forte = lugar ou telefone E nome. Só casamento forte pode reprovar uma empresa: casar errado derruba lead bom.
        const forte = local && m.porNome;
        const pontos = (m.porTel ? 3 : 0) + (m.porCep ? 3 : 0) + (m.porEndereco ? 2 : 0) + (m.porNome ? 4 : 0) + (m.porAvaliacao ? 2 : 0) + (m.e.s === 'ATIVA' ? 1 : 0);
        return { ...m, forte, pontos };
      })
      .filter(m => m.forte || m.porTel || m.porAvaliacao || (numeroFicha && m.e.n === numeroFicha) || (m.porNome && nomesRaros.size <= 3))
      .sort((a, b) => b.forte - a.forte || b.pontos - a.pontos);

    const melhor = casados[0];
    const registro = { ...c, cnpj: null, casou_por: [], veredito: 'sem_cnpj', motivos: [], candidatas_cnpj: [], site: null };

    if (melhor) {
      const d = await porCnpj(melhor.e.cnpj);
      await sleep(400);
      registro.candidatas_cnpj = casados.slice(0, 5).map(m => ({
        cnpj: m.e.cnpj, razao: m.e.r, fantasia: m.e.f, situacao: m.e.s,
        bateu: [m.porTel && 'telefone', m.porCep && 'CEP', m.porEndereco && 'número e início do CEP', m.porRegiao && 'região do CEP', m.porNome && 'nome', m.porAvaliacao && 'nome do dono nas avaliações'].filter(Boolean)
      }));
      if (d) {
        registro.cnpj = d.cnpj;
        registro.casou_por = registro.candidatas_cnpj[0].bateu;
        registro.receita = {
          razao: d.razao_social, fantasia: d.nome_fantasia, situacao: d.descricao_situacao_cadastral, abertura: d.data_inicio_atividade,
          porte: d.porte, capital: d.capital_social, mei: d.opcao_pelo_mei, simples: d.opcao_pelo_simples,
          matriz_filial: d.descricao_identificador_matriz_filial, natureza: d.natureza_juridica,
          cnae: `${d.cnae_fiscal} ${d.cnae_fiscal_descricao}`,
          cnaes_sec: (d.cnaes_secundarios || []).filter(x => x.codigo).map(x => `${x.codigo} ${x.descricao}`),
          endereco: `${d.descricao_tipo_de_logradouro || ''} ${d.logradouro}, ${d.numero} ${d.complemento || ''} · ${d.bairro} · ${d.municipio}/${d.uf} · ${d.cep}`,
          socios: (d.qsa || []).map(s => s.nome_socio).filter(Boolean)
        };
        const r = registro.receita;
        const falhas = [];
        if (r.situacao !== 'ATIVA') falhas.push(`situação ${r.situacao}`);
        if (r.mei === true && !opt['aceita-mei']) falhas.push('MEI');
        if (r.abertura && anosDesde(r.abertura) < ANOS) falhas.push(`CNPJ com menos de ${ANOS} anos (${r.abertura})`);
        if (CIDADE && norm(d.municipio) !== CIDADE) falhas.push(`Receita em ${d.municipio}/${d.uf}`);
        if (r.matriz_filial === 'FILIAL') {
          const m = await matrizDe(d.cnpj);
          registro.matriz = m ? `${m.razao_social} · ${m.municipio}/${m.uf}` : 'não encontrada';
          if (!m || norm(m.municipio) !== CIDADE) falhas.push(`filial, matriz em ${m ? m.municipio + '/' + m.uf : 'lugar não encontrado'}`);
        }
        const emailRec = d.email ? { email: d.email } : {};
        registro.site = await checarSite(c, tokens, { f: d.nome_fantasia, ...emailRec }, linksWeb);
        if (registro.site.confirmado.length) falhas.push(`site no ar com o telefone dela: ${registro.site.confirmado.join(', ')}`);
        const temSite = registro.site.confirmado.length > 0;
        if (falhas.length && !melhor.forte && !temSite) {
          // Casamento fraco com problema: provavelmente não é ela. Volta pra fila de busca, sem reprovar.
          registro.veredito = 'sem_cnpj';
          registro.motivos = [`não confirmado: ${registro.receita.razao} é parecida, mas tem ${falhas.join(', ')}`];
          registro.cnpj = null; registro.casou_por = []; delete registro.receita;
        } else if (falhas.length) { registro.veredito = 'reprovado'; registro.motivos = falhas; }
        else {
          const duvidas = [];
          if (melhor.porAvaliacao) duvidas.push('firma no nome do dono, casada pelas avaliações: conferir');
          else if (!melhor.forte) duvidas.push(melhor.porNome ? 'casou só pelo nome, em outro endereço: confirmar se é a mesma empresa' : 'CNPJ casou só por telefone ou endereço: confirmar se é a mesma empresa');
          else if (melhor.porRegiao && !melhor.porTel) duvidas.push('nome igual, mas o CEP só bate no início: conferir o endereço');
          if (registro.site.possivel.length) duvidas.push(`domínio que parece dela: ${registro.site.possivel.join(', ')}`);
          if (CNAES.length && !CNAES.includes(String(d.cnae_fiscal)) && !(d.cnaes_secundarios || []).some(x => CNAES.includes(String(x.codigo)))) duvidas.push(`CNAE fora do ramo: ${r.cnae}`);
          registro.veredito = duvidas.length ? 'revisar' : 'aprovado';
          registro.motivos = duvidas;
        }
      }
    } else {
      registro.site = await checarSite(c, tokens, null, linksWeb);
      if (registro.site.confirmado.length) { registro.veredito = 'reprovado'; registro.motivos = [`site no ar com o telefone dela: ${registro.site.confirmado.join(', ')}`]; }
    }
    out.push(registro);
    console.log(`${registro.veredito.toUpperCase().padEnd(9)} ${c.title} | ${registro.cnpj || '-'} (${registro.casou_por.join('+')}) ${registro.motivos.join('; ')}`);
  }

  const conta = v => out.filter(x => x.veredito === v).length;
  const pendentes = out.filter(x => x.veredito === 'sem_cnpj');
  gravarJSON(outPath, { parametros: { cidade: opt.cidade, cnaes: CNAES, anos: ANOS, aviso_base: avisoBase }, etapas: entrada.etapas, doRamo: entrada.doRamo, comSite: entrada.comSite, resultados: out });
  console.log(`\nAprovados ${conta('aprovado')} · revisar ${conta('revisar')} · reprovados ${conta('reprovado')} · sem CNPJ ${conta('sem_cnpj')}`);
  if (pendentes.length && !opt['sem-receita']) {
    console.log('\nSem CNPJ. Buscar na web e registrar em buscas.json:');
    pendentes.forEach(p => console.log(`  "${p.title.replace(/\s*[|(].*$/, '')}" cnpj ${opt.cidade || ''}`));
  }
})().catch(e => { console.error(e.message); process.exitCode = 1; });
