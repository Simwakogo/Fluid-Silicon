/* Fluid Silicon site behaviour.
   Every page is complete without this file. It adds the menus and site search, tabs, the resource,
   device-table and job filters, copy buttons, form handling and, in the one-file preview, the view router. */
(function () {
  "use strict";
  var CFG = window.FS_CONFIG || {};
  var PREVIEW = !!window.FS_PREVIEW;
  var $ = function (sel, root) { return (root || document).querySelector(sel); };
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };

  /* ------------------------------------------------------------ navigation */
  function closeMenus(except) {
    $$(".nav-trigger[aria-expanded='true']").forEach(function (b) {
      if (b === except) return;
      b.setAttribute("aria-expanded", "false");
      var panel = document.getElementById(b.getAttribute("aria-controls")); if (panel) panel.hidden = true;
    });
  }
  $$(".nav-trigger").forEach(function (b) {
    b.addEventListener("click", function () {
      var open = b.getAttribute("aria-expanded") === "true";
      closeMenus(b);
      b.setAttribute("aria-expanded", String(!open));
      var panel = document.getElementById(b.getAttribute("aria-controls")); if (panel) panel.hidden = open;
    });
  });
  document.addEventListener("click", function (e) { if (!e.target.closest(".nav-item")) closeMenus(); });
  var menuBtn = $(".menu-btn"), nav = $("#site-nav");
  function setMenu(open) {
    if (!menuBtn || !nav) return;
    menuBtn.setAttribute("aria-expanded", String(open));
    var lbl = menuBtn.querySelector("span:not(.bars)"); if (lbl) lbl.textContent = open ? "Close" : "Menu";
    nav.classList.toggle("is-open", open);
    document.body.classList.toggle("menu-open", open);
    $$(".nav-panel", nav).forEach(function (p) { p.hidden = true; });
    $$(".nav-trigger", nav).forEach(function (b) { b.setAttribute("aria-expanded", "false"); });
    if (open) { var f = nav.querySelector("a,button"); if (f) f.focus(); }
  }
  if (menuBtn) menuBtn.addEventListener("click", function () { setMenu(menuBtn.getAttribute("aria-expanded") !== "true"); });
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    var openTrig = $(".nav-trigger[aria-expanded='true']");
    if (openTrig && !(nav && nav.classList.contains("is-open"))) { closeMenus(); openTrig.focus(); return; }
    if (nav && nav.classList.contains("is-open")) { setMenu(false); menuBtn.focus(); }
  });
  if (nav) nav.addEventListener("click", function (e) { if (e.target.closest("a")) { setMenu(false); closeMenus(); } });
  window.addEventListener("resize", function () { if (window.innerWidth > 1040 && nav && nav.classList.contains("is-open")) setMenu(false); });

  /* ------------------------------------------------------------ preview router (one-file build only) */
  var ROLE_LABELS = {
    "fpga-engineer": "FPGA Engineer",
    "systems-software-engineer": "Systems Software Engineer, HW/SW Co-Design",
    "software-engineering-intern": "Software Engineering Intern",
    "hardware-design-fpga-intern": "Hardware Design (FPGA) Intern",
    "business-development-intern": "Business Development Intern"
  };
  function route(arg) {
    var raw = typeof arg === "string" ? arg : (location.hash || "").replace(/^#/, "");
    var parts = raw.split("~"), tok = parts[0] || "home", sub = parts[1] || "";
    var view = document.getElementById("view-" + tok);
    if (!view) {
      if (tok === "main") { var m = $("#main"); if (m) { m.setAttribute("tabindex", "-1"); m.focus(); } }
      return;
    }
    $$("[data-route]").forEach(function (v) { v.classList.toggle("is-active", v === view); });
    document.title = view.getAttribute("data-title") || "Fluid Silicon";
    var navKey = view.getAttribute("data-nav");
    $$(".site-header a[href^='#'], .site-footer a[href^='#']").forEach(function (a) {
      var t = a.getAttribute("href").slice(1).split("~")[0];
      if (a.closest(".nav")) { if (t === tok || (a.classList.contains("nav-link") && t === navKey)) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); }
    });
    $$(".nav-trigger").forEach(function (b) {
      var panel = document.getElementById(b.getAttribute("aria-controls"));
      var hit = panel && panel.querySelector("a[aria-current='page']");
      b.classList.toggle("is-current", !!hit);
    });
    setMenu(false); closeMenus();
    if (tok === "apply" && sub && ROLE_LABELS[sub]) prefillRole(sub);
    var target = sub && document.getElementById(sub);
    if (target && view.contains(target)) target.scrollIntoView({ block: "start" });
    else window.scrollTo(0, 0);
    // like a page load: after the first view, move focus to the new content for keyboard and screen reader users
    if (routed) {
      var f = (target && view.contains(target)) ? target : view.querySelector("h1");
      if (f) { if (!f.hasAttribute("tabindex")) f.setAttribute("tabindex", "-1"); f.focus({ preventScroll: true }); }
    }
    routed = true;
  }
  var routed = false;

  /* ------------------------------------------------------------ device table filters */
  $$(".filters[data-filter-for]").forEach(function (box) {
    var table = document.getElementById(box.getAttribute("data-filter-for")); if (!table) return;
    var note = document.querySelector("[data-count-for='" + table.id + "']");
    var state = { vendor: "all", status: "all" };
    function apply() {
      var rows = $$("tbody tr", table), shown = 0;
      rows.forEach(function (r) {
        var ok = (state.vendor === "all" || r.getAttribute("data-vendor") === state.vendor) && (state.status === "all" || r.getAttribute("data-status") === state.status);
        r.hidden = !ok; if (ok) shown++;
      });
      if (note) note.textContent = shown === rows.length ? "Showing all " + rows.length + " families." : "Showing " + shown + " of " + rows.length + " families.";
    }
    $$(".chip-btn", box).forEach(function (b) {
      b.addEventListener("click", function () {
        var f = b.getAttribute("data-f");
        state[f] = b.getAttribute("data-v");
        $$(".chip-btn[data-f='" + f + "']", box).forEach(function (o) { o.setAttribute("aria-pressed", String(o === b)); });
        apply();
      });
    });
  });

  /* ------------------------------------------------------------ header search (index built at publish time) */
  (function () {
    var btn = $(".search-btn"), box = $("#search-box"), input = $("#search-q"), list = $("#search-results");
    if (!btn || !box || !input || !list) return;
    var index = null, loading = null;
    function load() {
      if (index) return Promise.resolve(index);
      if (window.FS_INDEX) { index = window.FS_INDEX; return Promise.resolve(index); }
      if (!loading) loading = fetch("/search-index.json").then(function (r) { return r.json(); }).then(function (j) { index = j; return j; }).catch(function () { index = []; return index; });
      return loading;
    }
    function open(on) {
      btn.setAttribute("aria-expanded", String(on)); box.hidden = !on;
      if (on) { load(); input.focus(); } else { input.value = ""; list.innerHTML = ""; }
    }
    btn.addEventListener("click", function () { open(box.hidden); });
    document.addEventListener("click", function (e) { if (!e.target.closest(".search") && !box.hidden) open(false); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !box.hidden) { open(false); btn.focus(); } });
    function href(item) { return PREVIEW ? "#" + item.p : item.u; }
    function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
    function render(q) {
      q = q.trim().toLowerCase();
      if (!q) { list.innerHTML = ""; return; }
      load().then(function (idx) {
        var words = q.split(/\s+/);
        var hits = idx.map(function (it) {
          var hay = (it.t + " " + it.d + " " + it.k).toLowerCase(), score = 0;
          words.forEach(function (w) { if (it.t.toLowerCase().indexOf(w) >= 0) score += 3; else if (hay.indexOf(w) >= 0) score += 1; else score -= 5; });
          return { it: it, score: score };
        }).filter(function (h) { return h.score > 0; }).sort(function (a, b) { return b.score - a.score; }).slice(0, 8);
        list.innerHTML = hits.length ? hits.map(function (h) {
          return '<li><a href="' + href(h.it) + '"><span class="k">' + esc(h.it.k) + '</span><span class="t">' + esc(h.it.t) + '</span><span class="d">' + esc(h.it.d) + '</span></a></li>';
        }).join("") : '<li class="search-empty">No results for “' + esc(q) + '”.</li>';
      });
    }
    var t; input.addEventListener("input", function () { clearTimeout(t); t = setTimeout(function () { render(input.value); }, 120); });
    list.addEventListener("click", function () { open(false); });
  })();

  /* ------------------------------------------------------------ tabs */
  $$("[data-tabs]").forEach(function (box) {
    var tabs = $$(".tab-btn", box), panels = $$(".tab-panel", box);
    function show(i) {
      tabs.forEach(function (b, j) { b.setAttribute("aria-selected", String(i === j)); b.setAttribute("tabindex", i === j ? "0" : "-1"); });
      panels.forEach(function (p, j) { p.hidden = i !== j; });
    }
    tabs.forEach(function (b, i) {
      b.addEventListener("click", function () { show(i); });
      b.addEventListener("keydown", function (e) {
        var n = e.key === "ArrowRight" ? i + 1 : e.key === "ArrowLeft" ? i - 1 : null;
        if (n === null) return;
        e.preventDefault(); n = (n + tabs.length) % tabs.length; show(n); tabs[n].focus();
      });
    });
    show(0);
  });

  /* ------------------------------------------------------------ knowledge center filter and search */
  (function () {
    var bar = $("[data-res-toolbar]"); if (!bar) return;
    var cards = $$("[data-res-list] .res-card"), q = $("[data-res-search]"), count = $("[data-res-count]"), empty = $("[data-res-empty]");
    var type = "all";
    function apply() {
      var text = (q && q.value || "").trim().toLowerCase(), shown = 0;
      cards.forEach(function (c) {
        var ok = (type === "all" || c.getAttribute("data-type") === type) && (!text || c.textContent.toLowerCase().indexOf(text) >= 0);
        c.hidden = !ok; if (ok) shown++;
      });
      if (count) count.textContent = shown === cards.length ? "Showing all " + cards.length + " resources." : "Showing " + shown + " of " + cards.length + " resources.";
      if (empty) empty.hidden = shown > 0;
    }
    $$("[data-res-type]", bar).forEach(function (b) {
      b.addEventListener("click", function () {
        type = b.getAttribute("data-res-type");
        $$("[data-res-type]", bar).forEach(function (o) { o.setAttribute("aria-pressed", String(o === b)); });
        apply();
      });
    });
    if (q) q.addEventListener("input", apply);
  })();

  /* ------------------------------------------------------------ job listings filter */
  (function () {
    var box = $("[data-jobs-filters]"), list = $("[data-jobs]"); if (!box || !list) return;
    var rows = $$("li", list), count = $("[data-jobs-count]"), sel = $$("select[data-jobs-f]", box);
    function apply() {
      var shown = 0;
      rows.forEach(function (r) {
        var ok = sel.every(function (s) { var v = s.value; return v === "all" || r.getAttribute("data-" + s.getAttribute("data-jobs-f")) === v; });
        r.hidden = !ok; if (ok) shown++;
      });
      if (count) count.textContent = shown === rows.length ? "Showing all " + rows.length + " roles." : (shown ? "Showing " + shown + " of " + rows.length + " roles." : "No roles match. Email careers@fluidsilicon.com with what you're looking for.");
    }
    sel.forEach(function (s) { s.addEventListener("change", apply); });
  })();

  /* ------------------------------------------------------------ copy buttons */
  function copyText(text, btn, fallbackEl) {
    function done(ok) {
      if (!btn) return;
      var old = btn.getAttribute("data-label") || btn.textContent;
      btn.setAttribute("data-label", old);
      btn.textContent = ok ? "Copied" : "Select and copy";
      setTimeout(function () { btn.textContent = old; }, 2200);
      if (!ok && fallbackEl) { var r = document.createRange(); r.selectNodeContents(fallbackEl); var s = getSelection(); s.removeAllRanges(); s.addRange(r); }
    }
    try { navigator.clipboard.writeText(text).then(function () { done(true); }, function () { done(false); }); } catch (e) { done(false); }
  }
  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-copy]"); if (!b) return;
    var el = $(b.getAttribute("data-copy")); if (el) copyText(el.textContent.trim(), b, el);
  });

  /* ------------------------------------------------------------ forms */
  function fieldError(form, input, msg) {
    var err = input.getAttribute("aria-describedby") ? document.getElementById(input.getAttribute("aria-describedby").split(" ").pop()) : null;
    var wrap = input.closest(".field") || input.closest("label");
    if (msg) {
      input.setAttribute("aria-invalid", "true");
      if (wrap) wrap.classList.add("has-error");
      if (err) { err.textContent = msg; err.hidden = false; }
    } else {
      input.removeAttribute("aria-invalid");
      if (wrap) wrap.classList.remove("has-error");
      if (err) { err.textContent = ""; err.hidden = true; }
    }
  }
  function groupError(form, name, errId, msg) {
    var err = document.getElementById(errId);
    if (err) { err.textContent = msg || ""; err.hidden = !msg; }
    $$("input[name='" + name + "']", form).forEach(function (i) { if (msg) i.setAttribute("aria-invalid", "true"); else i.removeAttribute("aria-invalid"); });
  }
  var EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  function status(form, msg, isErr) {
    var s = $(".form-status", form); if (!s) return;
    s.innerHTML = msg; s.classList.toggle("is-error", !!isErr);
  }
  function collect(form) {
    var o = {};
    $$("input,select,textarea", form).forEach(function (el) {
      if (!el.name || el.type === "file") return;
      if (el.type === "checkbox") { if (el.name === "consent") { o.consent = el.checked; return; } if (el.checked) (o[el.name] = o[el.name] || []).push(el.value); return; }
      if (el.type === "radio") { if (el.checked) o[el.name] = el.value; return; }
      o[el.name] = el.value.trim();
    });
    return o;
  }
  function post(url, payload) {
    return fetch(url, { method: "POST", body: JSON.stringify(payload) })   // no Content-Type header: a simple request, no CORS preflight
      .then(function (r) { return r.json(); })
      .then(function (j) { if (!j || j.status !== "ok") throw new Error((j && j.message) || "The server did not accept the form."); return j; });
  }
  function showDone(form, doneId) {
    var done = document.getElementById(doneId); if (!done) return;
    form.hidden = true; done.hidden = false; done.focus();
  }

  /* demo request */
  var demo = document.getElementById("demo-form");
  if (demo) {
    var t0 = Date.now();
    var rd = CFG.replyDays || 2;
    var words = { 1: "one business day", 2: "two business days", 3: "three business days", 5: "five business days" };
    $$("[data-reply-line]").forEach(function (p) { p.textContent = "We'll reply within " + (words[rd] || rd + " business days") + " to set a time."; });
    demo.addEventListener("submit", function (e) {
      e.preventDefault();
      var bad = null;
      [["demo-name", "Enter your name."], ["demo-email", "Enter your work email."], ["demo-company", "Enter your company."]].forEach(function (p) {
        var el = document.getElementById(p[0]); var v = el.value.trim();
        var msg = !v ? p[1] : (p[0] === "demo-email" && !EMAIL.test(v) ? "Enter an email address like name@company.com." : "");
        fieldError(demo, el, msg); if (msg && !bad) bad = el;
      });
      var consent = document.getElementById("demo-consent");
      groupError(demo, "consent", "demo-consent-err", consent.checked ? "" : "Tick the box so we can contact you about this request.");
      if (!consent.checked && !bad) bad = consent;
      if (bad) { status(demo, "Check the highlighted fields.", true); bad.focus(); return; }
      var data = collect(demo);
      if (data.website) { showDone(demo, "demo-done"); return; }       // honeypot filled: quietly drop
      var summary = "Demo request\nName: " + data.name + "\nEmail: " + data.email + "\nCompany: " + data.company + "\nRole: " + (data.title || "") +
        "\nFPGA families: " + (data.families || []).join(", ") + "\nFleet size: " + (data.fleetSize || "") + "\nIndustry: " + (data.industry || "") +
        "\nPriorities: " + (data.goals || []).join(", ") + "\nTimeline: " + (data.timeline || "") + "\n\n" + (data.message || "");
      if (PREVIEW) { status(demo, "This is a preview, so nothing was sent. On fluidsilicon.com this form sends your request to the team."); return; }
      if (!CFG.demoEndpoint) {
        var mail = "mailto:" + (CFG.contactEmail || "info@fluidsilicon.com") + "?subject=" + encodeURIComponent("Demo request: " + data.company) + "&body=" + encodeURIComponent(summary);
        status(demo, "Online requests aren't switched on yet. Email <strong>" + (CFG.contactEmail || "info@fluidsilicon.com") + "</strong> and paste your details: " +
          "<button type=\"button\" class=\"btn btn--ghost btn--small\" id=\"demo-copy-summary\">Copy my details</button> <a href=\"" + mail + "\">Open in my email app</a>");
        var cb = document.getElementById("demo-copy-summary"); if (cb) cb.addEventListener("click", function () { copyText(summary, cb); });
        return;
      }
      var btn = document.getElementById("demo-submit"); btn.disabled = true; status(demo, "Sending your request…");
      data.formType = "demo"; data.elapsedMs = Date.now() - t0; data.page = location.href;
      post(CFG.demoEndpoint, data).then(function () {
        if (CFG.calendarUrl) { var c = $("[data-calendar]"); if (c) { c.hidden = false; $("[data-calendar-link]").setAttribute("href", CFG.calendarUrl); } }
        showDone(demo, "demo-done");
      }).catch(function () {
        btn.disabled = false;
        status(demo, "We couldn't send that just now. Please try again, or email <strong>" + (CFG.contactEmail || "info@fluidsilicon.com") + "</strong>.", true);
      });
    });
  }

  /* contact */
  var contact = document.getElementById("contact-form");
  if (contact) {
    var ct0 = Date.now();
    if (!PREVIEW) { var tq = new URLSearchParams(location.search).get("topic"); var tsel = document.getElementById("ct-topic");
      if (tq && tsel) { var map = { partnership: "Partnership", event: "Event or speaking", press: "Press", careers: "Careers", demo: "Demo or evaluation" }; if (map[tq]) tsel.value = map[tq]; } }
    contact.addEventListener("submit", function (e) {
      e.preventDefault();
      var bad = null;
      [["ct-name", "Enter your name."], ["ct-email", "Enter your work email."], ["ct-message", "Tell us what this is about."]].forEach(function (p) {
        var el = document.getElementById(p[0]); var v = el.value.trim();
        var msg = !v ? p[1] : (p[0] === "ct-email" && !EMAIL.test(v) ? "Enter an email address like name@company.com." : "");
        fieldError(contact, el, msg); if (msg && !bad) bad = el;
      });
      var consent = document.getElementById("ct-consent");
      groupError(contact, "consent", "ct-consent-err", consent.checked ? "" : "Tick the box so we can reply to you.");
      if (!consent.checked && !bad) bad = consent;
      if (bad) { status(contact, "Check the highlighted fields.", true); bad.focus(); return; }
      var data = collect(contact);
      if (data.website) { showDone(contact, "ct-done"); return; }
      var summary = "Contact: " + data.topic + "\nName: " + data.name + "\nEmail: " + data.email + "\nCompany: " + (data.company || "") + "\n\n" + data.message;
      if (PREVIEW) { status(contact, "This is a preview, so nothing was sent. On fluidsilicon.com this form sends your message to the team."); return; }
      if (!CFG.demoEndpoint) {
        var mail = "mailto:" + (CFG.contactEmail || "info@fluidsilicon.com") + "?subject=" + encodeURIComponent(data.topic + ": " + (data.company || data.name)) + "&body=" + encodeURIComponent(summary);
        status(contact, "Online messages aren't switched on yet. Email <strong>" + (CFG.contactEmail || "info@fluidsilicon.com") + "</strong> and paste your message: " +
          "<button type=\"button\" class=\"btn btn--ghost btn--small\" id=\"ct-copy-summary\">Copy my message</button> <a href=\"" + mail + "\">Open in my email app</a>");
        var cb = document.getElementById("ct-copy-summary"); if (cb) cb.addEventListener("click", function () { copyText(summary, cb); });
        return;
      }
      var btn = document.getElementById("ct-submit"); btn.disabled = true; status(contact, "Sending your message…");
      data.formType = "contact"; data.elapsedMs = Date.now() - ct0; data.page = location.href;
      post(CFG.demoEndpoint, data).then(function () { showDone(contact, "ct-done"); }).catch(function () {
        btn.disabled = false;
        status(contact, "We couldn't send that just now. Please try again, or email <strong>" + (CFG.contactEmail || "info@fluidsilicon.com") + "</strong>.", true);
      });
    });
  }

  /* job application */
  var apply = document.getElementById("apply-form");
  function prefillRole(slug) {
    var sel = document.getElementById("apply-role"); if (!sel || !ROLE_LABELS[slug]) return;
    sel.value = slug; sel.dispatchEvent(new Event("change"));
    var line = document.getElementById("apply-role-line"); if (line) line.textContent = "Applying for: " + ROLE_LABELS[slug] + ".";
  }
  if (apply) {
    var at0 = Date.now();
    var roleSel = document.getElementById("apply-role");
    function toggles() {
      var v = roleSel.value;
      $$("[data-show-if]", apply).forEach(function (el) {
        var cond = el.getAttribute("data-show-if");
        el.hidden = !((cond === "role=other" && v === "other") || (cond === "role=intern" && /-intern$/.test(v)));
      });
    }
    roleSel.addEventListener("change", toggles); toggles();
    if (!PREVIEW) { var q = new URLSearchParams(location.search).get("role"); if (q) prefillRole(q); }
    apply.addEventListener("submit", function (e) {
      e.preventDefault();
      var bad = null;
      function need(id, msg, test) {
        var el = document.getElementById(id); var v = el.value.trim();
        var m = !v ? msg : (test ? test(v) : "");
        fieldError(apply, el, m); if (m && !bad) bad = el;
      }
      need("apply-name", "Enter your full name.");
      need("apply-email", "Enter your email address.", function (v) { return EMAIL.test(v) ? "" : "Enter an email address like name@example.com."; });
      need("apply-location", "Tell us where you're based.");
      need("apply-role", "Choose the role you're applying for.");
      var auth = $("input[name='workAuthorized']:checked", apply), spon = $("input[name='needSponsorship']:checked", apply);
      groupError(apply, "workAuthorized", "apply-auth-err", auth ? "" : "Choose yes or no.");
      groupError(apply, "needSponsorship", "apply-spon-err", spon ? "" : "Choose yes or no.");
      if ((!auth || !spon) && !bad) bad = $("input[name='" + (!auth ? "workAuthorized" : "needSponsorship") + "']", apply);
      var fileEl = document.getElementById("apply-resume"), file = fileEl.files && fileEl.files[0];
      var maxMB = CFG.maxResumeMB || 5, fmsg = "";
      if (!file) fmsg = "Attach your résumé.";
      else if (!/\.(pdf|docx?|DOCX?|PDF)$/.test(file.name)) fmsg = "Use a PDF, DOC or DOCX file.";
      else if (file.size > maxMB * 1024 * 1024) fmsg = "That file is " + (file.size / 1048576).toFixed(1) + " MB. Keep it under " + maxMB + " MB.";
      fieldError(apply, fileEl, fmsg); if (fmsg && !bad) bad = fileEl;
      var consent = document.getElementById("apply-consent");
      groupError(apply, "consent", "apply-consent-err", consent.checked ? "" : "Tick the box so we can consider your application.");
      if (!consent.checked && !bad) bad = consent;
      if (bad) { status(apply, "Check the highlighted fields.", true); bad.focus(); return; }
      var d = collect(apply);
      if (d.website) { showDone(apply, "apply-done"); return; }
      if (PREVIEW) { status(apply, "This is a preview, so nothing was sent. On fluidsilicon.com this form sends your application to the hiring team."); return; }
      if (!CFG.applyEndpoint) { status(apply, "Online applications aren't switched on yet. Email your résumé to <strong>" + (CFG.careersEmail || "careers@fluidsilicon.com") + "</strong>.", true); return; }
      var btn = document.getElementById("apply-submit"); btn.disabled = true; btn.textContent = "Uploading…";
      status(apply, "Uploading your résumé and details…");
      var reader = new FileReader();
      reader.onload = function () {
        var payload = {
          formType: "application",
          // "Not provided" / "Not asked" keep older endpoints that expect these fields working; the new script stores them as-is
          name: d.name, email: d.email, phone: d.phone || "Not provided", location: d.location,
          role: roleSel.value === "other" ? "Other: " + (d.roleOther || "") : (ROLE_LABELS[roleSel.value] || roleSel.value),
          startDate: d.startDate || "", onsite: d.onsite || "", school: d.school || "", graduation: d.graduation || "",
          linkedin: d.linkedin || "", portfolio: d.portfolio || "", coverLetter: d.coverLetter || "",
          workAuthorized: d.workAuthorized, needSponsorship: d.needSponsorship,
          visaType: d.needSponsorship === "Yes" ? "Not asked" : "", visaExpiration: d.needSponsorship === "Yes" ? "Not asked" : "",
          honeypot: d.website || "", elapsedMs: Date.now() - at0,
          fileName: file.name, mimeType: file.type, fileData: String(reader.result).split(",")[1]
        };
        post(CFG.applyEndpoint, payload).then(function () { showDone(apply, "apply-done"); }).catch(function (err) {
          btn.disabled = false; btn.textContent = "Submit application";
          var why = err && err.message && !/fetch|network|JSON/i.test(err.message) ? err.message + " " : "";
          status(apply, why + "We couldn't upload that just now. Please try again, or email your résumé to <strong>" + (CFG.careersEmail || "careers@fluidsilicon.com") + "</strong>.", true);
        });
      };
      reader.onerror = function () { btn.disabled = false; btn.textContent = "Submit application"; status(apply, "We couldn't read that file. Try saving it again as a PDF.", true); };
      reader.readAsDataURL(file);
    });
  }

  /* sideways scrollers: a keyboard stop only while there is something to scroll */
  function scrollers() {
    $$("[data-scroller]").forEach(function (el) {
      if (!el.offsetParent) return;                       // hidden view or mobile swap: leave as built
      var over = el.scrollWidth > el.clientWidth + 1;
      if (over) { el.setAttribute("tabindex", "0"); el.setAttribute("role", "region"); }
      else { el.removeAttribute("tabindex"); el.removeAttribute("role"); }
    });
  }
  var rsT; window.addEventListener("resize", function () { clearTimeout(rsT); rsT = setTimeout(scrollers, 150); });
  window.addEventListener("load", scrollers);
  window.FS_scrollers = scrollers;

  if (PREVIEW) {
    // Page links switch views directly, so the preview works even where a viewer blocks fragment navigation
    // (sandboxed frames, local files). The address bar follows along when the viewer allows it.
    document.addEventListener("click", function (e) {
      var a = e.target.closest && e.target.closest("a[href^='#']");
      if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      var raw = a.getAttribute("href").slice(1), tok = raw.split("~")[0] || "home";
      if (tok !== "main" && !document.getElementById("view-" + tok)) return;
      e.preventDefault();
      try { if (location.hash !== "#" + raw) history.pushState(null, "", "#" + raw); } catch (err) { }
      route(raw); scrollers();
    });
    window.addEventListener("hashchange", function () { route(); scrollers(); });
    window.addEventListener("popstate", function () { route(); scrollers(); });
    route();
  }
})();

// team rail arrows
(function () {
  document.querySelectorAll('.team-rail').forEach(function (rail) {
    var track = rail.querySelector('.team'), btns = rail.querySelectorAll('[data-rail]');
    if (!track || btns.length < 2) return;
    function update() {
      btns[0].disabled = track.scrollLeft < 4;
      btns[1].disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 4;
    }
    btns.forEach(function (b) {
      b.addEventListener('click', function () {
        var card = track.querySelector('.person');
        var step = card ? card.offsetWidth + parseFloat(getComputedStyle(track).gap || 24) : 320;
        track.scrollBy({ left: step * Number(b.dataset.rail), behavior: 'smooth' });
      });
    });
    track.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    update();
  });
})();
