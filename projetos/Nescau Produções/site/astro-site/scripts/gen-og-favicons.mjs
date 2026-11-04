/* ============================================================================
   Gerador de favicon set + og-image + manifest
   ----------------------------------------------------------------------------
   O favicon.svg é a fonte da verdade (paleta e wordmark do design-guide).
   Este script rasteriza a partir dele, então basta editar public/favicon.svg
   e rodar `npm run gen:og` de novo pra propagar a mudança pros PNGs.
   ========================================================================== */
import sharp from "sharp";
import { writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const PUB = join(dirname(fileURLToPath(import.meta.url)), "..", "public");

const faviconSvg = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" fill="none">
    <defs>
        <linearGradient id="halo" x1="4" y1="4" x2="28" y2="28" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#ffe07a" />
            <stop offset="0.4" stop-color="#ffc531" />
            <stop offset="1" stop-color="#ff7a18" />
        </linearGradient>
    </defs>
    <circle cx="16" cy="16" r="14" fill="#050505" />
    <circle cx="16" cy="16" r="12.4" stroke="url(#halo)" stroke-width="2.2" />
    <text x="16" y="21.5" text-anchor="middle" font-family="Arial, sans-serif" font-weight="700" font-size="14" fill="#FFFFFF">N</text>
</svg>`;

async function makeFavicons() {
  const sizes = [
    ["favicon-32x32.png", 32],
    ["favicon-16x16.png", 16],
    ["apple-touch-icon.png", 180],
    ["icon-192.png", 192],
    ["icon-512.png", 512],
  ];
  for (const [name, size] of sizes) {
    await sharp(Buffer.from(faviconSvg), { density: 384 })
      .resize(size, size)
      .png()
      .toFile(join(PUB, name));
    console.log("wrote", name);
  }
}

function ogSvg() {
  return `
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <radialGradient id="leak1" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#ff7a18" stop-opacity="0.55"/>
      <stop offset="70%" stop-color="#ff7a18" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="leak2" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#ffc531" stop-opacity="0.35"/>
      <stop offset="70%" stop-color="#ffc531" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="beamText" x1="0%" y1="0%" x2="100%" y2="30%">
      <stop offset="0%" stop-color="#ffe07a"/>
      <stop offset="30%" stop-color="#ffc531"/>
      <stop offset="100%" stop-color="#ff7a18"/>
    </linearGradient>
  </defs>

  <rect width="1200" height="630" fill="#050505"/>
  <circle cx="880" cy="120" r="420" fill="url(#leak1)"/>
  <circle cx="140" cy="560" r="320" fill="url(#leak2)"/>

  <text x="80" y="290" font-family="Arial, sans-serif" font-weight="900" font-size="108" letter-spacing="-2"
        fill="url(#beamText)" style="text-transform:uppercase">NESCAU</text>
  <text x="80" y="350" font-family="Arial, sans-serif" font-weight="700" font-size="34" letter-spacing="10"
        fill="#ffffff" fill-opacity="0.7" style="text-transform:uppercase">Produções</text>

  <text x="80" y="440" font-family="Arial, sans-serif" font-weight="400" font-size="30"
        fill="#ffffff" fill-opacity="0.66">Samba e pagode que seguram uma data inteira</text>

  <text x="80" y="560" font-family="Arial, sans-serif" font-weight="700" font-size="20" letter-spacing="4"
        fill="#ffc531" style="text-transform:uppercase">Desde 1997 · Brasil · Europa · EUA</text>
</svg>`;
}

async function makeOg() {
  await sharp(Buffer.from(ogSvg())).png().toFile(join(PUB, "og-image.png"));
  console.log("wrote og-image.png");
}

await makeFavicons();
await makeOg();

const manifest = {
  name: "Nescau Produções",
  short_name: "Nescau",
  description: "Gestão de carreira e venda de shows de samba e pagode",
  start_url: "/",
  display: "standalone",
  background_color: "#050505",
  theme_color: "#050505",
  icons: [
    { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
    { src: "/icon-512.png", sizes: "512x512", type: "image/png" },
  ],
};
writeFileSync(join(PUB, "site.webmanifest"), JSON.stringify(manifest, null, 2) + "\n");
console.log("wrote site.webmanifest");
