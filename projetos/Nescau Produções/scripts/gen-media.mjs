/* ============================================================================
   Gerador das placas visuais (public/media/*.svg)
   ----------------------------------------------------------------------------
   O site precisa de imagem grande em quase toda dobra, e ainda não existe uma
   única foto real de show da Nescau em disco. Em vez de deixar <img> quebrado
   ou puxar banco de imagem genérico, cada slot recebe uma placa desenhada:
   abstração de luz de palco (facho, névoa, bokeh, silhueta) na paleta da
   marca. É deliberadamente abstrata — parece direção de arte, não
   "placeholder".

   Só gradiente e forma, zero filtro SVG: filtro de blur em área grande custa
   caro no compositor e derrubaria o alvo de 60 FPS com várias placas na tela.
   A borda suave vem de stop de gradiente.

   Rodar: node scripts/gen-media.mjs
   Trocar por foto real: salvar o arquivo com o MESMO nome (.webp/.jpg) em
   public/media/ e ajustar a extensão em src/lib/media.ts.
   ========================================================================== */

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const OUT = join(dirname(fileURLToPath(import.meta.url)), "..", "site", "astro-site", "public", "media");
mkdirSync(OUT, { recursive: true });

/* --- PRNG com semente: mesma entrada, mesma placa em todo build ----------- */
function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a += 0x6d2b79f5;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const PALETTE = {
  amber: "#ffc531",
  amberHi: "#ffe07a",
  flame: "#ff7a18",
  ember: "#ff3b1f",
  cool: "#7c5cff", // contraluz roxo — usado com muita parcimônia, só pra dar
  // separação entre planos; sem ele tudo vira uma mancha laranja só.
};

const r2 = (n) => Math.round(n * 100) / 100;

/* --- Peças ---------------------------------------------------------------- */

/* Facho volumétrico.
   Cada facho é composto de três polígonos concêntricos — halo largo quase
   invisível, corpo médio, núcleo estreito e claro. Essa é a queda lateral de
   luz que um polígono só, de opacidade única, nunca dá (vira triângulo
   chapado). O grupo inteiro entra em `screen`: luz que se cruza soma e
   clareia, em vez de virar aquele marrom de sobreposição alfa. */
function beams(rand, w, h, opts = {}) {
  const count = opts.count ?? 7;
  const originY = opts.originY ?? -h * 0.06;
  const spread = opts.spread ?? 1;
  let defs = "";
  let body = "";

  for (let i = 0; i < count; i++) {
    const ox = w * (0.06 + rand() * 0.88);
    const angle = (rand() - 0.5) * 1.1 * spread;
    const len = h * (0.9 + rand() * 0.45);
    const baseTop = w * (0.003 + rand() * 0.006);
    const baseBot = w * (0.03 + rand() * 0.075) * spread;
    const pick = rand();
    const color =
      pick > 0.93 ? PALETTE.cool : pick > 0.66 ? PALETTE.amberHi : pick > 0.34 ? PALETTE.amber : PALETTE.flame;
    const strength = 0.05 + rand() * 0.07;
    const bx = ox + Math.tan(angle) * len;

    // halo → corpo → núcleo
    const layers = [
      [2.9, strength * 0.34],
      [1.5, strength * 0.72],
      [0.55, strength * 1.5],
    ];

    layers.forEach(([mul, op], li) => {
      const id = `bm${opts.key}${i}_${li}`;
      const tw = baseTop * mul;
      const bw = baseBot * mul;
      const pts = [
        [r2(ox - tw), r2(originY)],
        [r2(ox + tw), r2(originY)],
        [r2(bx + bw), r2(originY + len)],
        [r2(bx - bw), r2(originY + len)],
      ]
        .map((p) => p.join(","))
        .join(" ");

      defs += `<linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="${color}" stop-opacity="${r2(op * 1.35)}"/>
        <stop offset=".35" stop-color="${color}" stop-opacity="${r2(op * 0.7)}"/>
        <stop offset=".72" stop-color="${color}" stop-opacity="${r2(op * 0.22)}"/>
        <stop offset="1" stop-color="${color}" stop-opacity="0"/>
      </linearGradient>`;
      body += `<polygon points="${pts}" fill="url(#${id})"/>`;
    });
  }
  return { defs, body: `<g style="mix-blend-mode:screen">${body}</g>` };
}

