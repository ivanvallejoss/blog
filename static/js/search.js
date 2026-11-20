/*
  Búsqueda del cliente (README §6 M4/D4). Vanilla, sin dependencias, sin textos:
  los pone partials/search.html en data-attributes.

  Hasta que se abre no hace nada más que escuchar tres cosas:
    - clic en cualquier [data-search-open];
    - ⌘K / Ctrl+K;
    - envío de un formulario [data-search-form] (la 404): abre con lo escrito.
  También: window.blogSearch.open(texto, elementoQueAbre).

  La primera vez que se abre pide /search.json y lo guarda en memoria. Si
  falla, toast de fallo con «Reintentar». Filtra por inclusión sobre título,
  tema y bajada, sin distinguir mayúsculas ni tildes.

  Teclado (patrón combobox con lista): el foco queda en el campo; ↑↓ mueven
  el resultado activo (aria-activedescendant), que se mantiene a la vista;
  Enter lo abre. Esc, el velo y «Cancelar» cierran (dialog.js atrapa el foco,
  lo devuelve al cerrar y bloquea el scroll del fondo).
*/
(function () {
  "use strict";

  var STATUS_DELAY_MS = 500;
  var root = document.getElementById("search");
  if (!root || !window.blogDialog) return;

  var data = root.dataset;
  var panel = root.querySelector(".search__panel");
  var input = root.querySelector("#search-input");
  var body = root.querySelector("[data-search-body]");
  var list = root.querySelector("#search-results");
  var count = root.querySelector("[data-search-count]");
  var noneTitle = root.querySelector("[data-search-none-title]");
  var chips = root.querySelector("[data-search-chips]");
  var status = root.querySelector("[data-search-status]");
  var optionTemplate = document.getElementById("search-option-template");
  var chipTemplate = document.getElementById("search-chip-template");

  var posts = null;    // índice, una vez cargado
  var loading = null;  // pedido en curso
  var options = [];    // <a role=option> visibles, en orden
  var active = -1;
  var statusTimer = null;

  var dialog = window.blogDialog.create({
    element: panel,
    onOpen: function () { root.hidden = false; },
    onClose: function () {
      root.hidden = true;
      root.classList.remove("uses-keys");
      clearTimeout(statusTimer);
      status.textContent = "";
    },
  });

  // — Texto —

  function norm(text) {
    return String(text || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  }

  function plural(n) {
    var template = n === 0 ? data.resultsNone : n === 1 ? data.resultsOne : data.resultsMany;
    return template.replace("{n}", String(n));
  }

  // — Índice —

  function load() {
    if (posts) return;
    if (loading) return;
    root.dataset.state = "loading";
    loading = fetch(data.indexUrl, { headers: { Accept: "application/json" } })
      .then(function (response) {
        if (!response.ok) throw new Error(String(response.status));
        return response.json();
      })
      .then(function (entries) {
        posts = entries.map(function (entry) {
          entry.haystack = norm(entry.title + " " + entry.category + " " + entry.excerpt);
          return entry;
        });
        renderChips();
        loading = null;
        render();
      })
      .catch(function () {
        loading = null;
        if (window.blogToast) {
          window.blogToast.error(data.failed, {
            actionLabel: data.retry,
            onAction: function () { if (dialog.isOpen()) load(); },
          });
        }
      });
  }

  // Temas para las etiquetas: los del índice, de más a menos posts.
  function renderChips() {
    var byName = {};
    posts.forEach(function (post) { byName[post.category] = (byName[post.category] || 0) + 1; });
    var names = Object.keys(byName).sort(function (a, b) {
      return byName[b] - byName[a] || a.localeCompare(b);
    });
    chips.textContent = "";
    names.forEach(function (name) {
      var chip = chipTemplate.content.firstElementChild.cloneNode(true);
      chip.textContent = name;
      chip.addEventListener("click", function () {
        input.value = name;
        render();
        input.focus();
      });
      chips.appendChild(chip);
    });
  }

  // — Resultados —

  function render() {
    if (!posts) return;
    var raw = input.value.trim();
    var query = norm(raw);
    var results = query
      ? posts.filter(function (post) { return post.haystack.indexOf(query) !== -1; })
      : posts;

    var state = !query ? "idle" : results.length ? "results" : "none";
    root.dataset.state = state;
    count.textContent = query ? plural(results.length) : data.allPosts;
    noneTitle.textContent = data.noResults.replace("{q}", raw);

    list.textContent = "";
    options = results.map(function (post, index) {
      var option = optionTemplate.content.firstElementChild.cloneNode(true);
      option.id = "search-option-" + index;
      option.href = post.url;
      option.querySelector(".search-option__title").textContent = post.title;
      option.querySelector(".search-option__date").textContent = post.date_label;
      option.querySelector(".search-option__excerpt").textContent = post.excerpt;
      option.querySelector(".search-option__meta").textContent = post.meta_label;
      list.appendChild(option);
      return option;
    });
    setActive(options.length ? 0 : -1, false);
    announce(query ? (results.length ? plural(results.length) : noneTitle.textContent) : "");
  }

  function listVisible() {
    return list.getClientRects().length > 0 && options.length > 0;
  }

  function setActive(index, reveal) {
    if (active >= 0 && options[active]) options[active].setAttribute("aria-selected", "false");
    active = index;
    var visibleList = listVisible();
    input.setAttribute("aria-expanded", visibleList ? "true" : "false");
    if (active >= 0 && visibleList) {
      options[active].setAttribute("aria-selected", "true");
      input.setAttribute("aria-activedescendant", options[active].id);
      if (reveal) options[active].scrollIntoView({ block: "nearest" });
    } else {
      input.removeAttribute("aria-activedescendant");
    }
  }

  // La cantidad se anuncia con una pausa: no un número por cada tecla.
  function announce(text) {
    clearTimeout(statusTimer);
    statusTimer = setTimeout(function () { status.textContent = text; }, STATUS_DELAY_MS);
  }

  input.addEventListener("input", render);

  input.addEventListener("keydown", function (event) {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      if (!listVisible()) return;
      event.preventDefault();
      root.classList.add("uses-keys");
      var step = event.key === "ArrowDown" ? 1 : -1;
      setActive((active + step + options.length) % options.length, true);
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (listVisible() && active >= 0) window.location.assign(options[active].href);
    }
  });

  // — Abrir y cerrar —

  function open(text, opener) {
    if (!dialog.isOpen()) dialog.open(opener || document.activeElement);
    if (typeof text === "string") input.value = text;
    input.focus();
    if (posts) render(); else load();
    body.scrollTop = 0;
  }

  root.addEventListener("click", function (event) {
    if (event.target.closest("[data-search-close]")) dialog.close();
  });

  document.addEventListener("click", function (event) {
    var trigger = event.target.closest("[data-search-open]");
    if (!trigger) return;
    event.preventDefault();
    open("", trigger);
  });

  document.addEventListener("keydown", function (event) {
    if ((event.metaKey || event.ctrlKey) && !event.altKey && !event.shiftKey && event.key.toLowerCase() === "k") {
      event.preventDefault();
      if (dialog.isOpen()) input.focus();
      else open("", document.activeElement);
    }
  });

  document.addEventListener("submit", function (event) {
    var form = event.target.closest("[data-search-form]");
    if (!form) return;
    event.preventDefault();
    var field = form.querySelector("input");
    open(field ? field.value.trim() : "", field);
  });

  window.blogSearch = { open: open };
})();
