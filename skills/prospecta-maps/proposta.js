// Índice: dados · checagens · seções · página · PDF
// Gera a proposta de um lead: uma página só (HTML com tudo embutido) e um PDF pra mandar no WhatsApp.
// Uso: node proposta.js <pasta-da-rodada> --lead <pasta, slug ou parte do nome> [--pdf 0]
// Lê rodada.json e o config.json da pasta acima. O bloco "proposta" do lead tem prioridade sobre os dois.
// Sai em <pasta-da-rodada>/propostas/, fora do git e fora da publicação das prévias.
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
const { args, lerJSON, esc, slug, norm, digits, acharChrome, pdfChrome } = require('./comum');

const opt = args();
const [rodada] = opt._;
if (!rodada || !opt.lead) { console.error('Uso: node proposta.js <pasta-da-rodada> --lead <pasta, slug ou parte do nome>'); process.exit(1); }
const rodadaPath = path.join(rodada, 'rodada.json');
if (!fs.existsSync(rodadaPath)) { console.error(`Não achei ${rodadaPath}. Monte o rodada.json antes (Passo 8).`); process.exit(1); }
const configPath = path.join(rodada, '..', 'config.json');
const cfg = { ...(fs.existsSync(configPath) ? lerJSON(configPath) : {}), ...lerJSON(rodadaPath) };

const entradas = Object.entries(cfg.leads || {});
const procura = norm(opt.lead);
const achados = entradas.filter(([k, L]) => k === opt.lead || L.slug === opt.lead || norm(L.empresa).includes(procura));
if (achados.length !== 1) {
  console.error(`${achados.length ? 'Mais de um lead' : 'Nenhum lead'} para "${opt.lead}". Leads da rodada: ${entradas.map(([, L]) => L.empresa).join(', ')}`);
  process.exit(1);
}
const [[pasta, L]] = achados;
const P = { ...cfg, ...(L.proposta || {}) };

const art = L.artigo === 'o' ? 'o' : 'a';
const trocas = {
  empresa: L.empresa, a: art, da: art === 'o' ? 'do' : 'da', na: art === 'o' ? 'no' : 'na', pra: art === 'o' ? 'pro' : 'pra',
  servico: L.servico || cfg.nicho || '', busca: L.busca || [cfg.nicho, cfg.cidade].filter(Boolean).join(' '), cidade: cfg.cidade || '',
  remetente: P.remetente, preco: P.preco, oferta: P.oferta
};
const t = s => String(s ?? '').replace(/\{(\w+)\}/g, (m, k) => trocas[k] ?? m);
const lista = v => (Array.isArray(v) ? v : v ? [v] : []);
const maiuscula = s => s.replace(/^./, c => c.toUpperCase());

const faltam = [];
for (const c of ['remetente', 'assinatura', 'oferta', 'preco', 'entrega', 'prazo']) if (!P[c]) faltam.push(`${c} (config.json)`);
for (const c of ['inclui', 'naoInclui', 'limites', 'pagamento']) if (!lista(P[c]).length) faltam.push(`${c} (config.json)`);
if (!lista(P.achados).length && !P.contexto) faltam.push(`achados ou contexto (bloco "proposta" de ${L.empresa} no rodada.json)`);
if (faltam.length) { console.error(`Faltou pra montar a proposta:\n- ${faltam.join('\n- ')}`); process.exit(1); }

