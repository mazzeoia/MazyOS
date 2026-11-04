// Baixa as fotos das fichas (vêm na planilha do scraper) e monta uma folha pra escolher capa e galeria.
// Uso: node fotos.js <validados.json> <pasta-fotos> [--max 8] [--todas]
// Por padrão pega quem está como aprovado ou revisar. Cada empresa vira uma subpasta com foto1.jpg, foto2.jpg...
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { pathToFileURL } = require('url');
const { args, lerJSON, slug, esc, UA, acharChrome, printChrome } = require('./comum');

const opt = args();
const [entrada, pasta] = opt._;
if (!entrada || !pasta) { console.error('Uso: node fotos.js <validados.json> <pasta-fotos>'); process.exit(1); }
const MAX = Number(opt.max || 8);
const dados = lerJSON(entrada);
const lista = (dados.resultados || dados).filter(x => opt.todas || x.veredito === 'aprovado' || x.veredito === 'revisar');

// Pede a foto em tamanho bom. O sufixo depois do "=" define o tamanho nas URLs do Google.
const grande = u => /googleusercontent\.com/.test(u) ? u.replace(/=[^/=]*$/, '') + '=w1600-k-no' : u;

async function baixar(url) {
  try {
    const r = await fetch(url, { headers: UA, signal: AbortSignal.timeout(30000) });
    if (!r.ok || !/image/.test(r.headers.get('content-type') || '')) return null;
    return Buffer.from(await r.arrayBuffer());
  } catch { return null; }
}

(async () => {
  const blocos = [];
  for (const c of lista) {
    const chave = slug(c.title).slice(0, 40);
    const dir = path.join(pasta, chave);
    fs.mkdirSync(dir, { recursive: true });
    const urls = [...new Set([c.thumbnail, ...(c.images || [])].filter(Boolean).map(grande))].slice(0, MAX + 4);
    const hashes = new Set();
    let n = 0;
    const arquivos = [];
    for (const u of urls) {
      if (n >= MAX) break;
      const b = await baixar(u);
      if (!b || b.length < 8000) continue;
      const h = crypto.createHash('md5').update(b).digest('hex');
      if (hashes.has(h)) continue;
      hashes.add(h);
      n++;
      const nome = `foto${n}.jpg`;
      fs.writeFileSync(path.join(dir, nome), b);
      arquivos.push(nome);
    }
    console.log(`${String(n).padStart(2)} fotos  ${chave}`);
    blocos.push({ chave, titulo: c.title, arquivos });
  }

  const html = `<!doctype html><meta charset="utf-8"><style>
    body{margin:0;background:#fff;font:600 15px Arial,sans-serif;color:#000}
    .l{display:flex;gap:6px;padding:6px;border-bottom:2px solid #000;align-items:center}
    .n{width:150px;flex:none;font-size:13px}.f{position:relative;width:230px;height:165px;flex:none;background:#eee}
    .f img{width:100%;height:100%;object-fit:cover}.f b{position:absolute;left:4px;top:4px;background:#000;color:#ff0;padding:1px 5px;font-size:12px}
  </style>${blocos.map(b => `<div class="l"><div class="n">${esc(b.chave)}<br><small>${b.arquivos.length} fotos</small></div>${b.arquivos.slice(0, 8).map(a => `<div class="f"><img src="${esc(encodeURI(b.chave + '/' + a))}"><b>${a.replace('.jpg', '')}</b></div>`).join('')}</div>`).join('')}`;
  const folhaHtml = path.join(pasta, 'folha.html');
  fs.writeFileSync(folhaHtml, html);
  const chrome = acharChrome();
  const png = path.join(pasta, 'folha.png');
  const altura = Math.max(300, blocos.length * 180);
  if (chrome && printChrome(chrome, pathToFileURL(path.resolve(folhaHtml)).href, png, { largura: 2050, altura, espera: 8000 })) console.log(`Folha pra conferir: ${png}`);
  else console.log(`Sem navegador pra gerar a imagem. Abra ${folhaHtml} ou leia as fotos direto.`);
})();
