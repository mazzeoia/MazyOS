/* ============================================================================
   Motor de movimento do site
   ----------------------------------------------------------------------------
   Um único módulo, uma única fonte de verdade: Lenis conduz o scroll, GSAP
   conduz o tempo (ticker compartilhado — dois loops de rAF concorrentes é a
   causa mais comum de scrollytelling tremido) e ScrollTrigger só reage.

   As libs entram por bundle, não por CDN: o CSP do site é `script-src 'self'`.

   Tudo aqui é declarativo por atributo no HTML (`data-anim`, `data-parallax`,
   `data-count`…), então nenhuma seção precisa do seu próprio <script>.
   ========================================================================== */

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { Flip } from "gsap/Flip";
import Lenis from "lenis";
import SplitType from "split-type";

gsap.registerPlugin(ScrollTrigger, Flip);

const EASE = "power3.out";
const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const finePointer = window.matchMedia("(pointer: fine)").matches;

/* -------------------------------------------------------------------------
   Sem movimento: nada de Lenis, nada de ScrollTrigger. Só garante que todo
   estado inicial de animação seja neutralizado e o conteúdo fique visível.
   ------------------------------------------------------------------------- */
function settleStatic() {
  document.querySelectorAll<HTMLElement>("[data-anim], [data-anim-group] > *").forEach((el) => {
    el.style.opacity = "1";
    el.style.transform = "none";
    el.style.filter = "none";
    el.style.clipPath = "none";
  });
  document.querySelectorAll<HTMLElement>("[data-count]").forEach((el) => {
    el.textContent = formatCount(Number(el.dataset.count ?? 0), el.dataset.countDecimals);
  });
}

/* =========================================================================
   1. Scroll — Lenis + ticker do GSAP
   ========================================================================= */

let lenis: Lenis | null = null;

function initScroll() {
  lenis = new Lenis({
    duration: 1.05,
    // Curva exponencial: rápido na largada, freio longo. É o que dá a
    // sensação de "peso" sem virar aquele scroll lento que atrasa a leitura.
    easing: (t: number) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    smoothWheel: true,
    // Touch fica com o scroll nativo: em celular o smooth-scroll sintético
    // briga com o overscroll do sistema e piora a percepção de performance.
    syncTouch: false,
    wheelMultiplier: 1,
    touchMultiplier: 1.6,
  });

  lenis.on("scroll", ScrollTrigger.update);
  gsap.ticker.add((time) => lenis?.raf(time * 1000));
  gsap.ticker.lagSmoothing(0);

  // Âncoras internas passam pelo Lenis pra manter a mesma curva de
  // desaceleração do scroll manual.
  document.addEventListener("click", (e) => {
    const link = (e.target as HTMLElement)?.closest?.<HTMLAnchorElement>('a[href^="#"]');
    if (!link) return;
    const id = link.getAttribute("href");
    if (!id || id === "#") return;
    const target = document.querySelector(id);
    if (!target) return;
    e.preventDefault();
    lenis?.scrollTo(target as HTMLElement, { offset: -80, duration: 1.2 });
  });
}

/* =========================================================================
   2. Revelação de texto — SplitType + máscara por linha
   ========================================================================= */

const splits: SplitType[] = [];

function initSplitText() {
  document.querySelectorAll<HTMLElement>("[data-split]").forEach((el) => {
    const split = new SplitType(el, {
      types: "lines,words",
      lineClass: "line",
      wordClass: "word",
    });
    splits.push(split);
    el.classList.add("is-split");

    const words = split.words ?? [];
    if (!words.length) return;

    gsap.set(words, { yPercent: 118, opacity: 0 });

    const mode = el.dataset.split; // "hero" dispara na carga, o resto no scroll
    const tween = gsap.to(words, {
      yPercent: 0,
      opacity: 1,
      duration: 1.05,
      ease: "power4.out",
      stagger: { each: 0.045, from: "start" },
      paused: mode === "hero",
    });

    if (mode === "hero") {
      tween.delay(0.25).play();
    } else {
      ScrollTrigger.create({
        trigger: el,
        start: "top 84%",
        once: true,
        animation: tween,
      });
    }
  });
}

