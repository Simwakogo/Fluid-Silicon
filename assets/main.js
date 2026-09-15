// Fluid Silicon: renders content.js into the pages.

const S = window.SITE || {};
// All paths in content.js and below are absolute (root-relative), so no path-prefixing needed.

// Mobile nav
const toggle = document.querySelector(".nav-toggle");
const links = document.querySelector(".nav-links");
if (toggle && links) {
  toggle.addEventListener("click", () => {
    const open = links.classList.toggle("open");
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
  });
}

// Hero media: photo if SITE.heroImage is set, else video if SITE.video is set, otherwise the chip fabric animation.
const media = document.getElementById("hero-media");
if (media) {
  if (S.heroImage) {
    media.innerHTML =
      `<img class="hero-photo" src="${S.heroImage}" alt="">`;
  } else if (S.video) {
    media.innerHTML =
      `<video class="hero-video" src="${S.video}" autoplay muted loop playsinline controls></video>`;
  } else {
    const NS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(NS, "svg");
    svg.id = "fabric";
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", "Reconfigurable chip fabric");
    media.appendChild(svg);

    const N = 12, CELL = 22, GAP = 4;
    const SIZE = N * CELL + (N - 1) * GAP;
    svg.setAttribute("viewBox", `0 0 ${SIZE} ${SIZE}`);
    const cells = [];
    for (let r = 0; r < N; r++) for (let c = 0; c < N; c++) {
      const rect = document.createElementNS(NS, "rect");
      rect.setAttribute("x", c * (CELL + GAP));
      rect.setAttribute("y", r * (CELL + GAP));
      rect.setAttribute("width", CELL);
      rect.setAttribute("height", CELL);
      svg.appendChild(rect);
      cells.push(rect);
    }
    const active = new Set();
    while (active.size < 9) active.add(Math.floor(Math.random() * cells.length));
    const paint = () => cells.forEach((rect, i) => {
      const on = active.has(i);
      rect.setAttribute("fill", on ? "#e05a10" : "none");
      rect.setAttribute("stroke", on ? "#e05a10" : "#2a2a2a");
      rect.setAttribute("stroke-width", "1");
    });
    paint();
    if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setInterval(() => {
        const arr = [...active];
        active.delete(arr[Math.floor(Math.random() * arr.length)]);
        let next;
        do { next = Math.floor(Math.random() * cells.length); } while (active.has(next));
        active.add(next);
        paint();
      }, 1400);
    }
  }
}

// Solutions cards
const solutions = document.getElementById("solutions-grid");
if (solutions && S.solutions) {
  solutions.innerHTML = S.solutions.map(x =>
    `<div class="card"><h3>${x.title}</h3><p>${x.text}</p></div>`).join("");
}

// How it works steps
const steps = document.getElementById("steps-grid");
if (steps && S.steps) {
  steps.innerHTML = S.steps.map(x =>
    `<div class="step"><span class="num">${x.n}</span><h3>${x.title}</h3><p>${x.text}</p></div>`).join("");
}

// Industries
const industries = document.getElementById("industry-grid");
if (industries && S.industries) {
  industries.innerHTML = S.industries.map(x =>
    `<a class="industry" href="/industries/">
       <span class="mono">${x.tag}</span><h3>${x.name}</h3><p>${x.text}</p>
     </a>`).join("");
}

// Segments page rows
const segRows = document.getElementById("segment-rows");
if (segRows && S.industries) {
  segRows.innerHTML = S.industries.map(x =>
    `<div class="row"><div><span class="mono">${x.tag}</span><h3>${x.name}</h3></div><p>${x.detail || x.text}</p></div>`).join("");
}

// Careers listings
const renderJobs = (id, list) => {
  const el = document.getElementById(id);
  if (el && list) el.innerHTML = list.map(j =>
    `<a class="job-row" href="${j.href}">
       <span class="job-title">${j.title}</span>
       <span class="job-meta">${j.meta}</span>
       <span class="job-arrow">View →</span>
     </a>`).join("");
};
if (S.jobs) { renderJobs("jobs-fulltime", S.jobs.fulltime); renderJobs("jobs-intern", S.jobs.intern); }

