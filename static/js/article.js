/*
  Artículo: controles de lectura. Vanilla, sin dependencias.

  - Tamaño de texto: entero de min a max (data-size-* en #reader), guardado en
    localStorage. El script en línea del <head> ya lo aplicó antes del primer
    pintado; acá se actualizan los botones y el valor, y se guardan cambios.
    En los extremos el botón queda con aria-disabled (no disabled: un botón
    deshabilitado pierde el foco, y dentro del panel el foco se perdería).
  - Compartir: copiar el link (cambia a «Copiado» 1,6 s y avisa con
    window.blogToast) y el menú nativo si existe navigator.share.
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
