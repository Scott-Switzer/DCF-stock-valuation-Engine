// Football-field bars and markers are sized from data attributes because the
// CSP (style-src 'self') blocks inline style="" attributes. Setting element
// style properties from script is allowed by that policy.
(function () {
  "use strict";
  function apply() {
    document.querySelectorAll("[data-width]").forEach(function (el) {
      el.style.width = el.dataset.width;
    });
    document.querySelectorAll("[data-left]").forEach(function (el) {
      el.style.left = el.dataset.left;
    });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", apply);
  } else {
    apply();
  }
})();