function haze(rand, w, h, key) {
  let defs = "";
  let body = "";
  const blobs = 3 + Math.floor(rand() * 2);
  for (let i = 0; i < blobs; i++) {
    const id = `hz${key}${i}`;
    const cx = w * (0.1 + rand() * 0.8);
    const cy = h * (0.25 + rand() * 0.6);
    const rx = w * (0.22 + rand() * 0.4);
    const ry = h * (0.12 + rand() * 0.28);
    const color = [PALETTE.flame, PALETTE.amber, PALETTE.ember][Math.floor(rand() * 3)];
    defs += `<radialGradient id="${id}">
      <stop offset="0" stop-color="${color}" stop-opacity="${r2(0.05 + rand() * 0.09)}"/>
      <stop offset=".55" stop-color="${color}" stop-opacity="${r2(0.02 + rand() * 0.04)}"/>
      <stop offset="1" stop-color="${color}" stop-opacity="0"/>
    </radialGradient>`;
    body += `<ellipse cx="${r2(cx)}" cy="${r2(cy)}" rx="${r2(rx)}" ry="${r2(ry)}" fill="url(#${id})"/>`;
  }
  return { defs, body: `<g style="mix-blend-mode:screen">${body}</g>` };
}

/* Glow de palco — a fonte de luz que fica ATRÁS do assunto. É ela que faz a
   silhueta ler como recorte preto, e não como mancha escura solta. */
function stageGlow(rand, w, h, key, y = 0.68) {
  const defs = `<radialGradient id="sg${key}" cx=".5" cy=".5" r=".5">
    <stop offset="0" stop-color="${PALETTE.amberHi}" stop-opacity=".3"/>
    <stop offset=".3" stop-color="${PALETTE.amber}" stop-opacity=".16"/>
    <stop offset=".62" stop-color="${PALETTE.flame}" stop-opacity=".07"/>
    <stop offset="1" stop-color="${PALETTE.flame}" stop-opacity="0"/>
  </radialGradient>`;
  const cx = w * (0.34 + rand() * 0.32);
  return {
    defs,
    body: `<g style="mix-blend-mode:screen"><ellipse cx="${r2(cx)}" cy="${r2(h * y)}" rx="${r2(w * 0.62)}" ry="${r2(h * 0.4)}" fill="url(#sg${key})"/></g>`,
  };
}

/* Poeira em suspensão no facho. Pontos pequenos — bokeh grande demais vira
   "bolha desfocada de stock", que é exatamente o que o site não pode parecer. */
function bokeh(rand, w, h, key, count = 26) {
  let defs = `<radialGradient id="bk${key}">
    <stop offset="0" stop-color="#fff6dd" stop-opacity=".9"/>
    <stop offset=".4" stop-color="${PALETTE.amber}" stop-opacity=".3"/>
    <stop offset="1" stop-color="${PALETTE.flame}" stop-opacity="0"/>
  </radialGradient>`;
  let body = "";
  for (let i = 0; i < count; i++) {
    const cx = w * rand();
    const cy = h * (0.06 + rand() * 0.78);
    const rad = w * (0.0012 + Math.pow(rand(), 3) * 0.011);
    body += `<circle cx="${r2(cx)}" cy="${r2(cy)}" r="${r2(rad)}" fill="url(#bk${key})" opacity="${r2(0.25 + rand() * 0.6)}"/>`;
  }
  return { defs, body: `<g style="mix-blend-mode:screen">${body}</g>` };
}