// Recognition logos
const rec = document.getElementById("recognition-row");
if (rec && S.recognition) {
  rec.innerHTML = S.recognition.map(x =>
    `<figure><img src="${x.img}" alt="${x.caption}"><figcaption class="mono">${x.caption}</figcaption></figure>`).join("");
}

// Demo form: prefilled email. Swap for Formspree when ready (see README).
const demoForm = document.getElementById("demo-form");
if (demoForm) {
  demoForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const f = new FormData(demoForm);
    const subject = `Demo request: ${f.get("org")}`;
    const body = [
      `Name: ${f.get("name")}`,
      `Organization: ${f.get("org")}`,
      `Email: ${f.get("email")}`,
      `Segment: ${f.get("segment")}`,
      "",
      f.get("message") || "",
    ].join("\n");
    window.location.href =
      `mailto:demo@fluidsilicon.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  });
}

// Site search
const SEARCH_INDEX = [
  { title: "Home", url: "/", snippet: "Monitor, adapt, and repair reconfigurable chips in real time.", keywords: "monitor adapt repair silicon health monitoring reconfigurable chips FPGA energy efficiency reliability vision mission why this matters" },
  { title: "Industries", url: "/industries/", snippet: "Aerospace & Defense, Hyperscale & Cloud, Telecom & High-Reliability, Finance & HFT.", keywords: "aerospace defense hyperscale cloud telecom finance HFT industries segments" },
  { title: "Our Team", url: "/team/", snippet: "Nhlanhla Mavuso, Dr. André DeHon, and Dr. Jing (Jane) Li.", keywords: "about team our team founder CEO Nhlanhla Mavuso Andre DeHon Jing Jane Li advisors leadership technical advisory President's Sustainability Prize Penn recognition scholar linkedin" },
  { title: "Careers", url: "/careers/", snippet: "Open roles at Fluid Silicon in Philadelphia.", keywords: "careers jobs open roles hiring FPGA engineer systems software engineer intern internship" },
  { title: "FPGA Engineer", url: "/jobs/fpga-engineer/", snippet: "Full-time FPGA Engineer role in Philadelphia.", keywords: "FPGA engineer RTL SystemVerilog VHDL job role full-time" },
  { title: "Systems Software Engineer, HW/SW Co-Design", url: "/jobs/systems-software-engineer/", snippet: "Full-time systems software engineering role.", keywords: "systems software engineer HW SW co-design firmware drivers embedded job role full-time" },
  { title: "Internships", url: "/jobs/internships/", snippet: "Software Engineering, Hardware Design / FPGA, and Business Development internships.", keywords: "internship intern software engineering hardware design FPGA business development" },
  { title: "Schedule a Demo", url: "/demo/", snippet: "See Fluid Silicon on live hardware.", keywords: "demo schedule request contact sales" },
  { title: "Apply", url: "/apply/", snippet: "Submit an application for an open role.", keywords: "apply application resume job form work authorization visa sponsorship" }
];

function toggleSearch() {
  const panel = document.getElementById('search-panel');
  const input = document.getElementById('search-input');
  if (!panel) return;
  const isOpen = panel.classList.toggle('open');
  if (isOpen && input) setTimeout(() => input.focus(), 50);
}

const searchInput = document.getElementById('search-input');
const searchResults = document.getElementById('search-results');
if (searchInput && searchResults) {
  searchInput.addEventListener('input', () => {
    const q = searchInput.value.trim().toLowerCase();
    if (!q) { searchResults.innerHTML = ''; return; }
    const matches = SEARCH_INDEX.filter(item =>
      item.title.toLowerCase().includes(q) ||
      item.snippet.toLowerCase().includes(q) ||
      item.keywords.toLowerCase().includes(q)
    ).slice(0, 6);
    if (matches.length === 0) {
      searchResults.innerHTML = '<p class="search-empty">No results found.</p>';
      return;
    }
    searchResults.innerHTML = matches.map(item =>
      `<a class="search-result" href="${item.url}">
         <span class="search-result-title">${item.title}</span>
         <span class="search-result-snippet">${item.snippet}</span>
       </a>`
    ).join('');
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const panel = document.getElementById('search-panel');
      if (panel) panel.classList.remove('open');
    }
  });
}
