const toggle = document.getElementById("menu-toggle");
const menu = document.getElementById("mobile-menu");

toggle?.addEventListener("click", () => {
  const isHidden = menu?.hasAttribute("hidden");
  if (isHidden) {
    menu?.removeAttribute("hidden");
    toggle.setAttribute("aria-expanded", "true");
  } else {
    menu?.setAttribute("hidden", "");
    toggle.setAttribute("aria-expanded", "false");
  }
});

// Consciência de contraste — observa seções .on-light passando atrás da
// navbar fixa e alterna o vidro entre escuro/claro.
const navbar = document.getElementById("navbar");
const lightSections = document.querySelectorAll<HTMLElement>(".on-light");

if (navbar && lightSections.length && "IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      const anyOnLight = entries.some((e) => e.isIntersecting);
      navbar.classList.toggle("on-light", anyOnLight);
    },
    { rootMargin: "-90px 0px -85% 0px", threshold: 0 },
  );

  lightSections.forEach((el) => observer.observe(el));
}