/* Multidão em contraluz: duas fileiras (fundo mais alto e claro, frente mais
   baixa e preta) pra dar profundidade, braços erguidos e um fio de rim-light
   no topo das cabeças — sem esse fio a silhueta some no preto do fundo. */
/* Multidão em contraluz.
   Nada de "fileiras": fileira de cabeça do mesmo tamanho na mesma altura sai
   como um colar de contas, que foi exatamente o resultado das duas primeiras
   tentativas desta placa. Aqui cada pessoa é sorteada num campo de
   profundidade — quem está mais perto fica mais baixo, maior e mais preto — e
   o conjunto é desenhado do fundo pra frente. O que se lê é massa com textura,
   não um padrão. */
function crowd(rand, w, h, key) {
  const N = Math.round(300 * (w / 1600));
  const people = [];

  for (let i = 0; i < N; i++) {
    // t=0 fundo, t=1 primeiro plano. Expoente < 1 adensa o fundo, que é como
    // a perspectiva realmente distribui gente numa plateia.
    const t = Math.pow(rand(), 0.62);
    people.push({
      t,
      x: w * (-0.03 + rand() * 1.06),
      y: h * (0.735 + t * 0.245) + (rand() - 0.5) * h * 0.018,
      r: w * (0.0042 + t * 0.0125) * (0.82 + rand() * 0.4),
      tilt: (rand() - 0.5) * 22,
      rim: rand(),
      arm: rand(),
      arc: rand() * 360,
    });
  }
  people.sort((a, b) => a.y - b.y);

  let bodies = "";
  let rims = "";

  for (const p of people) {
    // escurece conforme se aproxima: o plano de trás recebe mais névoa
    const shade = Math.round(13 - p.t * 11);
    const fill = `#${shade.toString(16).padStart(2, "0").repeat(3)}`;
    const g = `translate(${r2(p.x)},${r2(p.y)}) rotate(${r2(p.tilt)})`;

    bodies += `<g transform="${g}">`;
    bodies += `<path d="M${r2(-p.r * 2.3)},${r2(p.r * 4.2)} Q${r2(-p.r * 2)},${r2(p.r * 1.5)} 0,${r2(p.r * 1.35)} Q${r2(p.r * 2)},${r2(p.r * 1.5)} ${r2(p.r * 2.3)},${r2(p.r * 4.2)} Z" fill="${fill}"/>`;
    bodies += `<circle cx="0" cy="0" r="${r2(p.r)}" fill="${fill}"/>`;
    if (p.arm > 0.9) {
      // braço fino e bem curvado: reto e grosso vira taco de beisebol
      const lean = (p.rim - 0.5) * p.r * 6;
      const up = p.r * (4.5 + p.rim * 4.5);
      bodies += `<path d="M${r2(p.r * 0.7)},${r2(p.r * 2.2)} Q${r2(p.r * 2.2 + lean * 0.2)},${r2(-up * 0.35)} ${r2(lean + p.r)},${r2(-up)}" fill="none" stroke="${fill}" stroke-width="${r2(p.r * 0.24)}" stroke-linecap="round"/>`;
    }
    bodies += `</g>`;

    // Só uma minoria pega contraluz, e mais forte no fundo (que está mais
    // perto da fonte). Fio em todo mundo vira pontilhado regular — e
    // pontilhado regular é o que denuncia desenho vetorial.
    if (p.rim > 0.82) {
      const a0 = ((p.arc - 55) * Math.PI) / 180;
      const a1 = ((p.arc + 40) * Math.PI) / 180;
      const x0 = r2(Math.cos(a0) * p.r);
      const y0 = r2(Math.sin(a0) * p.r);
      const x1 = r2(Math.cos(a1) * p.r);
      const y1 = r2(Math.sin(a1) * p.r);
      rims += `<path transform="${g}" d="M${x0},${y0} A${r2(p.r)},${r2(p.r)} 0 0 1 ${x1},${y1}" fill="none" stroke="${PALETTE.amberHi}" stroke-width="${r2(Math.max(0.6, p.r * 0.11))}" stroke-linecap="round" opacity="${r2(0.42 - p.t * 0.26)}"/>`;
    }
  }

  return {
    defs: `<linearGradient id="fg${key}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#020203" stop-opacity="0"/>
      <stop offset="1" stop-color="#020203" stop-opacity="1"/>
    </linearGradient>`,
    body:
      `<g>${bodies}</g>` +
      `<g style="mix-blend-mode:screen">${rims}</g>` +
      `<rect x="0" y="${r2(h * 0.93)}" width="${w}" height="${r2(h * 0.07)}" fill="url(#fg${key})"/>`,
  };
}

