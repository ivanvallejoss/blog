/*
  Estado de carga de los pedidos de HTMX. Vanilla, sin dependencias.

  Mientras hay un pedido en curso:
  - <html> lleva la clase .is-loading (muestra la barra de 2px de arriba);
  - el destino del swap lleva aria-busy="true" (baja al 40 % por CSS).
  HTMX ya le pone .htmx-request al elemento que disparó el pedido (el filtro
  activo muestra el ícono girando por CSS).
*/
(function () {
  "use strict";

  var pending = 0;
  var root = document.documentElement;

  function start(event) {
    pending += 1;
    root.classList.add("is-loading");
    var target = event.detail && event.detail.target;
    if (target) target.setAttribute("aria-busy", "true");
  }

  function end(event) {
    pending = Math.max(0, pending - 1);
    if (pending === 0) root.classList.remove("is-loading");
    // Con swap outerHTML el destino viejo ya no está y el nuevo llega sin
    // aria-busy; si el pedido falló, el viejo sigue y hay que limpiarlo.
    var target = event.detail && event.detail.target;
    if (target) target.removeAttribute("aria-busy");
  }

  document.addEventListener("htmx:beforeRequest", start);
  document.addEventListener("htmx:afterRequest", end);
})();
