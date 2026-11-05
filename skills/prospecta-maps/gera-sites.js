// Índice: cortaEntre/trocaBloco · serviços e grade · galeria · como funciona · avaliações · capa · números · contato fixo · campos do modelo · checagens e cópia das fotos
// Gera um site de prévia por lead a partir de modelo-demo.html.
// Uso: node gera-sites.js <leads.json> <pasta-da-rodada> <pasta-fotos> --assinatura "Seu nome ou empresa"
// Campos de cada lead: ver exemplo-leads.json. Falha se sobrar {{CAMPO}} ou aparecer travessão.
const fs = require('fs');
const path = require('path');
const { args, lerJSON, esc } = require('./comum');

const opt = args();
const [leadsPath, outDir, fotosDir] = opt._;
if (!leadsPath || !outDir) { console.error('Uso: node gera-sites.js <leads.json> <pasta-da-rodada> <pasta-fotos> --assinatura "Nome"'); process.exit(1); }
if (!opt.assinatura) { console.error('Faltou --assinatura (seu nome ou empresa, aparece no rodapé da prévia).'); process.exit(1); }
const leads = lerJSON(leadsPath).filter(L => L.slug);
const modelo = fs.readFileSync(path.join(__dirname, 'modelo-demo.html'), 'utf8').replace(/\r\n/g, '\n');

function cortaEntre(html, inicio, fim) {
  const a = html.indexOf(inicio);
  const b = html.indexOf(fim, a);
  if (a < 0 || b < 0) throw new Error('marcador não achado: ' + inicio);
  return html.slice(0, a) + html.slice(b);
}

function trocaBloco(html, re, blocos) {
  const m = html.match(re);
  if (!m) throw new Error('bloco não achado: ' + re);
  return html.replace(m[0], () => blocos.join('\n      '));
}

