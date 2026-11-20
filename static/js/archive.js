/*
  Archivo: mantiene visible el filtro activo en la fila con scroll horizontal
  de mobile. El swap de HTMX reemplaza #archive-filters y la fila vuelve al
  principio; sin esto, el tema elegido podía quedar fuera de la pantalla.
  En desktop los filtros van en columna y esto no mueve nada.
*/
(function () {
  "use strict";

  function revealActiveFilter() {
    var nav = document.getElementById("archive-filters");
    var active = nav && nav.querySelector("[aria-current='page']");
    if (!active || nav.scrollWidth <= nav.clientWidth) return;
    // Solo desplazamiento horizontal dentro de la fila: la página no se mueve.
    var navBox = nav.getBoundingClientRect();
    var box = active.getBoundingClientRect();
    if (box.left < navBox.left || box.right > navBox.right) {
      nav.scrollLeft += box.left - navBox.left - (navBox.width - box.width) / 2;
    }
  }

  document.addEventListener("DOMContentLoaded", revealActiveFilter);
  document.addEventListener("htmx:afterSettle", revealActiveFilter);
})();
