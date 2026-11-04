// Índice: acharInstalado · instalar · abrir · geocodificar · buscar
// Instala, abre e usa o MazyOS Scraper pela API, no Windows, no Mac e no Linux.
// Uso:
//   node scraper.js abrir [--porta 8080] [--pasta <onde está instalado>]
//   node scraper.js buscar --nicho "marcenaria" --cidade "Curitiba" --bairros "Batel,Centro" --saida final.csv
//                          [--raio 20000] [--lat -25.4 --lon -49.2] [--porta 8080]
// O scraper fica em ~/mazyos-scraper, fora do projeto, pra um executável de 60 MB não subir no /salvar.
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn, spawnSync } = require('child_process');
const { args, sleep, UA } = require('./comum');

const opt = args();
const comando = opt._[0];
const PORTA = opt.porta || 8080;
const API = `http://localhost:${PORTA}/api/v1/jobs`;
const REPO = 'https://github.com/mazzeoia/mazyos-scraper.git';
const ehWin = process.platform === 'win32';
const EXE = ehWin ? 'mazyos-scraper.exe' : 'mazyos-scraper';

const noAr = async () => {
  try { return (await fetch(API, { signal: AbortSignal.timeout(3000) })).ok; } catch { return false; }
};

function acharInstalado() {
  const lugares = [opt.pasta, process.env.MAZYOS_SCRAPER, path.join(os.homedir(), 'mazyos-scraper'),
    path.join(process.cwd(), 'ferramentas', 'mazyos-scraper'), path.join(process.cwd(), 'ferramentas', 'google-maps-scraper')].filter(Boolean);
  return lugares.find(d => fs.existsSync(path.join(d, EXE))) || null;
}

function instalar() {
  const destino = opt.pasta || path.join(os.homedir(), 'mazyos-scraper');
  if (!fs.existsSync(destino)) {
    console.log(`Baixando o MazyOS Scraper em ${destino}...`);
    const g = spawnSync('git', ['-c', 'core.longpaths=true', 'clone', '--depth', '1', REPO, destino], { stdio: 'inherit' });
    if (g.status !== 0) throw new Error('Não consegui baixar. Confira se o git está instalado: https://git-scm.com');
  }
  console.log('Instalando (na primeira vez pode levar alguns minutos)...');
  const r = ehWin
    ? spawnSync('powershell', ['-ExecutionPolicy', 'Bypass', '-File', 'instalar.ps1'], { cwd: destino, stdio: 'inherit' })
    : spawnSync('bash', ['instalar.sh'], { cwd: destino, stdio: 'inherit' });
  if (r.status !== 0 || !fs.existsSync(path.join(destino, EXE))) {
    throw new Error(`A instalação não terminou. Veja o CLAUDE.md em ${destino}. Sem o scraper, dá pra seguir com qualquer planilha de empresas (Passo 3).`);
  }
  return destino;
}

async function abrir() {
  if (await noAr()) { console.log(`MazyOS Scraper já está no ar em http://localhost:${PORTA}`); return; }
  const dir = acharInstalado() || instalar();
  if (await noAr()) { console.log(`MazyOS Scraper no ar em http://localhost:${PORTA}`); return; }
  const filho = spawn(path.join(dir, EXE), ['-web', '-addr', `:${PORTA}`, '-c', '4', '-data-folder', 'webdata'], {
    cwd: dir, detached: true, stdio: 'ignore', windowsHide: true, env: { ...process.env, DISABLE_TELEMETRY: '1' }
  });
  filho.on('error', e => { console.error('Não consegui abrir o scraper:', e.message); process.exitCode = 1; });
  filho.unref();
  for (let i = 0; i < 40; i++) {
    await sleep(1500);
    if (await noAr()) { console.log(`MazyOS Scraper no ar em http://localhost:${PORTA}`); return; }
  }
  throw new Error(`O scraper não respondeu na porta ${PORTA}. Se ela estiver ocupada, rode de novo com --porta 8090.`);
}

async function geocodificar(cidade) {
  const r = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(cidade)}&format=json&limit=1`, { headers: UA });
  const j = await r.json();
  if (!j[0]) throw new Error(`Não achei "${cidade}" no mapa. Passe --lat e --lon.`);
  return { lat: j[0].lat, lon: j[0].lon };
}

async function buscar() {
  const { nicho, cidade, saida } = opt;
  if (!nicho || !cidade || !saida) throw new Error('Faltou --nicho, --cidade ou --saida.');
  await abrir();
  const bairros = String(opt.bairros === true ? '' : opt.bairros || '').split(',').map(s => s.trim()).filter(Boolean);
  const nichos = String(nicho).split(',').map(s => s.trim()).filter(Boolean);
  const keywords = nichos.flatMap(n => [`${n} em ${cidade}`, ...bairros.map(b => `${n} em ${b}, ${cidade}`)]);
  const { lat, lon } = opt.lat ? { lat: String(opt.lat), lon: String(opt.lon) } : await geocodificar(cidade);
  const corpo = {
    name: `${nichos.join(' + ')} · ${cidade}`, keywords, lang: 'pt', zoom: 12, lat, lon,
    radius: Number(opt.raio || 20000), depth: 6, email: false, max_time: Math.max(900, keywords.length * 240)
  };
  const r = await fetch(API, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corpo) });
  if (!r.ok) throw new Error(`O scraper recusou a busca (${r.status}): ${await r.text()}`);
  const { id } = await r.json();
  console.log(`Busca ${id}: ${keywords.length} termos. Dá pra acompanhar em http://localhost:${PORTA}`);

  const inicio = Date.now();
  const limite = (corpo.max_time + 300) * 1000;
  let status = '';
  while (Date.now() - inicio < limite) {
    await sleep(15000);
    const j = await (await fetch(`${API}/${id}`)).json();
    status = String(j.Status || j.status || '').toLowerCase();
    if (status === 'ok') break;
    if (status === 'failed') throw new Error('A busca falhou no scraper. Veja a tela dele. Bloqueio do Google: esperar algumas horas e reduzir o volume.');
  }
  if (status !== 'ok') console.log(`A busca passou do tempo (status "${status}"). Tentando baixar o que já veio.`);

  const dl = await fetch(`${API}/${id}/download`);
  if (!dl.ok) throw new Error(`Não consegui baixar o resultado (${dl.status}).`);
  const texto = await dl.text();
  fs.mkdirSync(path.dirname(path.resolve(saida)), { recursive: true });
  fs.writeFileSync(saida, texto);
  console.log(`${texto.split('\n').length - 2} linhas em ${saida} (${Math.round((Date.now() - inicio) / 60000)} min)`);
}

(comando === 'abrir' ? abrir() : comando === 'buscar' ? buscar() : Promise.reject(new Error('Comandos: abrir | buscar')))
  .catch(e => { console.error(e.message); process.exitCode = 1; });
