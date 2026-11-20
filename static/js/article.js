/*
  Artículo: controles de lectura. Vanilla, sin dependencias.

  - Tamaño de texto: entero de min a max (data-size-* en #reader), guardado en
    localStorage. El script en línea del <head> ya lo aplicó antes del primer
    pintado; acá se actualizan los botones y el valor, y se guardan cambios.
    En los extremos el botón queda con aria-disabled (no disabled: un botón
    deshabilitado pierde el foco, y dentro del panel el foco se perdería).
  - Compartir: copiar el link (cambia a «Copiado» 1,6 s y avisa con
    window.blogToast) y el menú nativo si existe navigator.share.
  - Índice: marca la sección que se está leyendo (ver «Índice que sigue al
    scroll» más abajo).
  - Panel inferior (mobile): lo abre el botón flotante. Velo, tirador y Esc lo
    cierran; el foco queda atrapado adentro y vuelve al botón al cerrar. Un
    link del índice cierra el panel y deja que el navegador lleve a la sección.
    Requiere dialog.js (window.blogDialog), que base.html carga antes.

  Sin textos escritos: salen de data-attributes que pone el template.
*/
(function () {
  "use strict";

  var COPIED_MS = 1600;
  var DESKTOP = window.matchMedia("(min-width: 768px)");

  var root = document.documentElement;
  var reader = document.getElementById("reader");
  if (!reader) return;
  var data = reader.dataset;

  // — Tamaño de texto —

  var sizeMin = parseInt(data.sizeMin, 10);
  var sizeMax = parseInt(data.sizeMax, 10);
  var sizeDefault = parseInt(data.sizeDefault, 10);
  var sizeKey = data.sizeKey;
  var sizeValue = reader.querySelector("[data-size-value]");
  var sizeButtons = reader.querySelectorAll("[data-size-step]");

  function storedSize() {
    try {
      var n = parseInt(localStorage.getItem(sizeKey), 10);
      if (n >= sizeMin && n <= sizeMax) return n;
    } catch (e) {}
    return sizeDefault;
  }

  var size = storedSize();

  function renderSize() {
    root.style.setProperty("--prose-size", size + "px");
    if (sizeValue) sizeValue.textContent = String(size);
    Array.prototype.forEach.call(sizeButtons, function (button) {
      var step = parseInt(button.dataset.sizeStep, 10);
      var atLimit = step < 0 ? size <= sizeMin : size >= sizeMax;
      if (atLimit) button.setAttribute("aria-disabled", "true");
      else button.removeAttribute("aria-disabled");
    });
  }

  function setSize(next) {
    next = Math.min(sizeMax, Math.max(sizeMin, next));
    if (next === size) return;
    size = next;
    renderSize();
    try {
      if (size === sizeDefault) localStorage.removeItem(sizeKey);
      else localStorage.setItem(sizeKey, String(size));
    } catch (e) {}
  }

  Array.prototype.forEach.call(sizeButtons, function (button) {
    button.addEventListener("click", function () {
      if (button.getAttribute("aria-disabled") === "true") return;
      setSize(size + parseInt(button.dataset.sizeStep, 10));
      // Otro tamaño mueve los títulos: el índice vuelve a mirar dónde está.
      if (sections.length && !frame) frame = window.requestAnimationFrame(markCurrent);
    });
  });

  renderSize();

  // — Compartir —

  function pageUrl() {
    return window.location.origin + window.location.pathname;
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    // Respaldo para contextos sin la API (http en una red local, por ejemplo).
    return new Promise(function (resolve, reject) {
      var field = document.createElement("textarea");
      field.value = text;
      field.setAttribute("readonly", "");
      field.style.position = "fixed";
      field.style.opacity = "0";
      (reader.contains(document.activeElement) ? reader : document.body).appendChild(field);
      var focused = document.activeElement;
      field.select();
      var ok = false;
      try { ok = document.execCommand("copy"); } catch (e) {}
      field.remove();
      if (focused && focused.focus) focused.focus();
      if (ok) resolve(); else reject(new Error("copy"));
    });
  }

  var copyButton = reader.querySelector("[data-copy-link]");
  if (copyButton) {
    var copyIcon = copyButton.querySelector("[data-copy-icon]");
    var copyText_ = copyButton.querySelector("[data-copy-text]");
    var copyTimer = null;

    copyButton.addEventListener("click", function () {
      copyText(pageUrl()).then(function () {
        copyText_.textContent = data.copiedLabel;
        copyIcon.classList.replace("ph-link", "ph-check");
        clearTimeout(copyTimer);
        copyTimer = setTimeout(function () {
          copyText_.textContent = data.copyLabel;
          copyIcon.classList.replace("ph-check", "ph-link");
        }, COPIED_MS);
        if (window.blogToast) window.blogToast.success(data.copiedMessage);
      }, function () {
        if (window.blogToast) window.blogToast.error(data.copyFailed);
      });
    });
  }

  var nativeShare = reader.querySelector("[data-native-share]");
  if (nativeShare && typeof navigator.share === "function") {
    nativeShare.hidden = false;
    nativeShare.addEventListener("click", function () {
      navigator.share({ title: data.shareTitle, url: pageUrl() }).catch(function () {
        // AbortError: el lector cerró el menú. Nada que avisar.
      });
    });
  }

  // — Índice que sigue al scroll —
  // Marca con aria-current la entrada de la sección que se está leyendo: la
  // del último h2 del índice que ya pasó la línea de lectura (READING_LINE
  // de la ventana desde arriba). Antes del primer título, ninguna; al llegar
  // al final de la página, la última, aunque su título no llegue a la línea.
  // Un solo marcado sirve al lateral de desktop y al panel de mobile, así que
  // al abrir el panel la sección actual ya está marcada.
  // Al tocar una entrada se marca enseguida, y la marca se sostiene mientras
  // dura el salto a la sección: el navegador puede no llevar el título hasta
  // la línea (las secciones del final), y no tiene que ganar la de al lado.
  // Se suelta con el próximo scroll del lector.
  // El estilo de entradas inactivas solo rige con .reader-toc--spy, que pone
  // este script: sin JavaScript el índice es una lista de links común.

  var READING_LINE = 0.3;
  var JUMP_QUIET_MS = 200; // sin scroll durante este tiempo, el salto terminó

  var tocList = reader.querySelector(".reader-toc");
  var sections = [];
  Array.prototype.forEach.call(reader.querySelectorAll("[data-reader-toc]"), function (link) {
    var id;
    try { id = decodeURIComponent(link.hash.slice(1)); } catch (e) { id = link.hash.slice(1); }
    var heading = id && document.getElementById(id);
    if (heading) sections.push({ link: link, heading: heading });
  });

  var active = null;
  var pinned = null;    // entrada tocada, sostenida durante el salto
  var lastScroll = 0;   // último scroll mientras hay una entrada sostenida
  var frame = 0;

  function setActive(section) {
    if (section === active) return;
    if (active) active.link.removeAttribute("aria-current");
    active = section;
    if (active) active.link.setAttribute("aria-current", "location");
  }

  function sectionInView() {
    var doc = document.documentElement;
    var bottom = window.scrollY + window.innerHeight;
    if (window.scrollY > 0 && doc.scrollHeight > window.innerHeight && bottom >= doc.scrollHeight - 2) {
      return sections[sections.length - 1];
    }
    var line = window.innerHeight * READING_LINE;
    var found = null;
    for (var i = 0; i < sections.length; i++) {
      if (sections[i].heading.getBoundingClientRect().top > line) break;
      found = sections[i];
    }
    return found;
  }

  function markCurrent() {
    frame = 0;
    if (!pinned) setActive(sectionInView());
  }

  function onScroll() {
    if (pinned) {
      var now = performance.now();
      var jumping = now - lastScroll < JUMP_QUIET_MS;
      lastScroll = now;
      if (jumping) return;
      pinned = null;
    }
    if (!frame) frame = window.requestAnimationFrame(markCurrent);
  }

  function pin(section) {
    pinned = section;
    lastScroll = performance.now();
    setActive(section);
  }

  if (sections.length) {
    tocList.classList.add("reader-toc--spy");
    sections.forEach(function (section) {
      section.link.addEventListener("click", function () { pin(section); });
    });
    // La rueda, un toque o una tecla son del lector: sueltan la entrada
    // sostenida (la marca se recalcula con el scroll que provoquen).
    ["wheel", "touchstart", "keydown"].forEach(function (type) {
      window.addEventListener(type, function () { pinned = null; }, { passive: true });
    });
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", function () {
      if (!frame) frame = window.requestAnimationFrame(markCurrent);
    });

    // Con el ancla de una sección en la URL (al llegar, con atrás y
    // adelante, o con el «#» de un título), esa queda marcada.
    var fromHash = function () {
      return sections.filter(function (s) { return s.link.hash === window.location.hash; })[0];
    };
    window.addEventListener("hashchange", function () {
      var section = fromHash();
      if (section) pin(section);
    });
    if (fromHash()) pin(fromHash());
    else markCurrent();
  }

  // — Panel inferior (mobile) —
  // Foco atrapado, Esc y fondo sin scroll los resuelve blogDialog (dialog.js).

  var openButton = document.querySelector("[data-reader-open]");
  var veil = document.querySelector("[data-reader-veil]");

  var sheet = window.blogDialog.create({
    element: reader,
    setModal: true, // en desktop el mismo <aside> es la columna lateral, no un diálogo
    onOpen: function () {
      reader.setAttribute("tabindex", "-1");
      reader.classList.add("is-open");
      if (veil) veil.classList.add("is-open");
      if (openButton) openButton.setAttribute("aria-expanded", "true");
      reader.scrollTop = 0;
      reader.focus({ preventScroll: true });
      if (sections.length) markCurrent();
    },
    onClose: function () {
      reader.classList.remove("is-open");
      reader.removeAttribute("tabindex");
      if (veil) veil.classList.remove("is-open");
      if (openButton) openButton.setAttribute("aria-expanded", "false");
    },
  });

  if (openButton) {
    openButton.addEventListener("click", function () {
      if (sheet.isOpen()) sheet.close();
      else if (!DESKTOP.matches) sheet.open(openButton);
    });
  }
  if (veil) veil.addEventListener("click", function () { sheet.close(); });

  var handle = reader.querySelector("[data-reader-close]");
  if (handle) handle.addEventListener("click", function () { sheet.close(); });

  // Un link del índice cierra el panel sin devolver el foco al botón: el
  // navegador lleva a la sección y el foco sigue desde ahí. Se cierra antes
  // de la navegación, así el fondo ya puede scrollear.
  Array.prototype.forEach.call(reader.querySelectorAll("[data-reader-toc]"), function (link) {
    link.addEventListener("click", function () { sheet.close(false); });
  });

  // Al pasar a desktop el panel deja de existir: se cierra sin mover el foco.
  var onBreakpoint = function (event) { if (event.matches) sheet.close(false); };
  if (DESKTOP.addEventListener) DESKTOP.addEventListener("change", onBreakpoint);
  else if (DESKTOP.addListener) DESKTOP.addListener(onBreakpoint);
})();
