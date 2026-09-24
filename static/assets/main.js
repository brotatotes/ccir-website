/* Christian Church In Raleigh — tiny progressive-enhancement script.
   No dependencies. Everything degrades gracefully without JS. */
(function () {
  "use strict";

  /* ---- mobile nav toggle ---- */
  var toggle = document.querySelector(".nav-toggle");
  var menu = document.getElementById("nav-menu");
  if (toggle && menu) {
    toggle.addEventListener("click", function () {
      var open = menu.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    menu.addEventListener("click", function (e) {
      if (e.target.tagName === "A") {
        menu.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* ---- lite YouTube facade: click loads the real iframe ----
     Keeps the page fast and avoids loading YouTube until asked. */
  function activate(btn) {
    var id = btn.getAttribute("data-yt");
    if (!id) return;
    var title = btn.getAttribute("data-title") || "YouTube video";
    var iframe = document.createElement("iframe");
    iframe.setAttribute("title", title);
    iframe.setAttribute("allow", "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share");
    iframe.setAttribute("allowfullscreen", "");
    iframe.setAttribute("loading", "lazy");
    iframe.src = "https://www.youtube-nocookie.com/embed/" + id + "?autoplay=1&rel=0";
    btn.innerHTML = "";
    btn.appendChild(iframe);
    btn.classList.add("is-active");
    var f = iframe;
    f.focus && f.focus();
  }
  document.querySelectorAll(".video-embed[data-yt]").forEach(function (btn) {
    btn.addEventListener("click", function () { activate(btn); });
    btn.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); activate(btn); }
    });
  });

  /* ---- footer year ---- */
  var y = document.getElementById("year");
  if (y) y.textContent = new Date().getFullYear();
})();