const hoje = new Date();
const dataBR = d => d.toLocaleDateString('pt-BR');
const validade = new Date(hoje.getTime() + Number(P.validadeDias || 7) * 864e5);
const cor = /^#[0-9a-f]{6}$/i.test(P.cor || '') ? P.cor : '#1E3A5F';
const luz = [1, 3, 5].map(i => parseInt(cor.slice(i, i + 2), 16) / 255).map(c => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
const sobreCor = 0.2126 * luz[0] + 0.7152 * luz[1] + 0.0722 * luz[2] > 0.4 ? '#111111' : '#FFFFFF';
const corTexto = sobreCor === '#FFFFFF' ? cor : '#111111';

const dataUrl = arq => {
  if (!arq || !fs.existsSync(arq)) return null;
  const ext = path.extname(arq).slice(1).toLowerCase().replace('jpg', 'jpeg').replace('svg', 'svg+xml');
  return `data:image/${ext};base64,${fs.readFileSync(arq).toString('base64')}`;
};
const IMG_PREVIA = '__IMG_PREVIA__';
const IMG_LOGO = '__IMG_LOGO__';
const previaImg = cfg.semPrevia === true ? null : dataUrl(path.join(rodada, pasta, 'print-whatsapp.png'));
const logoImg = dataUrl(P.logo);
const base = /^https?:\/\//.test(cfg.base || '') ? cfg.base.replace(/\/?$/, '/') : '';
const linkPrevia = base && L.slug && cfg.semPrevia !== true ? `${base}${L.slug}/` : '';
const zap = digits(P.whatsapp).length >= 12
  ? `https://wa.me/${digits(P.whatsapp)}?text=${encodeURIComponent(t('Oi, {remetente}. Quero seguir com a proposta {da} {empresa}.'))}` : '';

// Seções: sem dado, a seção some.
const secaoCenario = () => {
  const nums = lista(P.achados);
  if (!nums.length && !P.contexto && !P.conversa) return '';
  return `<section class="bloco"><h2>O que vi ${esc(t('{na} {empresa}'))}</h2>
    ${nums.length ? `<div class="nums">${nums.map(n => { const [v, r] = Array.isArray(n) ? n : [n, '']; return `<div><b>${esc(t(v))}</b><span>${esc(t(r))}</span></div>`; }).join('')}</div>` : ''}
    ${P.contexto ? `<p>${esc(t(P.contexto))}</p>` : ''}
    ${P.conversa ? `<blockquote><span>O que você me contou</span>${esc(t(P.conversa))}</blockquote>` : ''}
  </section>`;
};
const secaoPrevia = () => {
  if (!previaImg) return '';
  return `<section class="bloco previa"><div><h2>A prévia do site</h2>
    <p>${esc(t(P.textoPrevia || 'Montei esta prévia com os dados públicos {da} {empresa}, pra você ver como poderia ficar antes de decidir qualquer coisa.'))}</p>
    ${linkPrevia ? `<p><a href="${esc(linkPrevia)}">Abrir a prévia no celular</a></p>` : ''}
    <p class="nota">Prévia não oficial. Ainda não está no ar, e os textos e as fotos são ajustados com você.</p></div>
    <img src="${IMG_PREVIA}" alt="Prévia do site ${esc(t('{da} {empresa}'))}"></section>`;
};
const secaoInclui = () => `<section class="bloco"><h2>O que entra</h2><ol class="itens">${lista(P.inclui).map(i => {
    const [titulo, det] = Array.isArray(i) ? i : [i];
    return `<li><b>${esc(t(titulo))}</b>${det ? `<span>${esc(t(det))}</span>` : ''}</li>`;
  }).join('')}</ol></section>`;
const secaoPrazo = () => {
  const passos = lista(P.passos);
  return `<section class="bloco"><h2>Prazo</h2><p class="prazo">${esc(t(P.prazo))}</p>
    ${passos.length ? `<ol class="passos">${passos.map(p => `<li>${esc(t(p))}</li>`).join('')}</ol>` : ''}</section>`;
};
const secaoInvestimento = () => `<section class="bloco invest"><h2>Investimento</h2>
    <div class="preco">${esc(t(P.preco))}</div>
    <p class="resumo">${esc(maiuscula(t(P.entrega)).replace(/\.?$/, '.'))}</p>
    <div class="formas">${lista(P.pagamento).map(f => {
      const [rot, val, det] = Array.isArray(f) ? f : ['', f, ''];
      return `<div>${rot ? `<span>${esc(t(rot))}</span>` : ''}<b>${esc(t(val))}</b>${det ? `<small>${esc(t(det))}</small>` : ''}</div>`;
    }).join('')}</div>
    ${P.conta ? `<p class="conta">${esc(t(P.conta))}</p>` : ''}
  </section>`;
const secaoCombinado = () => `<section class="bloco duas"><div><h2>O que não entra</h2><ul>${lista(P.naoInclui).map(x => `<li>${esc(t(x))}</li>`).join('')}</ul></div>
    <div><h2>O que não depende de mim</h2><ul>${lista(P.limites).map(x => `<li>${esc(t(x))}</li>`).join('')}</ul></div></section>`;
const secaoFim = () => `<section class="bloco fim"><h2>Próximo passo</h2>
    <p>${esc(t(P.proximoPasso || 'Se fizer sentido, é só me responder com um ok que eu te passo o que preciso pra começar. Se tiver dúvida ou algo precisar mudar, me fala que eu ajusto.'))}</p>
    ${zap ? `<p><a class="botao" href="${esc(zap)}">Quero seguir com a proposta</a></p>` : ''}
    <p class="nota">Proposta válida até ${dataBR(validade)}.</p></section>`;

const corpo = `<div class="pagina">
  <header>
    ${logoImg ? `<img class="logo" src="${IMG_LOGO}" alt="${esc(P.assinatura)}">` : `<strong>${esc(P.assinatura)}</strong>`}
    <span>Proposta · ${dataBR(hoje)}</span>
  </header>
  <div class="capa">
    <p class="olho">Proposta para ${esc(L.empresa)}</p>
    <h1>${esc(maiuscula(t(P.titulo || '{oferta}')))}</h1>
  </div>
  ${secaoCenario()}
  ${secaoPrevia()}
  ${secaoInclui()}
  ${secaoPrazo()}
  ${secaoInvestimento()}
  ${secaoCombinado()}
  ${secaoFim()}
  <footer>${esc(P.assinatura)}${P.documento ? ` · ${esc(P.documento)}` : ''}</footer>
</div>`;

// Checagens: a proposta vai pro cliente, então erro aqui para tudo.
const visivel = corpo.replace(/<[^>]+>/g, ' ');
if (/[—–]/.test(visivel)) { console.error('Tem travessão no texto da proposta: troque no rodada.json ou no config.json.'); process.exit(1); }
const sobra = visivel.match(/\{\{?\w+\}?\}/);
if (sobra) { console.error(`Campo não preenchido na proposta: ${sobra[0]}`); process.exit(1); }
const promessa = visivel.match(/(?<!não )(?<!sem )\b(garanto|garantimos|garantia de (resultado|clientes|vendas)|retorno garantido)\b|\b\d+\s*(clientes|vendas|leads)\s+(por|ao|no|na)\s+(m[eê]s|semana|dia)\b|\b(vai|v[aã]o|ir[aá]|ir[aã]o)\s+(vender|faturar|lotar|dobrar|triplicar)\b|\bROI\b/i);
if (promessa) { console.error(`Promessa de resultado na proposta: "${promessa[0]}". Reescreva sem número nem garantia de venda.`); process.exit(1); }

const html = `<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<title>Proposta para ${esc(L.empresa)}</title>
<style>
*{box-sizing:border-box;margin:0}
html{-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{background:#F3F4F6;color:#1F2933;font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.pagina{max-width:820px;margin:0 auto;background:#fff;padding:40px 48px}
header{display:flex;justify-content:space-between;align-items:center;gap:16px;padding-bottom:16px;border-bottom:1px solid #E4E7EB;font-size:14px;color:#52606D}
header strong{color:#111;font-size:16px}
.logo{max-height:40px;max-width:180px}
.capa{padding:36px 0 12px}
.olho{font-size:14px;font-weight:600;color:${corTexto};margin-bottom:8px}
h1{font-size:34px;line-height:1.15;color:#111;letter-spacing:-.01em;text-wrap:balance}
h2{font-size:20px;line-height:1.25;color:#111;margin-bottom:12px}
.bloco{padding:26px 0;border-bottom:1px solid #E4E7EB;break-inside:avoid}
.bloco p+p,.nums+p,.nums+blockquote,p+blockquote{margin-top:12px}
.nums{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px}
.nums div{background:#F7F8FA;border-radius:8px;padding:14px}
.nums b{display:block;font-size:26px;line-height:1.1;color:#111}
.nums span{font-size:14px;color:#52606D}
blockquote{border-left:3px solid ${cor};padding:2px 0 2px 14px;font-style:italic}
blockquote span{display:block;font-style:normal;font-size:13px;font-weight:600;color:#52606D;margin-bottom:2px}
.previa{display:grid;grid-template-columns:1fr 200px;gap:28px;align-items:start}
.previa img{width:100%;height:auto;border:1px solid #E4E7EB;border-radius:10px;display:block}
a{color:${corTexto};font-weight:600}
.nota{font-size:13px;color:#52606D}
.itens{list-style:none;padding:0;counter-reset:n;display:grid;gap:12px}
.itens li{counter-increment:n;display:grid;grid-template-columns:30px 1fr;column-gap:8px}
.itens li::before{content:counter(n);grid-row:span 2;width:26px;height:26px;border-radius:50%;background:${cor};color:${sobreCor};font-size:13px;font-weight:700;display:grid;place-items:center}
.itens b{color:#111;font-weight:600}
.itens span{grid-column:2;color:#52606D;font-size:15px}
.prazo{font-weight:600;color:#111}
.passos{margin-top:10px;padding-left:20px;color:#52606D;font-size:15px}
.preco{font-size:44px;font-weight:700;line-height:1.1;color:#111;letter-spacing:-.01em}
.resumo{margin-top:8px}
.formas{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin-top:16px}
.formas div{border:1px solid #E4E7EB;border-radius:8px;padding:12px 14px}
.formas span{display:block;font-size:13px;color:#52606D}
.formas b{display:block;color:#111}
.formas small{display:block;font-size:13px;color:#52606D}
.conta{margin-top:14px;background:#F7F8FA;border-radius:8px;padding:12px 14px;font-size:15px}
.duas{display:grid;grid-template-columns:1fr 1fr;gap:28px}
.duas h2{font-size:17px}
.duas ul{padding-left:18px;font-size:15px;color:#52606D}
.duas li+li{margin-top:6px}
.botao{display:inline-block;background:${cor};color:${sobreCor};padding:12px 20px;border-radius:8px;text-decoration:none;margin-top:12px}
.fim{border-bottom:0}
.fim .nota{margin-top:12px}
footer{padding-top:14px;border-top:1px solid #E4E7EB;font-size:13px;color:#52606D}
@media(max-width:640px){.pagina{padding:24px 20px}h1{font-size:27px}.previa,.duas{grid-template-columns:1fr}.previa img{max-width:280px}.preco{font-size:36px}}
@page{size:A4;margin:12mm}
@media print{body{background:#fff;font-size:14px}.pagina{max-width:none;padding:0}.capa{padding:22px 0 4px}h1{font-size:28px}h2{font-size:17px;margin-bottom:8px}.bloco{padding:15px 0}.previa{grid-template-columns:1fr 150px}.preco{font-size:34px}.nums b{font-size:22px}.nums div{padding:10px 12px}.itens{gap:8px}.itens span,.passos,.duas ul{font-size:13.5px}.formas{margin-top:10px}.botao{padding:9px 16px;margin-top:6px}}
</style></head>
<body>
${corpo.replace(IMG_PREVIA, () => previaImg || '').replace(IMG_LOGO, () => logoImg || '')}
</body></html>
`;

const saida = path.join(rodada, 'propostas');
fs.mkdirSync(saida, { recursive: true });
const nome = slug(L.slug || L.empresa);
const arqHtml = path.join(saida, `${nome}.html`);
fs.writeFileSync(arqHtml, html);

const arqPdf = path.join(saida, `${nome}.pdf`);
let pdfOk = false;
if (opt.pdf !== '0') {
  const chrome = acharChrome();
  pdfOk = chrome ? pdfChrome(chrome, pathToFileURL(path.resolve(arqHtml)).href, arqPdf) : false;
  if (!pdfOk) console.log(`Sem PDF${chrome ? ' (o navegador falhou)' : ' (não achei Chrome nem Edge)'}. Abra o HTML e use Imprimir > Salvar como PDF.`);
}
console.log(`ok: ${arqHtml}${pdfOk ? `\nok: ${arqPdf}` : ''}\nPreço: ${P.preco} · válida até ${dataBR(validade)}${previaImg ? ' · com a prévia' : ' · sem imagem da prévia'}`);