// Treliça de palco: dois pórticos verticais + travessa, em silhueta.
function truss(rand, w, h, key) {
  const topY = h * 0.06;
  const barY = h * (0.2 + rand() * 0.06);
  const colW = w * 0.022;
  const sw = w * 0.0035;
  const S = `stroke="#08080a" stroke-width="${r2(sw)}" fill="none" opacity=".95"`;

  const leg = (x) => {
    let s = `<rect x="${r2(x)}" y="${r2(topY)}" width="${r2(colW)}" height="${r2(h - topY)}" fill="#08080a" opacity=".9"/>`;
    for (let y = topY; y < h; y += colW) {
      s += `<path d="M${r2(x)},${r2(y)} L${r2(x + colW)},${r2(y + colW)} M${r2(x + colW)},${r2(y)} L${r2(x)},${r2(y + colW)}" ${S}/>`;
    }
    return s;
  };

  let beam = `<rect x="${r2(w * 0.06)}" y="${r2(barY)}" width="${r2(w * 0.88)}" height="${r2(colW)}" fill="#08080a" opacity=".92"/>`;
  for (let x = w * 0.06; x < w * 0.94; x += colW) {
    beam += `<path d="M${r2(x)},${r2(barY)} L${r2(x + colW)},${r2(barY + colW)} M${r2(x + colW)},${r2(barY)} L${r2(x)},${r2(barY + colW)}" ${S}/>`;
  }

  // Refletores pendurados na travessa
  let heads = "";
  for (let i = 0; i < 9; i++) {
    const hx = w * (0.1 + (i / 8) * 0.8);
    heads += `<rect x="${r2(hx - w * 0.011)}" y="${r2(barY + colW)}" width="${r2(w * 0.022)}" height="${r2(h * 0.028)}" rx="${r2(w * 0.004)}" fill="#08080a"/>`;
    heads += `<circle cx="${r2(hx)}" cy="${r2(barY + colW + h * 0.028)}" r="${r2(w * 0.006)}" fill="${PALETTE.amberHi}" opacity=".55"/>`;
  }

  return { defs: "", body: leg(w * 0.055) + leg(w * 0.923) + beam + heads };
}

/* Painel de LED visto de longe numa sala escura: o conteúdo é uma diagonal
   de luz difusa, não confete colorido. Opacidade baixa e uma única direção
   de gradiente — painel muito saturado lê como mosaico decorativo. */
