(function () {
  "use strict";

  var sidebar = document.getElementById("sidebar");
  var toggle = document.getElementById("sidebar-toggle");
  var overlay = document.getElementById("sidebar-overlay");

  if (sidebar && toggle) {
    var openSidebar = function () {
      sidebar.classList.add("open");
      if (overlay) overlay.classList.add("show");
    };
    var closeSidebar = function () {
      sidebar.classList.remove("open");
      if (overlay) overlay.classList.remove("show");
    };

    toggle.addEventListener("click", function () {
      if (sidebar.classList.contains("open")) closeSidebar();
      else openSidebar();
    });

    if (overlay) overlay.addEventListener("click", closeSidebar); 

    sidebar.querySelectorAll(".side-link").forEach(function (link) {
      link.addEventListener("click", function () {
        if (window.innerWidth <= 960) closeSidebar();
      });
    });
  }

  document.querySelectorAll(".flash-close").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var flash = btn.closest(".flash");
      if (flash) flash.remove();
    });
  });
})();