for (const L of leads) {
  let h = modelo.replace(/<!--\s*\n  Modelo do site[\s\S]*?-->\n/, '');
  const fixo = !L.whatsapp;
  const linkContato = fixo
    ? `tel:+55${L.telefoneDigitos}`
    : `https://wa.me/${L.whatsapp}?text=${encodeURIComponent(L.msgWhats || '')}`;
  const servicos = L.servicos || [];
  const fotos = L.fotos || [];
  const passos = L.passos || [];
  const avaliacoes = L.avaliacoes || [];
  const numeros = L.numeros || [];

  // Serviços
  h = trocaBloco(h, /<!-- REPETIR por serviço[\s\S]*?<\/article>/, servicos.map((s, i) =>
    `<article class="servico${i === 0 ? ' destaque' : ''} revela">
        <div class="icone"><svg><use href="#${esc(s.icone || 'i-check')}"/></svg></div>
        <h3>${esc(s.titulo)}</h3>
        <p>${esc(s.desc)}</p>
      </article>`));
  const gradeServ = {
    3: '', 6: '',
    4: '    .servicos-grade { grid-template-columns: repeat(6, 1fr); }\n    .servico { grid-column: span 3; }\n',
    5: null
  }[servicos.length];
  if (gradeServ !== null && gradeServ !== undefined) {
    h = h.replace(/    \/\* 5 serviços[\s\S]*?\.servico:nth-child\(-n\+2\) \{ grid-column: span 3; \}\n/, () => gradeServ);
  }

  // Galeria
  if (fotos.length >= 3) {
    h = trocaBloco(h, /<!-- REPETIR 3 vezes \(fotos[\s\S]*?<\/figure>/, fotos.slice(0, 3).map(f =>
      `<figure class="foto revela"><img src="${esc(f.src)}" alt="${esc(f.alt)}"><figcaption>${esc(f.legenda)}<small>${esc(f.categoria)}</small></figcaption></figure>`));
  } else {
    h = cortaEntre(h, '<section class="trabalhos"', '<!-- COMO FUNCIONA');
    h = h.replace('<a href="#trabalhos">Trabalhos</a>', '');
  }

  // Como funciona (seção some se não houver passo real)
  if (passos.length) {
    h = trocaBloco(h, /<!-- REPETIR 3 vezes -->\s*<div class="passo[\s\S]*?<\/div>/, passos.map(p =>
      `<div class="passo revela"><h3>${esc(p[0])}</h3><p>${esc(p[1])}</p></div>`));
  } else {
    h = cortaEntre(h, '<!-- COMO FUNCIONA', '<!-- AVALIAÇÕES');
    h = h.replace(/<a href="#como[^"]*">[^<]*<\/a>/, '');
  }

  // Avaliações (só texto real)
  if (avaliacoes.length) {
    h = trocaBloco(h, /<!-- REPETIR 3 ou 4 vezes -->\s*<div class="aval[^\n]*/, avaliacoes.map(a =>
      `<div class="aval revela"><div class="estrelas">★★★★★</div><p>"${esc(a.texto)}"</p><div class="aval-autor"><span class="avatar">${esc(a.autor[0])}</span><div>${esc(a.autor)}<small>Google</small></div><svg class="g"><use href="#i-google"/></svg></div></div>`));
  } else {
    h = cortaEntre(h, '<!-- AVALIAÇÕES', '<section class="final"');
    h = h.replace('<a href="#avaliacoes">Avaliações</a>', '');
  }

  // Sem foto boa de capa: topo só com o fundo da marca
  if (!L.fotoHero) {
    h = h.replace(/\s*<div class="hero-foto"[^>]*><\/div>/, '');
    h = h.replace('.hero::after {', '.hero::before { content: \'\'; position: absolute; inset: 0; background: radial-gradient(ellipse at 80% 20%, color-mix(in srgb, var(--marca) 22%, transparent), transparent 60%); }\n  .hero::after { display:none;');
    L.fotoHero = '';
  }

  // Números: bloco sem dado sai, em vez de aparecer vazio
  numeros.forEach((nm, i) => {
    h = h.replace(`{{NUMERO_${i + 1}}}`, () => esc(nm[0])).replace(`{{LEGENDA_${i + 1}}}`, () => esc(nm[1]));
  });
  h = h.replace(/\s*<div class="numero"><strong>\{\{NUMERO_\d\}\}<\/strong><span>\{\{LEGENDA_\d\}\}<\/span><\/div>/g, '');

  // Contato: telefone fixo vira ligação
  if (fixo) {
    h = h.split('href="https://wa.me/{{WHATSAPP_DIGITOS}}?text={{MENSAGEM_WHATS_URLENCODED}}"><svg class="ic"><use href="#i-whats"/>')
      .join(`href="${linkContato}"><svg class="ic"><use href="#i-tel"/>`);
    h = h.replace(/<a class="whats"[\s\S]*?<\/a>/, () => `<a class="whats" style="background:var(--marca);color:var(--marca-texto);box-shadow:none" aria-label="Ligar" href="${linkContato}"><svg><use href="#i-tel"/></svg></a>`);
    h = h.replace('.whats::after {', '.whats::after { display:none;');
  }

  const endereco = L.endereco || ['', ''];
  const campos = {
    NOME_EMPRESA: L.nome, O_QUE_FAZ: L.oQueFaz, CIDADE: L.cidade, DESCRICAO_160: L.descricao,
    FONTE_CORPO_URL: (L.fonteCorpo || 'Barlow').replace(/ /g, '+'), FONTE_TITULO_URL: (L.fonteTitulo || 'Barlow Condensed').replace(/ /g, '+'),
    FONTE_CORPO: L.fonteCorpo || 'Barlow', FONTE_TITULO: L.fonteTitulo || 'Barlow Condensed',
    COR_MARCA: L.cor[0], COR_MARCA_ESCURA: L.cor[1], COR_SOBRE_MARCA: L.cor[2],
    COR_FUNDO: '#121417', COR_FUNDO_2: '#181B1F', COR_CARD: '#1C2024', COR_LINHA: 'rgba(255,255,255,.08)',
    COR_TEXTO: '#F2F3F5', COR_TEXTO_SUAVE: '#A3A9B2',
    INICIAL: L.inicial || L.nomeCurto[0], NOME_CURTO: L.nomeCurto, TAGLINE_CURTA: L.tagline,
    WHATSAPP_DIGITOS: L.whatsapp || '', MENSAGEM_WHATS_URLENCODED: encodeURIComponent(L.msgWhats || ''),
    CTA_CURTO: fixo ? 'Ligar' : (L.ctaCurto || 'WhatsApp'), CTA: fixo ? 'Ligar agora' : (L.cta || 'Chamar no WhatsApp'),
    FOTO_HERO: L.fotoHero, ALT_FOTO_HERO: L.altHero || L.nome,
    NOTA: L.nota, N_AVALIACOES: L.nAvaliacoes,
    PROMESSA_INICIO: L.promessa[0], PROMESSA_DESTAQUE: L.promessa[1], SUBTITULO: L.subtitulo,
    TITULO_SERVICOS: L.tituloServicos, SUB_SERVICOS: L.subServicos,
    ROTULO_GALERIA: L.rotuloGaleria || 'Fotos', TITULO_GALERIA: L.tituloGaleria || '', SUB_GALERIA: L.subGaleria || '',
    TITULO_COMO: L.tituloComo || 'Como funciona',
    TITULO_AVALIACOES: L.tituloAvaliacoes || 'Quem já é cliente',
    TITULO_FINAL: L.tituloFinal, SUB_FINAL: L.subFinal,
    ENDERECO_URLENCODED: encodeURIComponent(L.enderecoBusca || ''),
    ENDERECO_LINHA_1: endereco[0], ENDERECO_LINHA_2: endereco[1],
    HORARIO: L.horario || 'Consulte o horário no WhatsApp', TELEFONE_FORMATADO: L.telefone,
    RAZAO_OU_NOME: L.razao || L.nome, CNPJ_OU_INSTAGRAM: L.cnpj ? 'CNPJ ' + L.cnpj : L.cidade,
    ASSINATURA: opt.assinatura
  };
  // Campos de texto passam por escape; URLs e cores entram cruas.
  const crus = new Set(['FONTE_CORPO_URL', 'FONTE_TITULO_URL', 'COR_MARCA', 'COR_MARCA_ESCURA', 'COR_SOBRE_MARCA', 'COR_FUNDO', 'COR_FUNDO_2', 'COR_CARD', 'COR_LINHA', 'COR_TEXTO', 'COR_TEXTO_SUAVE', 'WHATSAPP_DIGITOS', 'MENSAGEM_WHATS_URLENCODED', 'ENDERECO_URLENCODED', 'FOTO_HERO']);
  for (const [k, v] of Object.entries(campos)) {
    if (v === undefined || v === null) continue;
    h = h.split(`{{${k}}}`).join(crus.has(k) ? v : esc(v));
  }

  const sobrou = h.match(/\{\{[A-Z_0-9]+\}\}/g);
  if (sobrou) throw new Error(`${L.slug}: campos sem preencher: ${[...new Set(sobrou)].join(', ')}`);
  if (/[—–]/.test(h)) throw new Error(`${L.slug}: travessão no texto`);

  const dir = path.join(outDir, L.slug);
  fs.mkdirSync(path.join(dir, 'img'), { recursive: true });
  fs.writeFileSync(path.join(dir, 'index.html'), h);
  for (const [destino, origem] of Object.entries(L.copias || {})) {
    const foto = path.join(fotosDir, origem);
    if (!fs.existsSync(foto)) throw new Error(`${L.slug}: foto não encontrada: ${origem}. Confira as copias no leads.json.`);
    fs.copyFileSync(foto, path.join(dir, destino));
  }
  console.log('ok', L.slug);
}
