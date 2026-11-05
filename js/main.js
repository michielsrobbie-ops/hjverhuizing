/* HJ Verhuizing - menu, cookiekeuze, formulieren en metingen. Geen externe libraries. */
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
    sget: function (k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } },
    sset: function (k, v) { try { sessionStorage.setItem(k, v); } catch (e) {} },
    sdel: function (k) { try { sessionStorage.removeItem(k); } catch (e) {} }
  };
  var track = function (name, params) { if (typeof window.gtag === "function") window.gtag("event", name, params || {}); };

  /* ---------- menu ---------- */
  var nav = $("#nav"), toggle = $(".menu-toggle");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open);
      document.body.style.overflow = open ? "hidden" : "";
    });
  }
  $$(".sub-toggle").forEach(function (b) {
    b.addEventListener("click", function () {
      var li = b.parentNode, open = !li.classList.contains("open");
      $$(".has-sub.open").forEach(function (o) { if (o !== li) { o.classList.remove("open"); $(".sub-toggle", o).setAttribute("aria-expanded", "false"); } });
      li.classList.toggle("open", open);
      b.setAttribute("aria-expanded", open);
    });
  });
  document.addEventListener("click", function (e) {
    if (!e.target.closest(".has-sub")) $$(".has-sub.open").forEach(function (o) { o.classList.remove("open"); $(".sub-toggle", o).setAttribute("aria-expanded", "false"); });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    $$(".has-sub.open").forEach(function (o) { o.classList.remove("open"); var b = $(".sub-toggle", o); b.setAttribute("aria-expanded", "false"); b.focus(); });
  });

  /* ---------- cookiekeuze (Google Consent Mode v2) ---------- */
  var banner = $("#consent");
  var setConsent = function (v) {
    store.set("hj_consent", v);
    var g = v === "granted" ? "granted" : "denied";
    if (typeof window.gtag === "function") window.gtag("consent", "update", { ad_storage: g, ad_user_data: g, ad_personalization: g, analytics_storage: g });
    if (banner) banner.hidden = true;
  };
  if (banner) {
    if (!store.get("hj_consent")) banner.hidden = false;
    $$("[data-consent]", banner).forEach(function (b) { b.addEventListener("click", function () { setConsent(b.getAttribute("data-consent")); }); });
  }
  $$("[data-consent-open]").forEach(function (b) { b.addEventListener("click", function () { if (banner) { banner.hidden = false; $("button", banner).focus(); } }); });

  /* ---------- klikken op bellen / WhatsApp meten ---------- */
  document.addEventListener("click", function (e) {
    var a = e.target.closest("[data-track]");
    if (a) track(a.getAttribute("data-track") === "whatsapp" ? "whatsapp_klik" : "bel_klik", { link_url: a.href, pagina: location.pathname });
  });

  /* ---------- formulieren: tijdscheck + nette foutmelding ---------- */
  var started = Date.now();
  $$(".hj-form").forEach(function (f) {
    var ts = $("input[name=ts]", f);
    if (ts) ts.value = String(started);
    f.addEventListener("submit", function (e) {
      var status = $(".form-status", f);
      if (!f.checkValidity()) { e.preventDefault(); f.reportValidity(); return; }
      if (Date.now() - started < 3000) { e.preventDefault(); if (status) status.textContent = "Een moment geduld, probeer het over een paar seconden opnieuw."; return; }
      var btn = $("button[type=submit]", f);
      if (btn) { btn.disabled = true; btn.textContent = "Bezig met versturen…"; }
      store.sset("hj_lead", ($("input[name=formulier]", f) || {}).value || "formulier");
    });
  });
  // pagina terug via de knop "terug": knop weer bruikbaar maken
  window.addEventListener("pageshow", function () { $$(".hj-form button[type=submit][disabled]").forEach(function (b) { b.disabled = false; b.textContent = b.getAttribute("data-label") || "Versturen"; }); });
  $$(".hj-form button[type=submit]").forEach(function (b) { b.setAttribute("data-label", b.textContent); });

  // foutmelding van de server (verzend.php stuurt terug met ?fout=...)
  var fout = new URLSearchParams(location.search).get("fout");
  if (fout) {
    var msg = { velden: "Vul alstublieft uw naam, telefoonnummer en een geldig e-mailadres in.", mail: "Het versturen is niet gelukt. Bel ons gerust op 06 48 57 77 05 of mail naar info@hjverhuizing.nl." }[fout];
    var f1 = $(".hj-form"); if (msg && f1) { $(".form-status", f1).textContent = msg; f1.scrollIntoView({ block: "center" }); }
  }

  // conversie: alleen op de bedankpagina en alleen direct na een verzonden formulier
  if (location.pathname === "/bedankt/" && store.sget("hj_lead")) {
    track("generate_lead", { formulier: store.sget("hj_lead") });
    // Google Ads-conversie "Offerteaanvraag website (bedankpagina)" in account 846-437-8947
    track("conversion", { send_to: "AW-16718229948/R8GHCPrczrIdELzj76M-", value: 1.0, currency: "EUR" });
    store.sdel("hj_lead");
  }

  /* ---------- kaart pas laden na klik ---------- */
  $$(".map[data-map]").forEach(function (m) {
    var b = $("button", m);
    b.addEventListener("click", function () {
      var i = document.createElement("iframe");
      i.src = m.getAttribute("data-map"); i.title = "Kaart"; i.loading = "lazy"; i.referrerPolicy = "no-referrer-when-downgrade";
      m.innerHTML = ""; m.appendChild(i);
    });
  });
})();