/* Texto que acende palavra por palavra conforme a página rola. Preso ao
   scroll (scrub), não disparado por gatilho: quem controla o ritmo da frase é
   o dedo do usuário, e é isso que faz a seção parecer "viva" em vez de
   animada. */
function initScrubText() {
  document.querySelectorAll<HTMLElement>("[data-scrub-text]").forEach((el) => {
    const split = new SplitType(el, { types: "lines,words", lineClass: "line", wordClass: "word" });
    splits.push(split);
    el.classList.add("is-split");

    const words = split.words ?? [];
    if (!words.length) return;

    gsap.set(words, { opacity: 0.14 });
    gsap.to(words, {
      opacity: 1,
      ease: "none",
      stagger: 0.5,
      scrollTrigger: {
        trigger: el,
        start: "top 78%",
        end: "bottom 52%",
        scrub: 0.4,
      },
    });
  });
}

// Quebra de linha depende da métrica da fonte: re-split ao redimensionar em
// largura (altura muda sozinha quando a barra do navegador móvel some).
function watchResplit() {
  let lastWidth = window.innerWidth;
  let timer: number;
  window.addEventListener("resize", () => {
    if (window.innerWidth === lastWidth) return;
    lastWidth = window.innerWidth;
    window.clearTimeout(timer);
    timer = window.setTimeout(() => {
      splits.forEach((s) => s.split({}));
      document.querySelectorAll<HTMLElement>("[data-split] .word").forEach((w) => {
        gsap.set(w, { yPercent: 0, opacity: 1 });
      });
      ScrollTrigger.refresh();
    }, 220);
  });
}

/* =========================================================================
   3. Entradas por scroll — fade / rise / blur / scale / máscara / imagem
   ========================================================================= */

function initReveals() {
  document.querySelectorAll<HTMLElement>("[data-anim]").forEach((el) => {
    const kind = el.dataset.anim;
    const delay = Number(el.dataset.animDelay ?? 0);
    const base = {
      scrollTrigger: { trigger: el, start: el.dataset.animStart ?? "top 86%", once: true },
      duration: 1,
      delay,
      ease: EASE,
    } as const;

    switch (kind) {
      case "fade":
        gsap.fromTo(el, { opacity: 0 }, { opacity: 1, ...base });
        break;
      case "rise":
        gsap.fromTo(el, { opacity: 0, y: 32 }, { opacity: 1, y: 0, ...base });
        break;
      case "blur":
        gsap.fromTo(
          el,
          { opacity: 0, filter: "blur(14px)", y: 20 },
          { opacity: 1, filter: "blur(0px)", y: 0, ...base, duration: 1.2 },
        );
        break;
      case "scale":
        gsap.fromTo(el, { opacity: 0, scale: 1.06 }, { opacity: 1, scale: 1, ...base, duration: 1.3 });
        break;
      case "mask":
        gsap.fromTo(
          el,
          { clipPath: "inset(0 0 100% 0)" },
          { clipPath: "inset(0 0 0% 0)", ...base, duration: 1.15 },
        );
        break;
      case "mask-x":
        gsap.fromTo(
          el,
          { clipPath: "inset(0 100% 0 0)" },
          { clipPath: "inset(0 0% 0 0)", ...base, duration: 1.15 },
        );
        break;
      case "reveal-img": {
        // A janela abre de baixo pra cima enquanto a imagem desfaz a escala:
        // as duas metades do movimento se cancelam e a foto parece "entrar"
        // no lugar em vez de crescer.
        const img = el.querySelector("img");
        const tl = gsap.timeline({
          scrollTrigger: { trigger: el, start: el.dataset.animStart ?? "top 88%", once: true },
          delay,
        });
        tl.fromTo(
          el,
          { clipPath: "inset(0 0 100% 0)" },
          { clipPath: "inset(0 0 0% 0)", duration: 1.25, ease: EASE },
        );
        if (img) tl.fromTo(img, { scale: 1.22 }, { scale: 1, duration: 1.5, ease: EASE }, 0);
        break;
      }
    }
  });

  document.querySelectorAll<HTMLElement>("[data-anim-group]").forEach((group) => {
    const kids = Array.from(group.children) as HTMLElement[];
    if (!kids.length) return;
    gsap.fromTo(
      kids,
      { opacity: 0, y: 26 },
      {
        opacity: 1,
        y: 0,
        duration: 0.9,
        ease: EASE,
        stagger: Number(group.dataset.animGroup) || 0.08,
        scrollTrigger: { trigger: group, start: "top 85%", once: true },
      },
    );
  });
}

