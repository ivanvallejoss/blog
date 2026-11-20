/*
  Toasts del blog. Vanilla, sin dependencias.

  API (window.blogToast):
    blogToast.success(message)                         se oculta a los 3 s
    blogToast.error(message, { actionLabel, onAction }) con acción: no se oculta solo
                                                        sin acción: se oculta a los 3 s
    blogToast.show({ type, message, actionLabel, onAction, duration })
  Cada llamada devuelve una función que cierra ese toast.

  El script no tiene textos: el mensaje lo pasa quien llama, y los textos de
  los fallos de HTMX salen de data-attributes que pone el template
  (#toasts[data-error-message], #toasts[data-retry-label] y, en el elemento que
  disparó el pedido o un ancestro, [data-toast-error]).

  Se conecta a htmx:responseError y htmx:sendError: muestra un fallo con
  «Reintentar», que repite el mismo pedido.
*/
(function () {
  "use strict";

  var AUTO_HIDE_MS = 3000;
  var MAX_VISIBLE = 2;
  var ICONS = { success: "ph-check-circle", error: "ph-wifi-slash" };

  function container() {
    return document.getElementById("toasts");
  }

  function show(options) {
    var root = container();
    var template = document.getElementById("toast-template");
    if (!root || !template || !options || !options.message) return function () {};

    var type = options.type === "error" ? "error" : "success";
    var hasAction = Boolean(options.actionLabel && options.onAction);

    // Un mismo fallo no se apila: reemplaza al anterior.
    Array.prototype.forEach.call(root.querySelectorAll(".toast"), function (el) {
      if (el.dataset.message === options.message) el.remove();
    });

    var toast = template.content.firstElementChild.cloneNode(true);
    toast.classList.add("toast--" + type);
    toast.dataset.message = options.message;
    // Los fallos interrumpen; los avisos de éxito se anuncian sin cortar.
    toast.setAttribute("role", type === "error" ? "alert" : "status");
    toast.querySelector(".toast__icon").classList.add(ICONS[type]);
    toast.querySelector(".toast__message").textContent = options.message;

    var timer = null;
    function dismiss() {
      if (timer) clearTimeout(timer);
      toast.remove();
    }

    if (hasAction) {
      var button = document.createElement("button");
      button.type = "button";
      button.className = "btn btn-ghost toast__action";
      button.textContent = options.actionLabel;
      button.addEventListener("click", function () {
        dismiss();
        options.onAction();
      });
      toast.appendChild(button);
    }

    root.appendChild(toast);
    while (root.children.length > MAX_VISIBLE) root.firstElementChild.remove();

    var duration = options.duration != null ? options.duration : AUTO_HIDE_MS;
    if (!(type === "error" && hasAction) && duration > 0) {
      timer = setTimeout(dismiss, duration);
    }
    return dismiss;
  }

  window.blogToast = {
    show: show,
    success: function (message, options) {
      return show(Object.assign({}, options, { type: "success", message: message }));
    },
    error: function (message, options) {
      return show(Object.assign({}, options, { type: "error", message: message }));
    },
  };

  // — Fallos de HTMX —
  function onHtmxError(event) {
    var root = container();
    if (!root) return;
    var elt = event.detail && event.detail.elt;
    var source = elt && elt.closest ? elt.closest("[data-toast-error]") : null;
    var message = (source && source.dataset.toastError) || root.dataset.errorMessage;
    var config = event.detail && event.detail.requestConfig;
    var trigger = config && config.triggeringEvent ? config.triggeringEvent.type : "click";

    window.blogToast.error(message, {
      actionLabel: root.dataset.retryLabel,
      onAction: function () {
        if (elt && elt.isConnected && window.htmx) {
          window.htmx.trigger(elt, trigger);
        } else {
          window.location.reload();
        }
      },
    });
  }

  document.addEventListener("htmx:responseError", onHtmxError);
  document.addEventListener("htmx:sendError", onHtmxError);
})();
