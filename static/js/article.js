/* Progreso de lectura + sección activa. Vanilla, sin dependencias.
   Sin JS el artículo se lee completo: se pierden la barra y el resaltado. */

(function () {
  const article = document.querySelector('[data-article]');
  if (!article) return;

  const fills = document.querySelectorAll('[data-progress]');
  const links = document.querySelectorAll('[data-toc-link]');
  const counter = document.querySelector('[data-toc-counter]');

  /* --- barra de progreso ------------------------------------------------- */

  let ticking = false;

  function updateProgress() {
    ticking = false;
    const top = article.getBoundingClientRect().top + window.scrollY;
    const span = article.offsetHeight - window.innerHeight;
    const ratio = span <= 0 ? 1 : (window.scrollY - top) / span;
    const pct = Math.min(1, Math.max(0, ratio)) * 100;
    fills.forEach(function (fill) { fill.style.width = pct.toFixed(2) + '%'; });
  }

  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(updateProgress);
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  updateProgress();

  /* --- sección activa ----------------------------------------------------- */

  const headings = article.querySelectorAll('.prose h2[id], .prose h3[id]');
  if (!headings.length || !('IntersectionObserver' in window)) return;

  const total = String(links.length).padStart(2, '0');

  function setActive(id) {
    let index = 0;
    links.forEach(function (link, i) {
      const on = link.dataset.tocLink === id;
      link.classList.toggle('is-active', on);
      /* aria-current es lo que hace que el estado exista para un lector de
         pantalla: la clase y el borde son sólo visuales. */
      if (on) {
        link.setAttribute('aria-current', 'true');
        index = i + 1;
      } else {
        link.removeAttribute('aria-current');
      }
    });
    if (counter && index) {
      counter.textContent = String(index).padStart(2, '0') + ' / ' + total;
    }
  }

  const observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) setActive(entry.target.id);
    });
  }, { rootMargin: '-20% 0px -70% 0px' });

  headings.forEach(function (heading) { observer.observe(heading); });
})();