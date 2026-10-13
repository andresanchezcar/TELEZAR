(function () {
  "use strict";

  var sidebar = document.getElementById("sidebar");
  var toggle = document.getElementById("sidebar-toggle");
  var overlay = document.getElementById("sidebar-overlay");

  if (sidebar && toggle) {
    var openSidebar = function () {
      sidebar.classList.add("open");
      document.body.classList.add("sidebar-open");
      if (overlay) overlay.classList.add("show");
    };
    var closeSidebar = function () {
      sidebar.classList.remove("open");
      document.body.classList.remove("sidebar-open");
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

  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (!window.confirm(form.getAttribute("data-confirm"))) {
        event.preventDefault();
      }
    });
  });

  var conditionalFields = document.querySelectorAll("[data-show-if]");
  if (conditionalFields.length) {
    var form = conditionalFields[0].closest("form") || document;

    var applyConditions = function () {
      conditionalFields.forEach(function (block) {
        var rules;
        try {
          rules = JSON.parse(block.getAttribute("data-show-if"));
        } catch (e) {
          return;
        }
        var visible = Object.keys(rules).every(function (name) {
          var control = form.querySelector('[name="' + name + '"]');
          if (!control) return true;
          var allowed = rules[name];
          if (!Array.isArray(allowed)) allowed = [allowed];
          return allowed.indexOf(control.value) !== -1;
        });
        block.classList.toggle("is-hidden", !visible);
      });
    };

    form.addEventListener("change", applyConditions);
    applyConditions();
  }
})();