/* =========================================================================
   4. Parallax e escala presa ao scroll
   ========================================================================= */

function initParallax() {
  document.querySelectorAll<HTMLElement>("[data-parallax]").forEach((el) => {
    const strength = Number(el.dataset.parallax) || 0.15;
    gsap.fromTo(
      el,
      { yPercent: -strength * 50 },
      {
        yPercent: strength * 50,
        ease: "none",
        scrollTrigger: {
          trigger: el.dataset.parallaxTrigger
            ? (el.closest(el.dataset.parallaxTrigger) as HTMLElement) ?? el
            : el,
          start: "top bottom",
          end: "bottom top",
          scrub: true,
        },
      },
    );
  });

  // Traço que se desenha conforme a seção passa (linha do processo).
  // scaleY em vez de stroke-dashoffset: é a mesma leitura visual e roda no
  // compositor, sem recalcular geometria de path a cada quadro.
  document.querySelectorAll<HTMLElement>("[data-draw]").forEach((el) => {
    const scope = (el.closest(el.dataset.draw || "section") as HTMLElement) ?? el;
    gsap.fromTo(
      el,
      { scaleY: 0 },
      {
        scaleY: 1,
        ease: "none",
        transformOrigin: "top center",
        scrollTrigger: { trigger: scope, start: "top 62%", end: "bottom 78%", scrub: 0.5 },
      },
    );
  });

  // Camada de fundo que afunda e escurece enquanto a seção sai — dá
  // profundidade sem precisar de vídeo.
  document.querySelectorAll<HTMLElement>("[data-sink]").forEach((el) => {
    gsap.to(el, {
      yPercent: 12,
      scale: 1.08,
      opacity: 0.35,
      ease: "none",
      scrollTrigger: { trigger: el, start: "top top", end: "bottom top", scrub: true },
    });
  });
}

/* =========================================================================
   5. Contador numérico
   ========================================================================= */