function ledwall(rand, w, h, key) {
  const cols = 40;
  const rows = 22;
  const padX = w * 0.13;
  const top = h * 0.18;
  const panelW = w - padX * 2;
  const panelH = h * 0.46;
  const gw = panelW / cols;
  const gh = panelH / rows;
  const phase = rand() * 6.3;

  const defs = `<linearGradient id="lw${key}" x1="0" y1="1" x2="1" y2="0">
      <stop offset="0" stop-color="${PALETTE.ember}"/>
      <stop offset=".45" stop-color="${PALETTE.flame}"/>
      <stop offset="1" stop-color="${PALETTE.amberHi}"/>
    </linearGradient>
    <radialGradient id="lg${key}" cx=".5" cy=".5" r=".5">
      <stop offset="0" stop-color="${PALETTE.flame}" stop-opacity=".3"/>
      <stop offset="1" stop-color="${PALETTE.flame}" stop-opacity="0"/>
    </radialGradient>`;

  let cells = "";
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      const wave = Math.sin(x / 7 + y / 4 + phase) * 0.5 + 0.5;
      const v = Math.pow(wave, 1.6) * 0.85 + rand() * 0.15;
      if (v < 0.12) continue;
      cells += `<rect x="${r2(padX + x * gw)}" y="${r2(top + y * gh)}" width="${r2(gw * 0.78)}" height="${r2(gh * 0.78)}" opacity="${r2(v * 0.5)}"/>`;
    }
  }

  const body =
    // moldura do painel + carcaça preta
    `<rect x="${r2(padX - gw * 1.6)}" y="${r2(top - gh * 1.6)}" width="${r2(panelW + gw * 3.2)}" height="${r2(panelH + gh * 3.2)}" fill="#08080a" stroke="#1a1a1e" stroke-width="${r2(w * 0.0016)}"/>` +
    `<g fill="url(#lw${key})">${cells}</g>` +
    // derrame de luz do painel na fumaça em volta
    `<g style="mix-blend-mode:screen"><ellipse cx="${r2(w / 2)}" cy="${r2(top + panelH * 0.55)}" rx="${r2(panelW * 0.85)}" ry="${r2(panelH * 1.1)}" fill="url(#lg${key})"/></g>`;

  return { defs, body };
}

// Mesa de som: fileiras de faders e knobs, vistos de cima em silhueta.
function console_(rand, w, h, key) {
  const top = h * 0.52;
  let body = `<rect x="0" y="${r2(top)}" width="${w}" height="${r2(h - top)}" fill="#08080a"/>`;
  const cols = 26;
  const cw = w / (cols + 2);
  for (let i = 0; i < cols; i++) {
    const x = cw * (i + 1.5);
    const fy = top + h * 0.12 + rand() * h * 0.2;
    body += `<rect x="${r2(x - cw * 0.06)}" y="${r2(top + h * 0.1)}" width="${r2(cw * 0.12)}" height="${r2(h * 0.3)}" fill="#16161a"/>`;
    body += `<rect x="${r2(x - cw * 0.22)}" y="${r2(fy)}" width="${r2(cw * 0.44)}" height="${r2(h * 0.022)}" rx="${r2(h * 0.008)}" fill="#2a2a30"/>`;
    body += `<circle cx="${r2(x)}" cy="${r2(top + h * 0.06)}" r="${r2(cw * 0.16)}" fill="none" stroke="#2a2a30" stroke-width="${r2(w * 0.002)}"/>`;
    if (rand() > 0.45) {
      const c = rand() > 0.7 ? PALETTE.ember : rand() > 0.4 ? PALETTE.amber : PALETTE.flame;
      body += `<circle cx="${r2(x)}" cy="${r2(top + h * 0.06)}" r="${r2(cw * 0.05)}" fill="${c}" opacity=".9"/>`;
    }
  }
  return { defs: "", body };
}

// Line array: duas torres de caixas suspensas em curva.
function pa(rand, w, h, key) {
  let body = "";
  const hang = (x0) => {
    let s = "";
    for (let i = 0; i < 11; i++) {
      const y = h * 0.1 + i * h * 0.052;
      const tilt = i * 0.9;
      const bw = w * (0.1 + i * 0.004);
      s += `<g transform="translate(${r2(x0)},${r2(y)}) rotate(${r2(tilt)})">
        <rect x="${r2(-bw / 2)}" y="0" width="${r2(bw)}" height="${r2(h * 0.044)}" rx="${r2(w * 0.004)}" fill="#08080a" stroke="#1e1e22" stroke-width="${r2(w * 0.0018)}"/>
        <circle cx="${r2(-bw * 0.22)}" cy="${r2(h * 0.022)}" r="${r2(bw * 0.13)}" fill="#131317"/>
        <circle cx="${r2(bw * 0.22)}" cy="${r2(h * 0.022)}" r="${r2(bw * 0.13)}" fill="#131317"/>
      </g>`;
    }
    return s;
  };
  body += hang(w * 0.2) + hang(w * 0.8);
  return { defs: "", body };
}

