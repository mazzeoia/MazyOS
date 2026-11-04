// Motor compartilhado dos demos animados das páginas de serviço.
//
// Os 4 componentes (AutomacaoChatDemo, PresencaDigitalDemo,
// InteligenciaDashboardDemo, EngenhariaSystemDemo) descrevem a própria
// animação como uma lista de quadros — `{ wait, run }` — e este módulo cuida
// do que é igual entre eles: ligar só quando o painel entra na viewport,
// parar e rebobinar quando sai (ou quando a aba perde o foco), reiniciar em
// loop, e colapsar tudo para um estado final estático sob
// `prefers-reduced-motion` (baseline de acessibilidade do design-guide §6,
// não exceção).

export interface CountUpOptions {
  duration?: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
}

export interface DemoCtx {
  /** setTimeout cancelável — morre junto com o demo ao sair da viewport. */
  after(ms: number, fn: () => void): void;
  /** Escreve `text` em `el` caractere a caractere. Retorna a duração total. */
  type(el: HTMLElement, text: string, speed?: number): number;
  /** Anima um número de 0 até `to`, formatado em pt-BR. */
  countUp(el: HTMLElement, to: number, opts?: CountUpOptions): void;
}

export interface Frame {
  /** Espera, em ms, ANTES de executar este quadro. */
  wait?: number;
  run?: (ctx: DemoCtx) => void;
}

export interface DemoOptions {
  /** Volta o demo ao estado inicial. Chamado antes de cada volta do loop. */
  reset: () => void;
  frames: Frame[];
  /** Pausa antes de reiniciar, em ms. */
  loopPause?: number;
  /** Fração do painel visível necessária para ligar. */
  threshold?: number;
}

// Mesmo easing do resto do sistema (--ease-out), aqui em JS para o count-up.
const easeOut = (t: number) => 1 - Math.pow(1 - t, 3);

function format(value: number, o: CountUpOptions) {
  const decimals = o.decimals ?? 0;
  const n = value.toLocaleString("pt-BR", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
  return `${o.prefix ?? ""}${n}${o.suffix ?? ""}`;
}

export function mountDemo(root: Element, options: DemoOptions): void {
  const { reset, frames, loopPause = 2400, threshold = 0.3 } = options;

  // Sem motion: nenhum loop, nenhum timer. O demo renderiza direto no estado
  // final rodando os mesmos quadros com um contexto que resolve na hora — o
  // conteúdo continua todo legível, só a coreografia some.
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    const still: DemoCtx = {
      after: (_ms, fn) => fn(),
      type: (el, text) => {
        el.textContent = text;
        return 0;
      },
      countUp: (el, to, o = {}) => {
        el.textContent = format(to, o);
      },
    };
    reset();
    for (const frame of frames) frame.run?.(still);
    return;
  }

  const timeouts = new Set<number>();
  const rafs = new Set<number>();
  let playing = false;

  const after = (ms: number, fn: () => void) => {
    const id = window.setTimeout(() => {
      timeouts.delete(id);
      fn();
    }, ms);
    timeouts.add(id);
  };

  const clearTimers = () => {
    for (const id of timeouts) window.clearTimeout(id);
    timeouts.clear();
    for (const id of rafs) cancelAnimationFrame(id);
    rafs.clear();
  };

  const type: DemoCtx["type"] = (el, text, speed = 45) => {
    el.textContent = "";
    for (let i = 1; i <= text.length; i += 1) {
      after(i * speed, () => {
        el.textContent = text.slice(0, i);
      });
    }
    return text.length * speed;
  };

  const countUp: DemoCtx["countUp"] = (el, to, o = {}) => {
    const duration = o.duration ?? 1400;
    const start = performance.now();
    let id = 0;
    const step = (now: number) => {
      rafs.delete(id);
      const t = Math.min(1, (now - start) / duration);
      el.textContent = format(to * easeOut(t), o);
      if (t < 1) {
        id = requestAnimationFrame(step);
        rafs.add(id);
      }
    };
    id = requestAnimationFrame(step);
    rafs.add(id);
  };

  const ctx: DemoCtx = { after, type, countUp };

  const play = (i: number) => {
    if (!playing) return;
    if (i >= frames.length) {
      after(loopPause, () => {
        reset();
        play(0);
      });
      return;
    }
    const frame = frames[i];
    after(frame.wait ?? 0, () => {
      frame.run?.(ctx);
      play(i + 1);
    });
  };

  const start = () => {
    if (playing) return;
    playing = true;
    reset();
    play(0);
  };

  const stop = () => {
    if (!playing) return;
    playing = false;
    clearTimers();
    reset();
  };

  const isInView = () => {
    const r = root.getBoundingClientRect();
    return r.top < window.innerHeight && r.bottom > 0;
  };

  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) start();
        else stop();
      }
    },
    { threshold },
  );
  observer.observe(root);

  // Aba em segundo plano: os timers continuariam correndo e o usuário voltaria
  // no meio da sequência. Rebobina e retoma só se o painel ainda estiver à vista.
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) stop();
    else if (isInView()) start();
  });
}
