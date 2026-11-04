const reduceMotion = window.matchMedia(
  "(prefers-reduced-motion: reduce)",
).matches;

if (!reduceMotion) {
  const section = document.getElementById("tension-section");
  const network = document.getElementById("network-tension");
  const beats = section
    ? Array.from(section.querySelectorAll<HTMLElement>(".tension-beat"))
    : [];
  const lossGroups: Record<string, string[]> = network
    ? JSON.parse(network.getAttribute("data-loss-groups") || "{}")
    : {};

  function update() {
    if (!section) return;
    const rect = section.getBoundingClientRect();
    const total = rect.height - window.innerHeight;
    const scrolled = Math.min(Math.max(-rect.top, 0), Math.max(total, 1));
    const fraction = total > 0 ? scrolled / total : 0;
    const beatIndex = Math.min(
      beats.length - 1,
      Math.floor(fraction * beats.length),
    );

    // Opacidade calculada direto da posição de scroll a cada frame —
    // sem CSS transition, sem classe intermediária. Isso torna a
    // sobreposição entre beats matematicamente impossível: não existe
    // estado de animação "atrasado" que possa dessincronizar de um
    // scroll rápido (era exatamente essa a causa do bug de blocos
    // sobrepostos — uma transition de 500ms baseada em tempo competindo
    // com um scroll que pode avançar mais rápido que isso).
    beats.forEach((b, i) => {
      const active = i === beatIndex;
      b.style.opacity = active ? "1" : "0";
      b.style.pointerEvents = active ? "auto" : "none";
    });

    if (network) {
      const dark = new Set<string>();
      for (let i = 1; i <= beatIndex + 1; i++) {
        (lossGroups[String(i)] || []).forEach((id) => dark.add(id));
      }
      network.querySelectorAll<SVGElement>("[data-node]").forEach((node) => {
        const id = node.getAttribute("data-node") || "";
        node.classList.toggle("is-dark", dark.has(id));
      });
      network.querySelectorAll<SVGElement>("[data-edge]").forEach((edge) => {
        const [a, b] = (edge.getAttribute("data-edge") || "").split("-");
        edge.classList.toggle("is-dark", dark.has(a) || dark.has(b));
      });
    }
  }

  window.addEventListener("app:scroll", update, { passive: true });
  window.addEventListener("scroll", update, { passive: true });
  window.addEventListener("resize", update);
  update();
}
