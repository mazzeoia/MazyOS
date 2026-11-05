// Índice: parseCSV · COLUNAS aceitas · padronizar · funil (etapa) · saída
// Lê uma ou mais planilhas de empresas, tira as duplicadas e aplica o funil.
// Aceita o CSV da API do scraper (colunas em inglês), o "Baixar planilha" do painel (em português, com ;)
// e planilhas de outras ferramentas, desde que tenham nome e telefone.
// Uso: node qualifica.js <a.csv> [b.csv ...] <saida.json> --ramo "marcenar|moveis" [--cidade "Curitiba"]
//      [--nota-min 4] [--min-aval 15] [--celular 0] [--sem-site 0] [--historico saidas/prospeccao/historico.json]
const fs = require('fs');
const { args, lerJSON, gravarJSON, norm, telBR, ehCelular } = require('./comum');

const opt = args();
const entradas = opt._.slice(0, -1);
const saida = opt._[opt._.length - 1];
if (!entradas.length) { console.error('Uso: node qualifica.js <planilha.csv> <saida.json> --ramo "regex"'); process.exit(1); }

const NOTA_MIN = Number(opt['nota-min'] ?? 4);
const MIN_AVAL = Number(opt['min-aval'] ?? 15);
const SO_CELULAR = opt.celular !== '0';
const SEM_SITE = opt['sem-site'] !== '0';
const RAMO = opt.ramo ? new RegExp(norm(opt.ramo), 'i') : null;
const CIDADE = opt.cidade ? norm(opt.cidade) : null;
const social = /instagram\.com|facebook\.com|fb\.com|linktr\.ee|wa\.me|whatsapp\.com|tiktok\.com|bio\.site|linkme|beacons\.ai|linkbio/i;

function parseCSV(texto) {
  const topo = texto.slice(0, texto.indexOf('\n') + 1);
  const sep = (topo.match(/;/g) || []).length > (topo.match(/,/g) || []).length ? ';' : ',';
  const linhas = [];
  let row = [], campo = '', q = false;
  for (let i = 0; i < texto.length; i++) {
    const c = texto[i];
    if (q) {
      if (c === '"') { if (texto[i + 1] === '"') { campo += '"'; i++; } else q = false; }
      else campo += c;
    } else if (c === '"') q = true;
    else if (c === sep) { row.push(campo); campo = ''; }
    else if (c === '\n') { row.push(campo); linhas.push(row); row = []; campo = ''; }
    else if (c !== '\r') campo += c;
  }
  if (campo || row.length) { row.push(campo); linhas.push(row); }
  const head = linhas.shift().map(h => norm(h).trim());
  return linhas.filter(r => r.length > 1).map(r => Object.fromEntries(head.map((h, i) => [h, r[i] || ''])));
}

// Nomes de coluna aceitos pra cada dado. Primeiro os do scraper, depois os mais comuns em outras ferramentas.
const COLUNAS = {
  title: ['title', 'empresa', 'nome', 'name', 'razao social', 'nome da empresa'],
  category: ['category', 'categoria', 'ramo', 'segmento', 'type'],
  phone: ['phone', 'telefone', 'whatsapp', 'celular', 'fone', 'phone_number', 'contato'],
  website: ['website', 'site', 'url do site', 'web'],
  rating: ['review_rating', 'nota', 'rating', 'avaliacao', 'stars'],
  reviews: ['review_count', 'avaliacoes', 'reviews', 'qtd avaliacoes', 'reviewscount'],
  address: ['address', 'endereco', 'full_address'],
  bairro: ['bairro', 'neighborhood'],
  cidade: ['cidade', 'city', 'municipio'],
  link: ['link', 'google maps', 'maps', 'url', 'googlemapsurl']
};
const pega = (p, chave) => { for (const c of COLUNAS[chave]) if (p[c]) return p[c]; return ''; };
const json = s => { try { return JSON.parse(s); } catch { return null; } };
const numero = s => Number(String(s).replace(',', '.')) || 0;