function formatCount(value: number, decimals?: string) {
  const d = Number(decimals ?? 0);
  return value.toLocaleString("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d });
}

function initCounters() {
  document.querySelectorAll<HTMLElement>("[data-count]").forEach((el) => {
    const target = Number(el.dataset.count ?? 0);
    const decimals = el.dataset.countDecimals;
    const obj = { v: Number(el.dataset.countFrom ?? 0) };
    el.textContent = formatCount(obj.v, decimals);
    gsap.to(obj, {
      v: target,
      duration: 2.1,
      ease: "power2.out",
      scrollTrigger: { trigger: el, start: "top 88%", once: true },
      onUpdate: () => {
        el.textContent = formatCount(obj.v, decimals);
      },
    });
  });
}

/* =========================================================================
   6. Indicador de progresso da página
   ========================================================================= */

function initProgress() {
  const bar = document.querySelector<HTMLElement>("[data-progress]");
  if (!bar) return;
  gsap.set(bar, { scaleX: 0, transformOrigin: "left center" });
  gsap.to(bar, {
    scaleX: 1,
    ease: "none",
    scrollTrigger: { start: 0, end: () => document.body.scrollHeight - window.innerHeight, scrub: 0.3 },
  });
}

/* =========================================================================
   7. Seção horizontal presa
   ========================================================================= */

function initHorizontal() {
  if (window.innerWidth < 900) return;

  document.querySelectorAll<HTMLElement>("[data-hscroll]").forEach((section) => {
    const track = section.querySelector<HTMLElement>("[data-hscroll-track]");
    if (!track) return;

    const distance = () => Math.max(0, track.scrollWidth - section.clientWidth);
    if (distance() <= 0) return;

    gsap.to(track, {
      x: () => -distance(),
      ease: "none",
      scrollTrigger: {
        trigger: section,
        pin: true,
        scrub: 0.6,
        // A altura de scroll acompanha a largura real do trilho, então o
        // ritmo não muda quando entra ou sai um card.
        end: () => "+=" + distance(),
        invalidateOnRefresh: true,
        anticipatePin: 1,
      },
    });
  });
}

/* =========================================================================
   8. Microinterações de ponteiro
   ========================================================================= */

function initMagnetic() {
  if (!finePointer) return;

  document.querySelectorAll<HTMLElement>("[data-magnetic]").forEach((el) => {
    const pull = Number(el.dataset.magnetic) || 0.32;
    const label = el.querySelector<HTMLElement>("[data-magnetic-label]");
    const xTo = gsap.quickTo(el, "x", { duration: 0.5, ease: "power3.out" });
    const yTo = gsap.quickTo(el, "y", { duration: 0.5, ease: "power3.out" });
    const lxTo = label ? gsap.quickTo(label, "x", { duration: 0.7, ease: "power3.out" }) : null;
    const lyTo = label ? gsap.quickTo(label, "y", { duration: 0.7, ease: "power3.out" }) : null;

    el.addEventListener("pointermove", (e) => {
      const r = el.getBoundingClientRect();
      const dx = e.clientX - (r.left + r.width / 2);
      const dy = e.clientY - (r.top + r.height / 2);
      xTo(dx * pull);
      yTo(dy * pull);
      lxTo?.(dx * pull * 0.4);
      lyTo?.(dy * pull * 0.4);
    });

    el.addEventListener("pointerleave", () => {
      xTo(0);
      yTo(0);
      lxTo?.(0);
      lyTo?.(0);
    });
  });
}

function initTilt() {
  if (!finePointer) return;

  document.querySelectorAll<HTMLElement>("[data-tilt]").forEach((el) => {
    const max = Number(el.dataset.tilt) || 7;
    const rx = gsap.quickTo(el, "rotationX", { duration: 0.6, ease: "power3.out" });
    const ry = gsap.quickTo(el, "rotationY", { duration: 0.6, ease: "power3.out" });
    gsap.set(el, { transformPerspective: 1000, transformOrigin: "center" });

    el.addEventListener("pointermove", (e) => {
      const r = el.getBoundingClientRect();
      const px = (e.clientX - r.left) / r.width - 0.5;
      const py = (e.clientY - r.top) / r.height - 0.5;
      rx(-py * max * 2);
      ry(px * max * 2);
      // O brilho segue o ponteiro pela superfície: é o que faz o card
      // parecer material, e não uma div inclinada.
      el.style.setProperty("--sheen-x", `${((e.clientX - r.left) / r.width) * 100}%`);
      el.style.setProperty("--sheen-y", `${((e.clientY - r.top) / r.height) * 100}%`);
    });

    el.addEventListener("pointerleave", () => {
      rx(0);
      ry(0);
    });
  });
}

function initMouseGlow() {
  const glow = document.querySelector<HTMLElement>("[data-mouse-glow]");
  if (!glow || !finePointer) return;

  const xTo = gsap.quickTo(glow, "x", { duration: 0.85, ease: "power3.out" });
  const yTo = gsap.quickTo(glow, "y", { duration: 0.85, ease: "power3.out" });
  let shown = false;

  window.addEventListener("pointermove", (e) => {
    if (!shown) {
      shown = true;
      gsap.to(glow, { opacity: 1, duration: 0.6 });
    }
    xTo(e.clientX);
    yTo(e.clientY);
  });

  document.addEventListener("pointerleave", () => {
    shown = false;
    gsap.to(glow, { opacity: 0, duration: 0.4 });
  });
}

// Cursor de contexto: só aparece sobre zonas marcadas e mostra o que aquele
// alvo faz ("VER", "ARRASTAR"). O cursor nativo continua visível — esconder
// o ponteiro do sistema é o tipo de firula que quebra usabilidade.
function initContextCursor() {
  const cursor = document.querySelector<HTMLElement>("[data-cursor-ring]");
  if (!cursor || !finePointer) return;

  const labelEl = cursor.querySelector<HTMLElement>("[data-cursor-label]");
  const xTo = gsap.quickTo(cursor, "x", { duration: 0.35, ease: "power3.out" });
  const yTo = gsap.quickTo(cursor, "y", { duration: 0.35, ease: "power3.out" });

  window.addEventListener("pointermove", (e) => {
    xTo(e.clientX);
    yTo(e.clientY);
  });

  document.querySelectorAll<HTMLElement>("[data-cursor]").forEach((zone) => {
    zone.addEventListener("pointerenter", () => {
      if (labelEl) labelEl.textContent = zone.dataset.cursor || "";
      gsap.to(cursor, { scale: 1, opacity: 1, duration: 0.35, ease: "back.out(2)" });
    });
    zone.addEventListener("pointerleave", () => {
      gsap.to(cursor, { scale: 0.4, opacity: 0, duration: 0.25 });
    });
  });
}

/* =========================================================================
   9. Filtro de galeria com FLIP
   ========================================================================= */

function initGalleryFilter() {
  const gallery = document.querySelector<HTMLElement>("[data-gallery]");
  if (!gallery) return;

  const buttons = gallery.querySelectorAll<HTMLButtonElement>("[data-filter]");
  const items = gallery.querySelectorAll<HTMLElement>("[data-cat]");
  if (!buttons.length || !items.length) return;

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const cat = btn.dataset.filter ?? "todos";

      buttons.forEach((b) => {
        const on = b === btn;
        b.classList.toggle("is-on", on);
        b.setAttribute("aria-pressed", String(on));
      });

      // FLIP mede antes, aplica a mudança, e anima a diferença: os itens que
      // continuam visíveis deslizam pra nova posição em vez de saltar.
      const state = Flip.getState(items);
      items.forEach((item) => {
        const show = cat === "todos" || item.dataset.cat === cat;
        item.classList.toggle("is-hidden", !show);
      });

      Flip.from(state, {
        duration: 0.65,
        ease: "power3.inOut",
        scale: true,
        absolute: true,
        onEnter: (els) => gsap.fromTo(els, { opacity: 0, scale: 0.86 }, { opacity: 1, scale: 1, duration: 0.5 }),
        onLeave: (els) => gsap.to(els, { opacity: 0, scale: 0.86, duration: 0.35 }),
      });
    });
  });
}