/* --- Montagem ------------------------------------------------------------- */

function plate({ name, w, h, seed, subject = "beams", density = 1, cool = false }) {
  const rand = rng(seed);
  const key = seed.toString(36);
  const parts = [];

  const B = beams(rand, w, h, { key, count: Math.round(8 * density), spread: cool ? 1.25 : 1 });
  const Z = haze(rand, w, h, key);
  const K = bokeh(rand, w, h, key, Math.round(30 * density));
  const G = stageGlow(rand, w, h, key, subject === "crowd" ? 0.72 : subject === "truss" ? 0.5 : 0.58);

  let subjectPart = { defs: "", body: "" };
  if (subject === "crowd") subjectPart = crowd(rand, w, h, key);
  else if (subject === "truss") subjectPart = truss(rand, w, h, key);
  else if (subject === "led") subjectPart = ledwall(rand, w, h, key);
  else if (subject === "console") subjectPart = console_(rand, w, h, key);
  else if (subject === "pa") subjectPart = pa(rand, w, h, key);

  const defs = `
    <linearGradient id="bg${key}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#0d0d10"/>
      <stop offset=".55" stop-color="#08080a"/>
      <stop offset="1" stop-color="#050505"/>
    </linearGradient>
    <radialGradient id="vg${key}" cx=".5" cy=".48" r=".72">
      <stop offset=".4" stop-color="#000" stop-opacity="0"/>
      <stop offset=".8" stop-color="#000" stop-opacity=".42"/>
      <stop offset="1" stop-color="#000" stop-opacity=".82"/>
    </radialGradient>
    <linearGradient id="fl${key}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#000" stop-opacity=".3"/>
      <stop offset=".22" stop-color="#000" stop-opacity="0"/>
      <stop offset=".82" stop-color="#000" stop-opacity="0"/>
      <stop offset="1" stop-color="#000" stop-opacity=".45"/>
    </linearGradient>
    ${G.defs}${Z.defs}${B.defs}${K.defs}${subjectPart.defs}`;

  parts.push(`<rect width="${w}" height="${h}" fill="url(#bg${key})"/>`);
  parts.push(G.body);
  parts.push(Z.body);
  parts.push(B.body);
  if (subject === "led" || subject === "console" || subject === "pa") parts.push(subjectPart.body);
  parts.push(K.body);
  if (subject === "truss" || subject === "crowd") parts.push(subjectPart.body);
  parts.push(`<rect width="${w}" height="${h}" fill="url(#fl${key})"/>`);
  parts.push(`<rect width="${w}" height="${h}" fill="url(#vg${key})"/>`);

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" role="img" preserveAspectRatio="xMidYMid slice"><defs>${defs}</defs>${parts.join("")}</svg>`;

  writeFileSync(join(OUT, `${name}.svg`), svg.replace(/\n\s+/g, ""));
  return `${name}.svg`;
}

