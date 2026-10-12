(function () {
  "use strict";

  var navToggle = document.getElementById("nav-toggle");
  var mainNav = document.getElementById("main-nav");

  if (navToggle && mainNav) {
    var closeNav = function () {
      mainNav.classList.remove("open");
      navToggle.classList.remove("is-open");
      navToggle.setAttribute("aria-expanded", "false");
    };

    navToggle.addEventListener("click", function () {
      var open = mainNav.classList.toggle("open");
      navToggle.classList.toggle("is-open", open);
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });

    mainNav.querySelectorAll(".has-sub > a").forEach(function (link) {
      link.addEventListener("click", function (e) {
        if (window.innerWidth <= 1020) {
          e.preventDefault();
          link.parentElement.classList.toggle("open");
        }
      });
    });

    mainNav.querySelectorAll("a").forEach(function (link) {
      if (link.parentElement.classList.contains("has-sub")) return;
      link.addEventListener("click", function () {
        if (window.innerWidth <= 1020) closeNav();
      });
    });
  }

  var header = document.getElementById("site-header");
  if (header) {
    var onScroll = function () {
      header.classList.toggle("scrolled", window.scrollY > 10);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  document.querySelectorAll(".toast-close").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var toast = btn.closest(".toast");
      if (toast) toast.remove();
    });
  });

  var galleryItems = document.querySelectorAll(".gallery-item");
  if (galleryItems.length) {
    var lightbox = document.createElement("div");
    lightbox.className = "lightbox";
    lightbox.innerHTML =
      '<button class="lightbox-close" aria-label="Cerrar">&times;</button>' +
      '<img class="lightbox-img" src="" alt="">';
    document.body.appendChild(lightbox);

    var lightboxImg = lightbox.querySelector(".lightbox-img");

    var closeLightbox = function () {
      lightbox.classList.remove("show");
    };

    galleryItems.forEach(function (item) {
      item.addEventListener("click", function () {
        var img = item.querySelector("img");
        if (img) {
          lightboxImg.src = img.src;
          lightbox.classList.add("show");
        }
      });
    });

    lightbox.querySelector(".lightbox-close").addEventListener("click", closeLightbox);
    lightbox.addEventListener("click", function (e) {
      if (e.target === lightbox) closeLightbox();
    });
  }

  var storageGet = function (store, key) {
    try {
      return window[store].getItem(key);
    } catch (e) {
      return null;
    }
  };

  var storageSet = function (store, key) {
    try {
      window[store].setItem(key, "1");
    } catch (e) {
      /* almacenamiento no disponible */
    }
  };

  document.querySelectorAll("[data-modal]").forEach(function (modal) {
    var frequency = modal.getAttribute("data-frequency") || "session";
    var key = "telezar_" + (modal.getAttribute("data-key") || "modal");
    var delay = parseInt(modal.getAttribute("data-delay") || "0", 10) * 1000;

    if (frequency === "once" && storageGet("localStorage", key)) return;
    if (frequency === "session" && storageGet("sessionStorage", key)) return;

    var open = function () {
      modal.classList.add("show");
      if (frequency === "once") storageSet("localStorage", key);
      else if (frequency === "session") storageSet("sessionStorage", key);
    };

    var close = function () {
      modal.classList.remove("show");
    };

    setTimeout(open, isNaN(delay) || delay < 0 ? 0 : delay);

    modal.querySelectorAll("[data-modal-close]").forEach(function (btn) {
      btn.addEventListener("click", close);
    });
    modal.addEventListener("click", function (e) {
      if (e.target === modal) close();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") close();
    });
  });
})();