/* =========================================================================
   10. Lightbox da galeria
   ========================================================================= */

function initLightbox() {
  const box = document.querySelector<HTMLElement>("[data-lightbox]");
  if (!box) return;

  const imgEl = box.querySelector<HTMLImageElement>("[data-lightbox-img]");
  const capEl = box.querySelector<HTMLElement>("[data-lightbox-caption]");
  const counterEl = box.querySelector<HTMLElement>("[data-lightbox-counter]");
  const triggers = Array.from(document.querySelectorAll<HTMLElement>("[data-lightbox-open]"));
  if (!imgEl || !triggers.length) return;

  let index = 0;
  let opener: HTMLElement | null = null;

  const paint = () => {
    const el = triggers[index];
    const img = el.querySelector("img");
    imgEl.src = el.dataset.full || img?.getAttribute("src") || "";
    imgEl.alt = img?.getAttribute("alt") || "";
    if (capEl) capEl.textContent = el.dataset.caption || "";
    if (counterEl) counterEl.textContent = `${String(index + 1).padStart(2, "0")} / ${String(triggers.length).padStart(2, "0")}`;
    gsap.fromTo(imgEl, { opacity: 0, scale: 1.04 }, { opacity: 1, scale: 1, duration: 0.45, ease: EASE });
  };

  const open = (i: number, from: HTMLElement) => {
    index = i;
    opener = from;
    box.hidden = false;
    box.setAttribute("aria-hidden", "false");
    lenis?.stop();
    paint();
    gsap.fromTo(box, { opacity: 0 }, { opacity: 1, duration: 0.35 });
    box.querySelector<HTMLButtonElement>("[data-lightbox-close]")?.focus();
  };

  const close = () => {
    gsap.to(box, {
      opacity: 0,
      duration: 0.28,
      onComplete: () => {
        box.hidden = true;
        box.setAttribute("aria-hidden", "true");
        lenis?.start();
        opener?.focus();
      },
    });
  };

  const step = (dir: number) => {
    index = (index + dir + triggers.length) % triggers.length;
    paint();
  };

  triggers.forEach((el, i) => {
    el.addEventListener("click", () => open(i, el));
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        open(i, el);
      }
    });
  });

  box.querySelector("[data-lightbox-close]")?.addEventListener("click", close);
  box.querySelector("[data-lightbox-prev]")?.addEventListener("click", () => step(-1));
  box.querySelector("[data-lightbox-next]")?.addEventListener("click", () => step(1));
  box.addEventListener("click", (e) => {
    if (e.target === box) close();
  });

  document.addEventListener("keydown", (e) => {
    if (box.hidden) return;
    if (e.key === "Escape") close();
    if (e.key === "ArrowLeft") step(-1);
    if (e.key === "ArrowRight") step(1);
  });
}