/* --- Grão global (usado como background-image fixo em .grain) ------------- */
function grain() {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency=".82" numOctaves="3" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="200" height="200" filter="url(#n)"/></svg>`;
  writeFileSync(join(OUT, "grain.svg"), svg);
  return "grain.svg";
}

/* --- Catálogo ------------------------------------------------------------- */

const made = [];

// Herói
made.push(plate({ name: "hero", w: 1920, h: 1080, seed: 1997, subject: "crowd", density: 1.35 }));
made.push(plate({ name: "hero-alt", w: 1920, h: 1080, seed: 2011, subject: "truss", density: 1.2 }));

// Cases / projetos (formato largo, editorial)
made.push(plate({ name: "case-festival", w: 1600, h: 1000, seed: 3101, subject: "crowd", density: 1.3 }));
made.push(plate({ name: "case-corporativo", w: 1600, h: 1000, seed: 3202, subject: "led", density: 0.9 }));
made.push(plate({ name: "case-turne", w: 1600, h: 1000, seed: 3303, subject: "truss", density: 1.15 }));
made.push(plate({ name: "case-privado", w: 1600, h: 1000, seed: 3404, subject: "beams", density: 1.1 }));

// Galeria
made.push(plate({ name: "g-palco-01", w: 1200, h: 1500, seed: 4101, subject: "truss" }));
made.push(plate({ name: "g-palco-02", w: 1600, h: 1067, seed: 4102, subject: "truss", density: 1.2 }));
made.push(plate({ name: "g-luz-01", w: 1200, h: 1200, seed: 4201, subject: "beams", density: 1.5 }));
made.push(plate({ name: "g-luz-02", w: 1200, h: 1500, seed: 4202, subject: "beams", density: 1.6, cool: true }));
made.push(plate({ name: "g-publico-01", w: 1600, h: 1067, seed: 4301, subject: "crowd", density: 1.3 }));
made.push(plate({ name: "g-publico-02", w: 1200, h: 1200, seed: 4302, subject: "crowd", density: 1.1 }));
made.push(plate({ name: "g-bastidores-01", w: 1200, h: 1500, seed: 4401, subject: "console", density: 0.7 }));
made.push(plate({ name: "g-bastidores-02", w: 1600, h: 1067, seed: 4402, subject: "console", density: 0.8 }));
made.push(plate({ name: "g-led-01", w: 1600, h: 1067, seed: 4501, subject: "led", density: 0.8 }));
made.push(plate({ name: "g-som-01", w: 1200, h: 1500, seed: 4601, subject: "pa", density: 0.9 }));
made.push(plate({ name: "g-som-02", w: 1200, h: 1200, seed: 4602, subject: "pa", density: 1 }));
made.push(plate({ name: "g-luz-03", w: 1600, h: 1067, seed: 4203, subject: "beams", density: 1.7 }));

// Casting — retrato vertical, um facho por artista
const casting = [
  ["vou-pro-sereno", 5101],
  ["netinho-de-paula", 5102],
  ["samba-90-graus", 5103],
  ["grupo-do-bola", 5104],
  ["marvvila", 5105],
  ["dudu-nobre", 5106],
];
for (const [slug, seed] of casting) {
  made.push(plate({ name: `artista-${slug}`, w: 900, h: 1200, seed, subject: "beams", density: 1.2 }));
}

// Serviços — placa vertical por card
const servicos = [
  ["booking", 6101, "crowd"],
  ["gestao", 6102, "beams"],
  ["producao", 6103, "truss"],
  ["estrutura", 6104, "truss"],
  ["som", 6105, "pa"],
  ["luz", 6106, "beams"],
  ["led", 6107, "led"],
  ["corporativo", 6108, "led"],
  ["privado", 6109, "beams"],
  ["internacional", 6110, "crowd"],
];
for (const [slug, seed, subject] of servicos) {
  made.push(plate({ name: `svc-${slug}`, w: 900, h: 1200, seed, subject, density: 1 }));
}

// Interiores de página
made.push(plate({ name: "sobre", w: 1600, h: 1000, seed: 7101, subject: "truss", density: 1.1 }));
made.push(plate({ name: "contato", w: 1600, h: 1000, seed: 7202, subject: "beams", density: 1.3 }));
made.push(grain());

console.log(`${made.length} arquivos gerados em public/media/`);
