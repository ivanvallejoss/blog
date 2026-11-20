/*
  Comportamiento común de los diálogos modales del blog (búsqueda, panel de
  lectura del artículo). Vanilla, sin dependencias, sin textos.

    var dialog = blogDialog.create({
      element,      // el elemento que hace de diálogo: el foco queda adentro
      setModal,     // true: pone role="dialog" y aria-modal al abrir y los saca
                    // al cerrar (para un elemento que no siempre es diálogo)
      onOpen,       // () → mostrar el diálogo (clases, hidden…)
      onClose,      // () → ocultarlo
    });
    dialog.open(opener)        opener recibe el foco al cerrar
    dialog.close(returnFocus)  returnFocus === false: no lo devuelve
    dialog.isOpen()

  Mientras está abierto:
    - Esc cierra.
    - Tab y Mayús+Tab recorren los controles del diálogo en el orden en que se
      ven (no el del marcado) y vuelven al principio: el foco no sale.
    - Si el foco sale por otro camino (lector de pantalla, clic), vuelve.
      Los toasts (#toasts) quedan afuera de esa regla y entran en el recorrido:
      su acción («Reintentar») tiene que poder usarse con el diálogo abierto.
    - <html> lleva .dialog-open: el fondo no scrollea (blog.css).
  Abrir un diálogo cierra el que estuviera abierto.
*/
(function () {
  "use strict";

  var FOCUSABLE = "a[href], button:not([disabled]), input:not([disabled]), select, textarea, [tabindex]:not([tabindex='-1'])";
  var current = null;

  function visible(el) {
    return !el.hidden && el.getClientRects().length > 0;
  }

  function visualOrder(items) {
    return items
      .map(function (el) { return { el: el, box: el.getBoundingClientRect() }; })
      .sort(function (a, b) {
        return Math.abs(a.box.top - b.box.top) > 1 ? a.box.top - b.box.top : a.box.left - b.box.left;
      })
      .map(function (item) { return item.el; });
  }

  function create(options) {
    var element = options.element;
    var opener = null;
    var isOpen = false;

    function focusables() {
      var own = Array.prototype.filter.call(element.querySelectorAll(FOCUSABLE), visible);
      var toasts = document.getElementById("toasts");
      var extra = toasts ? Array.prototype.filter.call(toasts.querySelectorAll(FOCUSABLE), visible) : [];
      return visualOrder(own).concat(extra);
    }

    function inside(node) {
      var toasts = document.getElementById("toasts");
      return element.contains(node) || (toasts && toasts.contains(node));
    }

    function onKeydown(event) {
      if (event.key === "Escape") {
        event.preventDefault();
        api.close();
        return;
      }
      if (event.key !== "Tab") return;
      event.preventDefault();
      var items = focusables();
      if (!items.length) return;
      var index = items.indexOf(document.activeElement);
      var next;
      if (index === -1) next = event.shiftKey ? items[items.length - 1] : items[0];
      else next = items[(index + (event.shiftKey ? -1 : 1) + items.length) % items.length];
      next.focus();
    }

    function onFocusin(event) {
      if (!inside(event.target)) {
        var items = focusables();
        (items[0] || element).focus({ preventScroll: true });
      }
    }

    var api = {
      open: function (from) {
        if (isOpen) return;
        if (current && current !== api) current.close(false);
        current = api;
        isOpen = true;
        opener = from || document.activeElement;
        if (options.setModal) {
          element.setAttribute("role", "dialog");
          element.setAttribute("aria-modal", "true");
        }
        if (options.onOpen) options.onOpen();
        document.documentElement.classList.add("dialog-open");
        document.addEventListener("keydown", onKeydown);
        document.addEventListener("focusin", onFocusin);
      },
      close: function (returnFocus) {
        if (!isOpen) return;
        isOpen = false;
        if (current === api) current = null;
        document.removeEventListener("keydown", onKeydown);
        document.removeEventListener("focusin", onFocusin);
        document.documentElement.classList.remove("dialog-open");
        if (options.setModal) {
          element.removeAttribute("role");
          element.removeAttribute("aria-modal");
        }
        if (options.onClose) options.onClose();
        if (returnFocus !== false && opener && opener.isConnected && opener.focus) {
          opener.focus({ preventScroll: true });
        }
        opener = null;
      },
      isOpen: function () { return isOpen; },
    };
    return api;
  }

  window.blogDialog = { create: create };
})();
