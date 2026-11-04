// Sugere os CNAEs de um nicho a partir da lista oficial do IBGE (sem chave).
// Uso: node cnae.js "marcenaria" "moveis planejados"
const { args, norm, UA } = require('./comum');

const termos = args()._.map(norm).filter(Boolean);
if (!termos.length) { console.error('Uso: node cnae.js "nicho" ["outro termo"]'); process.exit(1); }

(async () => {
  const r = await fetch('https://servicodados.ibge.gov.br/api/v2/cnae/subclasses', { headers: UA });
  if (!r.ok) throw new Error(`IBGE respondeu ${r.status}`);
  const lista = await r.json();
  const raiz = p => p.length > 5 ? p.slice(0, -2) : p;
  const achados = lista.map(s => {
    const titulo = norm(s.descricao);
    const atividades = (s.atividades || []).map(norm).join(' | ');
    let pontos = 0;
    for (const termo of termos) {
      for (const palavra of termo.split(/\s+/).filter(p => p.length > 2)) {
        if (titulo.includes(raiz(palavra))) pontos += 3;
        else if (atividades.includes(raiz(palavra))) pontos += 1;
      }
    }
    return { id: s.id, descricao: s.descricao, pontos };
  }).filter(s => s.pontos).sort((a, b) => b.pontos - a.pontos).slice(0, 15);
  if (!achados.length) console.log('Nada encontrado. Tente um termo mais geral.');
  achados.forEach(s => console.log(`${s.id}  ${s.descricao}`));
})().catch(e => { console.error('Falhou:', e.message); process.exitCode = 1; });
