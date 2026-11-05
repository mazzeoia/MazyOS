// Funções usadas por todos os scripts da skill. Sem dependência externa: só Node 18+.
const fs = require('fs');
const os = require('os');
const path = require('path');

// Lê "--chave valor" e "--chave=valor". O resto vai em ._ (funciona igual no PowerShell e no bash).
function args(argv = process.argv.slice(2)) {
  const o = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--')) { o._.push(a); continue; }
    const igual = a.indexOf('=');
    if (igual > 0) { o[a.slice(2, igual)] = a.slice(igual + 1); continue; }
    const prox = argv[i + 1];
    if (prox === undefined || prox.startsWith('--')) o[a.slice(2)] = true;
    else { o[a.slice(2)] = prox; i++; }
  }
  return o;
}

const lerJSON = p => JSON.parse(fs.readFileSync(p, 'utf8').replace(/^﻿/, ''));
const gravarJSON = (p, v) => {
  fs.mkdirSync(path.dirname(path.resolve(p)), { recursive: true });
  fs.writeFileSync(p, JSON.stringify(v, null, 2));
};
const sleep = ms => new Promise(r => setTimeout(r, ms));
const digits = s => String(s || '').replace(/\D/g, '');
const norm = s => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
const slug = s => norm(s).replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const UA = { 'User-Agent': 'Mozilla/5.0 (mazyos-prospecta-maps)' };

// Celular BR: DDD + 9 + 8 dígitos. Fixo não recebe WhatsApp.
function telBR(fone) {
  let d = digits(fone);
  if (d.length >= 12 && d.startsWith('55')) d = d.slice(2);
  return d;
}
const ehCelular = fone => { const d = telBR(fone); return d.length === 11 && d[2] === '9'; };

// Chrome ou Edge em qualquer sistema. Retorna null se não houver nenhum.
function acharChrome() {
  const env = process.env;
  const lista = process.platform === 'win32'
    ? [env.PROGRAMFILES, env['PROGRAMFILES(X86)'], env.LOCALAPPDATA].filter(Boolean).flatMap(b => [
        path.join(b, 'Google', 'Chrome', 'Application', 'chrome.exe'),
        path.join(b, 'Microsoft', 'Edge', 'Application', 'msedge.exe')
      ])
    : process.platform === 'darwin'
    ? ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge', '/Applications/Chromium.app/Contents/MacOS/Chromium']
    : ['/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser', '/snap/bin/chromium', '/usr/bin/microsoft-edge'];
  return lista.find(p => fs.existsSync(p)) || null;
}

// Tira um print de uma URL ou arquivo. Pasta de perfil temporária pra não mexer no navegador da pessoa.
function printChrome(chrome, url, saida, { largura, altura, escala = 1, espera = 4000 }) {
  const { spawnSync } = require('child_process');
  const perfil = fs.mkdtempSync(path.join(os.tmpdir(), 'prospecta-'));
  const r = spawnSync(chrome, [
    '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run', '--no-default-browser-check',
    `--user-data-dir=${perfil}`, `--force-device-scale-factor=${escala}`, `--virtual-time-budget=${espera}`,
    `--window-size=${largura},${altura}`, `--screenshot=${path.resolve(saida)}`, url
  ], { timeout: 120000, stdio: 'ignore' });
  try { fs.rmSync(perfil, { recursive: true, force: true }); } catch {}
  return r.status === 0 && fs.existsSync(saida);
}

// Gera o PDF de uma página. Mesmo cuidado do print: perfil temporário, sem tocar no navegador da pessoa.
function pdfChrome(chrome, url, saida) {
  const { spawnSync } = require('child_process');
  const perfil = fs.mkdtempSync(path.join(os.tmpdir(), 'prospecta-'));
  try { fs.rmSync(saida, { force: true }); } catch {}
  spawnSync(chrome, [
    '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check', '--no-pdf-header-footer',
    `--user-data-dir=${perfil}`, '--virtual-time-budget=4000', `--print-to-pdf=${path.resolve(saida)}`, url
  ], { timeout: 120000, stdio: 'ignore' });
  try { fs.rmSync(perfil, { recursive: true, force: true }); } catch {}
  return fs.existsSync(saida) && fs.statSync(saida).size > 0;
}

module.exports = { args, lerJSON, gravarJSON, sleep, digits, norm, slug, esc, UA, telBR, ehCelular, acharChrome, printChrome, pdfChrome };
