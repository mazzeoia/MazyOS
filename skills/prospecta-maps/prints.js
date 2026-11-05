// Tira os prints de cada site da rodada, em qualquer sistema, com o Chrome ou o Edge da máquina.
// Uso: node prints.js <pasta-da-rodada>
// Gera print-desktop.png, print-celular.png e print-whatsapp.png (o topo do site, a imagem que vai pro lead).
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
const { args, acharChrome, printChrome } = require('./comum');

const [rodada] = args()._;
if (!rodada) { console.error('Uso: node prints.js <pasta-da-rodada>'); process.exit(1); }
const chrome = acharChrome();
if (!chrome) {
  console.log('Sem Chrome nem Edge: a rodada segue sem prints. Instale o Chrome e rode de novo pra ter a imagem da prévia.');
  process.exit(0);
}
const pastas = fs.readdirSync(rodada, { withFileTypes: true })
  .filter(d => d.isDirectory() && d.name !== 'previa' && !d.name.startsWith('.') && fs.existsSync(path.join(rodada, d.name, 'index.html')))
  .map(d => d.name);

let falhas = 0;
for (const p of pastas) {
  const dir = path.join(rodada, p);
  const url = pathToFileURL(path.resolve(dir, 'index.html')).href;
  // Janela de 500 é proposital: abaixo disso o modo headless corta a lateral.
  const ok = [
    printChrome(chrome, url, path.join(dir, 'print-celular.png'), { largura: 500, altura: 5000 }),
    printChrome(chrome, url, path.join(dir, 'print-desktop.png'), { largura: 1366, altura: 4700 }),
    printChrome(chrome, url, path.join(dir, 'print-whatsapp.png'), { largura: 500, altura: 1083, escala: 2 })
  ].every(Boolean);
  if (!ok) falhas++;
  console.log(`${ok ? 'ok   ' : 'FALHA'} ${p}`);
}
if (falhas) { console.error(`${falhas} site(s) sem print completo.`); process.exit(1); }