/* =========================================================================
   11. Acordeão (FAQ)
   ========================================================================= */

function initAccordion() {
  document.querySelectorAll<HTMLElement>("[data-accordion]").forEach((root) => {
    const items = root.querySelectorAll<HTMLElement>("[data-accordion-item]");

    items.forEach((item) => {
      const btn = item.querySelector<HTMLButtonElement>("[data-accordion-trigger]");
      const panel = item.querySelector<HTMLElement>("[data-accordion-panel]");
      if (!btn || !panel) return;

      gsap.set(panel, { height: 0, opacity: 0 });

      btn.addEventListener("click", () => {
        const isOpen = item.classList.contains("is-open");

        items.forEach((other) => {
          if (other === item) return;
          const oPanel = other.querySelector<HTMLElement>("[data-accordion-panel]");
          const oBtn = other.querySelector<HTMLButtonElement>("[data-accordion-trigger]");
          if (other.classList.contains("is-open") && oPanel) {
            other.classList.remove("is-open");
            oBtn?.setAttribute("aria-expanded", "false");
            gsap.to(oPanel, { height: 0, opacity: 0, duration: 0.4, ease: "power3.inOut" });
          }
        });

        item.classList.toggle("is-open", !isOpen);
        btn.setAttribute("aria-expanded", String(!isOpen));
        gsap.to(panel, {
          height: isOpen ? 0 : "auto",
          opacity: isOpen ? 0 : 1,
          duration: 0.45,
          ease: "power3.inOut",
          onComplete: () => ScrollTrigger.refresh(),
        });
      });
    });
  });
}

/* =========================================================================
   12. Casting — nome em foco troca a foto (padrão editorial)
   ========================================================================= */

