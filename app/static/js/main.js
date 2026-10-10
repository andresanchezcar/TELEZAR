(function () {
  "use strict";

  var navToggle = document.getElementById("nav-toggle");
  var mainNav = document.getElementById("main-nav");

  if (navToggle && mainNav) {
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
})();