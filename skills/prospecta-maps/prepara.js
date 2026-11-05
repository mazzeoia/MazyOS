// Confere o ambiente antes da rodada e diz o que falta, em vez de quebrar no meio.
// Uso: node prepara.js [--porta 8080]
// Também protege os leads: cria saidas/prospeccao/.gitignore pra telefone de terceiro não subir no /mazyos:salvar.
const fs = require('fs');
const path = require('path');
const { args, lerJSON, acharChrome, UA } = require('./comum');

const opt = args();
const PORTA = opt.porta || 8080;
const raiz = process.cwd();
const pasta = path.join(raiz, 'saidas', 'prospeccao');

const responde = async (url, ms = 8000) => {
  try { return (await fetch(url, { headers: UA, signal: AbortSignal.timeout(ms) })).ok; } catch { return false; }
};

function acharCofre(dir, nivel = 0) {
  if (nivel > 5) return null;
  let itens;
  try { itens = fs.readdirSync(dir, { withFileTypes: true }); } catch { return null; }
  for (const i of itens) {
    if (i.isDirectory() && /cola-direto-cofre|cofre-de-abordagens/i.test(i.name)) return path.join(dir, i.name);
  }
  for (const i of itens) {
    if (!i.isDirectory() || /^(\.git|node_modules|saidas)$/.test(i.name)) continue;
    const r = acharCofre(path.join(dir, i.name), nivel + 1);
    if (r) return r;
  }
  return null;
}

(async () => {
  fs.mkdirSync(pasta, { recursive: true });
  const ignora = path.join(pasta, '.gitignore');
  if (!fs.existsSync(ignora)) fs.writeFileSync(ignora, '# Leads têm telefone de terceiros: ficam só nesta máquina.\n*\n!.gitignore\n');

  const versao = Number(process.versions.node.split('.')[0]);
  const chrome = acharChrome();
  const scraper = await responde(`http://localhost:${PORTA}/api/v1/jobs`, 3000);
  const receita = await responde('https://minhareceita.org/33000167000101');
  const reserva = receita || await responde('https://brasilapi.com.br/api/cnpj/v1/33000167000101');
  const configPath = path.join(pasta, 'config.json');
  const config = fs.existsSync(configPath) ? lerJSON(configPath) : null;
  const memoria = path.join(raiz, '_memoria', 'empresa.md');
  const memoriaOk = fs.existsSync(memoria) && /\*\*Nome:\*\*[ \t]*\S/.test(fs.readFileSync(memoria, 'utf8'));
  const cofre = acharCofre(raiz);

  const linha = (ok, nome, det) => console.log(`${ok ? 'ok  ' : 'FALTA'} ${nome}${det ? ': ' + det : ''}`);
  linha(versao >= 18, 'Node', `v${process.versions.node}${versao < 18 ? ' (precisa do 18 ou mais novo)' : ''}`);
  linha(scraper, 'MazyOS Scraper', scraper ? `no ar na porta ${PORTA}` : 'desligado ou não instalado. Rode: node scraper.js abrir');
  linha(reserva, 'Base da Receita', receita ? 'Minha Receita respondendo' : reserva ? 'só a BrasilAPI respondeu (consulta por CNPJ funciona, a busca por ramo não)' : 'fora do ar agora');
  linha(!!chrome, 'Chrome ou Edge', chrome || 'não achei: a rodada sai sem os prints. Instale o Chrome pra ter a imagem da prévia');
  linha(!!config, 'Seus dados da oferta', config ? `${config.remetente} · ${config.oferta} · ${config.preco}` : 'ainda não: pegar em _memoria/empresa.md ou perguntar uma vez e salvar em saidas/prospeccao/config.json');
  console.log(`info  Memória do negócio: ${memoriaOk ? 'preenchida' : 'vazia (dá pra seguir, mas rode /mazyos:instalar depois)'}`);
  console.log(`info  Cofre de Abordagens: ${cofre ? 'achei em ' + path.relative(raiz, cofre) : 'não está neste projeto (usa as mensagens base da skill)'}`);
  console.log(`info  Pasta das rodadas: ${path.relative(raiz, pasta)} (fora do git)`);
  console.log(`info  Sistema: ${process.platform}`);
  if (versao < 18) process.exit(1);
})();