function initHoverIndex() {
  const root = document.querySelector<HTMLElement>("[data-hoverindex]");
  if (!root) return;

  const rows = root.querySelectorAll<HTMLElement>("[data-hoverindex-row]");
  const plates = root.querySelectorAll<HTMLElement>("[data-hoverindex-plate]");
  if (!rows.length || !plates.length) return;

  const stage = root.querySelector<HTMLElement>("[data-hoverindex-stage]");

  if (finePointer && stage) {
    const xTo = gsap.quickTo(stage, "x", { duration: 0.9, ease: "power3.out" });
    const yTo = gsap.quickTo(stage, "y", { duration: 0.9, ease: "power3.out" });
    root.addEventListener("pointermove", (e) => {
      const r = root.getBoundingClientRect();
      xTo(e.clientX - r.left - stage.offsetWidth / 2);
      yTo(e.clientY - r.top - stage.offsetHeight / 2);
    });
  }

  const activate = (i: number) => {
    plates.forEach((p, pi) => {
      gsap.to(p, { opacity: pi === i ? 1 : 0, scale: pi === i ? 1 : 1.06, duration: 0.5, ease: EASE });
    });
    rows.forEach((r, ri) => r.classList.toggle("is-on", ri === i));
    if (stage) gsap.to(stage, { opacity: 1, scale: 1, duration: 0.45, ease: EASE });
  };

  rows.forEach((row, i) => {
    row.addEventListener("pointerenter", () => activate(i));
    row.addEventListener("focusin", () => activate(i));
  });

  root.addEventListener("pointerleave", () => {
    rows.forEach((r) => r.classList.remove("is-on"));
    if (stage) gsap.to(stage, { opacity: 0, scale: 0.94, duration: 0.4, ease: EASE });
    gsap.to(plates, { opacity: 0, duration: 0.4 });
  });
}

/* =========================================================================
   13. Navbar — esconde ao descer, aparece ao subir
   ========================================================================= */

function initNav() {
  const nav = document.querySelector<HTMLElement>("[data-nav]");
  if (!nav) return;

  let last = 0;
  ScrollTrigger.create({
    start: 0,
    end: "max",
    onUpdate: (self) => {
      const y = self.scroll();
      nav.classList.toggle("is-solid", y > 40);
      if (y > 220 && y > last + 4) nav.classList.add("is-away");
      else if (y < last - 4) nav.classList.remove("is-away");
      last = y;
    },
  });
}

/* =========================================================================
   14. Marquee infinito
   ========================================================================= */

function initMarquee() {
  document.querySelectorAll<HTMLElement>("[data-marquee]").forEach((el) => {
    const track = el.querySelector<HTMLElement>("[data-marquee-track]");
    if (!track) return;
    const speed = Number(el.dataset.marquee) || 34;
    const dir = el.dataset.marqueeDir === "rtl" ? 1 : -1;
    // O trilho é duplicado no HTML, então -50% é exatamente uma volta.
    gsap.to(track, {
      xPercent: dir * 50,
      duration: speed,
      ease: "none",
      repeat: -1,
    });
  });
}

/* =========================================================================
   Boot
   ========================================================================= */

function boot() {
  if (reduced) {
    settleStatic();
    initAccordion();
    initGalleryFilter();
    initLightbox();
    return;
  }

  initScroll();
  initNav();
  initReveals();
  initParallax();
  initCounters();
  initProgress();
  initHorizontal();
  initMagnetic();
  initTilt();
  initMouseGlow();
  initContextCursor();
  initGalleryFilter();
  initLightbox();
  initAccordion();
  initHoverIndex();
  initMarquee();

  // O split só é confiável depois que a fonte real carregou — antes disso a
  // quebra de linha é medida na fonte de fallback e sai errada.
  document.fonts.ready.then(() => {
    initSplitText();
    initScrubText();
    watchResplit();
    ScrollTrigger.refresh();
  });

  window.addEventListener("load", () => ScrollTrigger.refresh());
}

boot();