function padronizar(p) {
  const end = json(p.complete_address) || {};
  const address = pega(p, 'address');
  const cep = end.postal_code || (address.match(/\b\d{5}-?\d{3}\b/) || [''])[0];
  const dono = json(p.owner);
  return {
    title: pega(p, 'title').replace(/^[^\p{L}\p{N}]+/u, '').trim(), category: pega(p, 'category'), phone: pega(p, 'phone'), website: pega(p, 'website'),
    rating: numero(pega(p, 'rating')), reviews: numero(pega(p, 'reviews')), address,
    complete_address: { ...end, borough: end.borough || pega(p, 'bairro'), city: end.city || pega(p, 'cidade'), postal_code: cep },
    status: p.status || '', open_hours: json(p.open_hours), description: p.descriptions || '', about: json(p.about),
    dono: dono && (dono.name || dono.Name) || '', thumbnail: p.thumbnail || '',
    images: (json(p.images) || []).map(i => i.image).filter(Boolean),
    user_reviews: (json(p.user_reviews) || []).map(r => ({ name: r.Name, rating: r.Rating, text: r.Description, when: r.When })),
    link: pega(p, 'link'), lat: numero(p.latitude), lon: numero(p.longitude), place_id: p.place_id || p.cid || ''
  };
}

for (const a of entradas) if (!fs.existsSync(a)) { console.error(`Planilha não encontrada: ${a}`); process.exit(1); }
const todas = entradas.flatMap(a => parseCSV(fs.readFileSync(a, 'utf8').replace(/^﻿/, ''))).map(padronizar).filter(p => p.title);
if (!todas.length) { console.error('Não achei nenhuma empresa. A planilha precisa de uma coluna com o nome da empresa.'); process.exit(1); }

const vistos = new Set();
const unicas = todas.filter(p => {
  const k = p.place_id || norm(p.title) + telBR(p.phone);
  if (vistos.has(k)) return false;
  vistos.add(k);
  return true;
});

const historico = opt.historico && fs.existsSync(opt.historico) ? lerJSON(opt.historico) : {};
const doRamo = p => !RAMO || RAMO.test(norm(p.category + ' ' + p.title));
const temSite = p => p.website && !social.test(p.website);

const etapas = [['Encontradas (sem duplicadas)', unicas.length]];
let lista = unicas;
const etapa = (nome, fn) => { lista = lista.filter(fn); etapas.push([nome, lista.length]); };

if (RAMO) etapa('Do ramo', doRamo);
etapa('Abertas', p => !/fechad|closed/i.test(p.status));
etapa('Sem "filial" no nome', p => !/\bfilial\b/i.test(norm(p.title)));
if (lista.some(p => p.rating)) {
  etapa(`Nota acima de ${String(NOTA_MIN).replace('.', ',')}`, p => p.rating > NOTA_MIN);
  etapa(`${MIN_AVAL} ou mais avaliações`, p => p.reviews >= MIN_AVAL);
}
if (SEM_SITE) etapa('Sem site na ficha (vazio ou só rede social)', p => !temSite(p));
if (SO_CELULAR) etapa('Com celular na ficha (WhatsApp)', p => ehCelular(p.phone));
if (CIDADE) etapa(`Em ${opt.cidade}`, p => {
  const c = norm(p.complete_address.city);
  return c ? c.includes(CIDADE) || CIDADE.includes(c) : norm(p.address).includes(CIDADE);
});
if (Object.keys(historico).length) etapa('Ainda não abordadas em outra rodada', p => !historico[telBR(p.phone)]);

const ramoTotal = unicas.filter(doRamo).length;
const comSite = unicas.filter(p => doRamo(p) && temSite(p)).length;
const candidatos = lista
  .sort((a, b) => b.reviews - a.reviews)
  .map(p => ({ ...p, celular: ehCelular(p.phone), so_rede_social: Boolean(p.website) }));

gravarJSON(saida, { etapas, doRamo: ramoTotal, comSite, candidatos });
etapas.forEach(([n, c]) => console.log(String(c).padStart(5), n));
console.log(`\nDo ramo com site próprio: ${comSite} de ${ramoTotal}`);
candidatos.slice(0, 80).forEach(p => console.log(`${p.rating.toFixed(1)} (${p.reviews})  ${p.title} | ${p.category} | ${p.phone} | ${p.website || '-'} | ${p.complete_address.borough || ''}`));
if (candidatos.length > 80) console.log(`... e mais ${candidatos.length - 80} em ${saida}`);
