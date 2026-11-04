const reduceMotion = window.matchMedia(
  "(prefers-reduced-motion: reduce)",
).matches;

if (!reduceMotion) {
  const el = document.getElementById("process-line");

  if (el) {
    const updateProgress = () => {
      const rect = el.getBoundingClientRect();
      const vh = window.innerHeight;
      // Progresso 0→1 conforme a seção atravessa o meio da viewport
      const raw = (vh * 0.75 - rect.top) / (rect.height * 0.85);
      const progress = Math.min(1, Math.max(0, raw));
      el.style.setProperty("--line-progress", String(progress));
    };

    window.addEventListener("app:scroll", updateProgress, { passive: true });
    window.addEventListener("scroll", updateProgress, { passive: true });
    window.addEventListener("resize", updateProgress);
    updateProgress();
  }
}
