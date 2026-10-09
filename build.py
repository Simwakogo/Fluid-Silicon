#!/usr/bin/env python3
"""Fluid Silicon static site builder. No dependencies beyond Python 3.9+.

    python3 build.py          -> dist/site     (deploy to GitHub Pages; every page is real HTML)
                              -> dist/preview  (one-file preview used for the Claude artifact)

Edit copy in src/pages/*.html. Shared pieces (header, footer, specs, device table,
diagrams) live below so every page says the same thing the same way.
"""
import json, os, re, shutil, sys, html
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgparts as S

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
DIST = os.path.join(ROOT, "dist")
SITE_URL = "https://fluidsilicon.com"
BUILD_DATE = "2026-09-29"          # shown as "Updated" on careers and device support
POST_DATE = "2026-09-24"           # publication date of the first five blog posts
esc = html.escape

# ------------------------------------------------------------------ facts used on several pages (one source of truth)
FACTS = {
    "margin": "30–54%",
    "precision": "< 20 ps",
    "sweep": "1 s",
    "lut": "< 1%",
    "ff": "< 5%",
    "delay": "< 2%",
    "variation": "> 20%",
    "service": "6+ years",
    "contact": "info@fluidsilicon.com",
    "careers": "careers@fluidsilicon.com",
    "linkedin": "https://www.linkedin.com/company/fluidsilicon/",
}

DEVICES = [
    # vendor, family, node, status key, note
    ("AMD", "7-series", "28 nm", "ok", ""),
    ("AMD", "UltraScale", "20 nm", "ok", ""),
    ("AMD", "UltraScale+", "16 nm", "ok", "Includes Virtex UltraScale+"),
    ("Altera", "Agilex 7", "10 nm class", "select", "Select devices, including F-Series"),
    ("Altera", "Stratix 10 / Arria 10", "14 nm / 20 nm", "dev", ""),
    ("AMD", "Versal AI Core", "7 nm", "dev", ""),
]
STATUS = {"ok": ("Supported", "pill--ok"), "select": ("Select devices", "pill--select"), "dev": ("In development", "pill--dev")}

CITES = {
    "nsdi": ('Firestone et al., “Azure Accelerated Networking: SmartNICs in the Public Cloud,” NSDI 2018',
             "https://www.usenix.org/conference/nsdi18/presentation/firestone"),
    "fpga26": ('Rydberg et al., “Hyperscale FPGA Engineering Systems at Microsoft,” FPGA 2026',
               "https://doi.org/10.1145/3748173.3779203"),
    "penn": ("Penn Today, “Penn student develops a way for computer chips to run more efficiently,” May 5, 2026",
             "https://penntoday.upenn.edu/news/penn-student-develops-way-computer-chips-run-more-efficiently"),
}

# ------------------------------------------------------------------ routes (deploy path -> preview token)
import content as C

ROUTES = {"/": "home", "/solutions/": "solutions"}
for _s in C.SOLUTIONS:
    ROUTES[f"/solutions/{_s['slug']}/"] = f"sol-{_s['slug']}"
ROUTES["/industries/"] = "industries"
ROUTES.update({
    "/technology/": "technology", "/technology/security/": "security", "/technology/devices/": "devices",
    "/blog/": "blog",
})
for _k, _r in C.RESOURCES.items():
    if _r["type"] == "Blog":
        ROUTES[_r["path"]] = "post-" + _k
ROUTES.update({
    "/company/": "company", "/company/events/": "events", "/company/news/": "news",
    "/careers/": "careers", "/jobs/": "jobs", "/apply/": "apply", "/demo/": "demo", "/contact/": "contact",
    "/privacy/": "privacy", "/terms/": "terms", "/404.html": "not-found",
})

# the header: a mega menu for Solutions (by topic, by industry), Technology, Resources and Company; Partners is a plain link
NAV = [
    ("mega", "solutions", "Solutions", "/solutions/", [
        ("By topic", [(f"/solutions/{s['slug']}/", s["name"], s["short"]) for s in C.SOLUTIONS]),
        ("By industry", [(f"/industries/#{i['slug']}", i["name"], i["short"]) for i in C.INDUSTRIES]),
    ], ("/solutions/", "Explore all solutions")),
    ("mega", "technology", "Technology", "/technology/", [
        ("", [("/technology/#monitoring", "Timing health monitoring", "Per-element timing measured at speed, in production."),
              ("/technology/#integration", "Integration and deployment", "Beside your design, on your site."),
              ("/technology/#characterization", "Characterization applications", "Every card measured before and after service."),
              ("/technology/#in-field", "In-field applications", "Monitor, model, tune and, when needed, repair."),
              ("/technology/security/", "Security and integration", "Six guarantees, controls and an FAQ."),
              ("/technology/devices/", "Device support", "AMD and Altera families, with status.")]),
    ], ("/technology/", "Technology overview")),
    ("mega", "resources", "Resources", "/blog/", [
        ("", [("/blog/", "Blog", "Margins, aging, power and how an evaluation runs."),
              ("/technology/security/", "Security and integration", "Where the health layer sits and its six guarantees."),
              ("/technology/devices/", "Device support", "AMD and Altera families, with status.")]),
    ], ("feature", "brief")),
    ("mega", "company", "Company", "/company/", [
        ("", [("/company/", "About and team", "Who we are, and where this is going."),
              ("/company/#partners", "Partners", "Vendors, tools and the partner program."),
              ("/company/news/", "News and press", "Coverage, announcements and the press kit."),
              ("/company/events/", "Events", "Where to meet the team."),
              ("/contact/", "Contact", "Questions, partnerships and press.")]),
    ], None),
    ("link", "careers", "Careers", "/careers/"),
]

CHEV = '<svg viewBox="0 0 10 10" aria-hidden="true" focusable="false"><path d="M1.5 3.5 L5 7 L8.5 3.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
ARROW = '<svg viewBox="0 0 14 14" aria-hidden="true" focusable="false"><path d="M2 7 H12 M8 3 L12 7 L8 11" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
PENN = '<svg viewBox="0 0 40 24" aria-hidden="true" focusable="false"><text x="20" y="17" text-anchor="middle" font-family="Red Hat Display, Segoe UI, system-ui, sans-serif" font-weight="700" font-size="13" fill="currentColor">Penn</text></svg>'
SCHOLAR = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M12 3 1 9l11 6 9-4.9V17h2V9L12 3zm0 14.2L5 13.4V17c0 2.2 3.1 4 7 4s7-1.8 7-4v-3.6l-7 3.8z"/></svg>'
LINKEDIN = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M20.45 20.45h-3.55v-5.57c0-1.33-.02-3.04-1.85-3.04-1.86 0-2.14 1.45-2.14 2.94v5.67H9.36V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.45v6.29zM5.34 7.43a2.06 2.06 0 1 1 0-4.12 2.06 2.06 0 0 1 0 4.12zM7.12 20.45H3.56V9h3.56v11.45z"/></svg>'


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


LOGO_DARK = re.sub(r"<title>.*?</title>", "", read(os.path.join(SRC, "assets/img/logo-on-dark.svg")))
LOGO_LIGHT = re.sub(r"<title>.*?</title>", "", read(os.path.join(SRC, "assets/img/logo-on-light.svg")))


def logo_svg(uid, on="light"):
    """Inline logo; strips the file's own title and labels it for its link."""
    s = (LOGO_LIGHT if on == "light" else LOGO_DARK).replace('role="img" aria-label="Fluid Silicon"', 'aria-hidden="true" focusable="false"')
    return s.replace("<svg ", f'<svg id="{uid}" ', 1)


# ------------------------------------------------------------------ shared components
def spec_strip(note=True):
    items = [
        (FACTS["margin"], "*", "timing margin a chip carries for the worst-case corner"),
        (FACTS["precision"], "", "per-link measurement precision, error plus drift"),
        (FACTS["sweep"], "", "to measure every logic element on the chip"),
        (FACTS["lut"], "", "of LUTs, and under 5% of flip-flops, on a production shell"),
        (FACTS["delay"], "", "delay impact on your design"),
        ("0", "", "downtime while monitoring runs"),
    ]
    out = ['<div class="specs" role="list">']
    for v, star, k in items:
        sup = f'<sup>{star}</sup>' if star else ""
        out.append(f'<div class="spec" role="listitem"><div class="v">{esc(v)}{sup}</div><div class="k">{esc(k)}</div></div>')
    out.append('</div>')
    if note:
        out.append('<p class="footnote">*Fluid Silicon measurements. Varies with variation pattern, workload, vendor and device age.</p>')
    return "".join(out)


def device_table(uid, filters=True, compact=False):
    out = []
    if filters:
        out.append(f'''<div class="filters" data-filter-for="{uid}">
  <div class="grp" role="group" aria-label="Filter by vendor"><span>Vendor</span>
    <button type="button" class="chip-btn" data-f="vendor" data-v="all" aria-pressed="true">All</button>
    <button type="button" class="chip-btn" data-f="vendor" data-v="AMD" aria-pressed="false">AMD</button>
    <button type="button" class="chip-btn" data-f="vendor" data-v="Altera" aria-pressed="false">Altera</button></div>
  <div class="grp" role="group" aria-label="Filter by status"><span>Status</span>
    <button type="button" class="chip-btn" data-f="status" data-v="all" aria-pressed="true">All</button>
    <button type="button" class="chip-btn" data-f="status" data-v="ok" aria-pressed="false">Supported</button>
    <button type="button" class="chip-btn" data-f="status" data-v="select" aria-pressed="false">Select devices</button>
    <button type="button" class="chip-btn" data-f="status" data-v="dev" aria-pressed="false">In development</button></div>
</div>''')
    tcls = "data data--fit data--compact"
    out.append(f'<div class="table-wrap"><table class="{tcls}" id="{uid}"><caption>Status as of September 2026. AMD and Altera product names are trademarks of their respective owners.</caption>'
               '<thead><tr><th scope="col" class="col-vendor">Vendor</th><th scope="col">Family</th><th scope="col">Process node</th><th scope="col">Status</th>')
    if not compact:
        out.append('<th scope="col" class="col-notes">Notes</th>')
    out.append('</tr></thead><tbody>')
    for vendor, fam, node, st, note in DEVICES:
        label, cls = STATUS[st]
        note_sm = f'<span class="note-sm">{esc(note)}</span>' if (note and not compact) else ""
        node_s = esc(node.replace(" nm / ", " / "))
        out.append(f'<tr data-vendor="{vendor}" data-status="{st}"><td class="col-vendor">{vendor}</td><th scope="row"><span class="vend" aria-hidden="true">{vendor}</span>{esc(fam)}{note_sm}</th><td class="mono">{node_s}</td><td><span class="pill {cls}">{label}</span></td>')
        if not compact:
            out.append(f'<td class="col-notes">{esc(note) if note else "&nbsp;"}</td>')
        out.append('</tr>')
    out.append('</tbody></table></div>')
    if filters:
        out.append(f'<p class="count-note" aria-live="polite" data-count-for="{uid}">Showing all 6 families.</p>')
    return "".join(out)


_CTA_N = 0
_CAP_N = 0


def cta_band(title="Measure a device at speed, live.",
             text="A 30-minute session: in-system slack measurements on a supported AMD or Altera device, and what an evaluation on your boards involves.",
             brief=True):
    b = ('<a class="btn btn--ghost" href="/assets/docs/fluid-silicon-technical-brief.pdf">Technical brief (PDF)</a>' if brief else "")
    global _CTA_N
    _CTA_N += 1
    cid = f"cta-{_CTA_N}"
    return f'''<section class="cta-band on-dark" aria-labelledby="{cid}">
  <div class="wrap">
    <div><h2 id="{cid}">{esc(title)}</h2><p>{esc(text)}</p></div>
    <div class="btn-row"><a class="btn btn--primary" href="/demo/">Request a demo {ARROW}</a>{b}</div>
  </div>
</section>'''


def figure_bar(legend_html="", note=""):
    return f'<div class="fig-bar"><div class="legend">{legend_html}</div><div class="legend">{note}</div></div>'


def icon_box(name):
    return f'<span class="icon">{S.icon(name)}</span>'


LIFECYCLE = [
    ("Before deployment", "Characterize and map", "Every LUT and carry block measured at speed, with a weak-resource map for the card."),
    ("After deployment", "Characterize again", "Cards leaving service measured the same way, with the evidence to resell, reuse or retire them."),
]
LOOP4 = [
    ("monitor", "Monitor", "Every logic element swept in about a second while the design runs."),
    ("model", "Model", "An aging curve per card and per element, with a predicted time-to-threshold."),
    ("tune", "Tune", "Voltage and frequency held within each device's measured margin, in windows you schedule."),
    ("repair", "Repair", "Only when an element degrades toward your threshold: that path moves to a healthy resource, through your change process."),
]


def lifecycle():
    """The health loop as three phases: the production phase holds the four connected capabilities."""
    before, after = LIFECYCLE
    loop = "".join(f'<div>{icon_box(ic)}<div><h4>{esc(t)}</h4><p>{esc(d)}</p></div></div>' for ic, t, d in LOOP4)
    return (f'<div class="lifecycle">'
            f'<div><p class="when">{before[0]}</p><h3>{before[1]}</h3><p>{before[2]}</p></div>'
            f'<div class="is-prod"><p class="when">In production</p><h3>Monitor, model, tune, repair. Then measure again.</h3>'
            f'<div class="loop4">{loop}</div><p class="loop-note">Monitoring feeds the model and the tuning; both feed back into monitoring, so every change is measured again.</p></div>'
            f'<div><p class="when">{after[0]}</p><h3>{after[1]}</h3><p>{after[2]}</p></div></div>')


def _mock_nav(on, items=None):
    items = items or ["Fleet", "Cards", "Alerts", "Models", "Reports", "Settings"]
    out = ['<div class="mock-nav" aria-hidden="true">']
    for i in items:
        out.append(f'<span class="on">{i}</span>' if i == on else f'<span>{i}</span>')
    out.append('</div>')
    return "".join(out)


def slack_map(uid, w=300, h=120, cols=40, rows=16):
    """One chip's measured slack as a heat map: the lowest slack in each small region of logic, hard columns blank,
    clock-region lines, and the weakest element ringed. Illustrative; deterministic per uid."""
    import math
    import random
    rnd = random.Random(uid)
    cw, ch = w / cols, h / rows
    weak = (27, 4)
    hard = {9, 22, 33}
    ramp = [(0.20, "#d2492f"), (0.32, "#ec8f3e"), (0.45, "#e3c25a"), (0.60, "#9cc96b")]
    out = [f'<svg class="slackmap" viewBox="0 0 {w} {h}" aria-hidden="true" focusable="false">',
           f'<rect width="{w}" height="{h}" rx="4" fill="#f4f1ea"/>']
    for r in range(rows):
        for c in range(cols):
            if c in hard:
                continue
            d = (c - weak[0]) ** 2 / 30 + (r - weak[1]) ** 2 / 8
            v = 0.66 + 0.16 * math.sin(c / 6.0) * math.cos(r / 4.0) + rnd.uniform(-0.07, 0.07) - 0.52 * math.exp(-d)
            fill = next((col for lim, col in ramp if v < lim), "#57a773")
            out.append(f'<rect x="{c * cw + .5:.1f}" y="{r * ch + .5:.1f}" width="{cw - 1:.1f}" height="{ch - 1:.1f}" rx="1" fill="{fill}"/>')
    for k in range(1, 4):
        out.append(f'<line x1="0" x2="{w}" y1="{k * h / 4:.1f}" y2="{k * h / 4:.1f}" stroke="#15130f" stroke-opacity=".18" stroke-width=".8"/>')
    x, y = weak[0] * cw + cw / 2, weak[1] * ch + ch / 2
    out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{ch * 1.15:.1f}" fill="none" stroke="#15130f" stroke-width="1.6"/>')
    out.append('</svg>')
    return "".join(out)


DEVICE_NAV = ["Chip", "Elements", "History", "Model", "Operating point", "Reports"]


def mock(kind, light=False):
    """Static product screens. Illustrative data; the numbers are the site's own figures, not a customer's."""
    cls = "mock mock--light" if light else "mock"
    title = {"fleet": "Fleet health", "program": "Program health"}.get(kind, "Device health")
    bar = f'<div class="mock-bar"><span class="dots" aria-hidden="true"><i></i><i></i><i></i></span><span class="mock-title">Fluid Silicon · {title}</span></div>'
    if kind == "device":
        hm = slack_map("devmap")
        sp = S.spark(S.series(11, 30, 14.6, -0.21, 0.18), 300, 56)
        main = (f'<div class="mock-main"><div class="mock-head"><strong>Chip B2-04 · XCVU9P</strong><span>AMD Virtex UltraScale+ · 16 nm · measured 2 min ago</span></div>'
                f'<div class="mock-tiles"><div><small>Median slack</small><b>33.7%</b></div><div><small>Worst slack</small><b class="red">8.2%</b></div><div><small>Time to threshold</small><b class="red">1.4 yrs</b></div><div><small>Clock</small><b>250 MHz</b></div></div>'
                f'<div class="mock-two"><div class="mock-panel"><div class="ph"><strong>Worst-slack element</strong><span>X84Y212 · C6LUT</span></div>{sp}</div>'
                f'<div class="mock-panel"><div class="ph"><strong>Slack across the chip</strong><span>lowest per region</span></div>{hm}</div></div>'
                f'<div class="mock-panel mock-table-wrap"><div class="ph"><strong>Lowest-slack elements</strong><span>the three lowest</span></div>'
                f'<table class="mock-table"><thead><tr><th>Site</th><th>Element</th><th>Slack</th><th>Time to threshold</th><th>Status</th></tr></thead><tbody>'
                f'<tr><td>X84Y212</td><td>C6LUT</td><td>8.2%</td><td>1.4 yrs</td><td><span class="st st-act">Action</span></td></tr>'
                f'<tr><td>X85Y212</td><td>Carry</td><td>9.6%</td><td>2.2 yrs</td><td><span class="st st-watch">Watch</span></td></tr>'
                f'<tr><td>X40Y96</td><td>B5LUT</td><td>11.9%</td><td>2.8 yrs</td><td><span class="st st-watch">Watch</span></td></tr>'
                f'</tbody></table></div></div>')
        body = f'<div class="mock-body">{_mock_nav("Chip", DEVICE_NAV)}{main}</div>'
        label = ("Device screen: median slack 33.7%, worst slack 8.2% at site X84Y212, time to threshold 1.4 years, clock 250 MHz, "
                 "with a slack map across the die, the worst-slack element's history and a table of the three lowest-slack elements.")
    elif kind == "fleet":
        sp = S.spark(S.series(5, 30, 37.2, 0.04, 0.35), 300, 64)
        br = S.bars([2, 3, 6, 11, 19, 31, 46, 58, 64, 52, 38, 21, 9, 4], 300, 64, low=2)
        main = (f'<div class="mock-main"><div class="mock-head"><strong>Fleet overview</strong><span>1,248 cards · AMD and Altera · updated 2 min ago</span></div>'
                f'<div class="mock-tiles"><div><small>Healthy</small><b class="green">1,231</b></div><div><small>Watch</small><b class="amber">14</b></div><div><small>Action needed</small><b class="red">3</b></div><div><small>Median slack</small><b>38.4%</b></div></div>'
                f'<div class="mock-two"><div class="mock-panel"><div class="ph"><strong>Median slack</strong><span>last 90 days</span></div>{sp}</div>'
                f'<div class="mock-panel"><div class="ph"><strong>Weakest element per card</strong><span>slack, % of clock</span></div>{br}</div></div>'
                f'<div class="mock-panel mock-table-wrap"><div class="ph"><strong>Needs attention</strong><span>3 of 1,248</span></div>'
                f'<table class="mock-table"><thead><tr><th>Card</th><th>Family</th><th>Weakest element</th><th>Time to threshold</th><th>Status</th></tr></thead><tbody>'
                f'<tr><td>A3-07</td><td>Virtex UltraScale+</td><td>8.2%</td><td>1.4 yrs</td><td><span class="st st-act">Action</span></td></tr>'
                f'<tr><td>B1-12</td><td>Agilex 7</td><td>11.9%</td><td>2.8 yrs</td><td><span class="st st-watch">Watch</span></td></tr>'
                f'<tr><td>C4-02</td><td>UltraScale</td><td>12.6%</td><td>3.1 yrs</td><td><span class="st st-watch">Watch</span></td></tr>'
                f'</tbody></table></div></div>')
        body = f'<div class="mock-body">{_mock_nav("Fleet")}{main}</div>'
        label = "Fleet overview screen: 1,248 cards, 1,231 healthy, 14 to watch, 3 needing action, median slack 38.4%, with a chart of median slack over 90 days and a table of the three cards needing attention."
    elif kind in ("card", "tune"):
        tune = kind == "tune"
        br = S.bars([1, 2, 5, 12, 24, 41, 57, 66, 60, 44, 27, 13, 6, 2], 300, 64, low=2)
        sp = S.spark(S.series(9, 30, 2.6, 0.06, 0.12), 300, 64)
        main = (f'<div class="mock-main"><div class="mock-head"><strong>Card {"B2-04" if tune else "A3-07"}</strong><span>AMD Virtex UltraScale+ · 16 nm · {"2.1" if tune else "4.2"} years in service</span></div>'
                + ('<div class="mock-tiles"><div><small>Median slack</small><b>33.7%</b></div><div><small>Weakest element</small><b>14.1%</b></div><div><small>Time to threshold</small><b class="green">5.2 yrs</b></div><div><small>Operating point</small><b>0.85 V</b></div></div>' if tune else
                   '<div class="mock-tiles"><div><small>Median slack</small><b>33.7%</b></div><div><small>Weakest element</small><b class="red">8.2%</b></div><div><small>Time to threshold</small><b class="red">1.4 yrs</b></div><div><small>Operating point</small><b>0.85 V</b></div></div>') +
                f'<div class="mock-two"><div class="mock-panel"><div class="ph"><strong>Slack, all elements</strong><span>% of clock</span></div>{br}</div>'
                f'<div class="mock-panel"><div class="ph"><strong>Path delay increase</strong><span>fitted, 55 °C history</span></div>{sp}</div></div>'
                f'<div class="mock-panel"><dl class="mock-kv"><dt>Last sweep</dt><dd>2 min ago, 1.0 s</dd><dt>Aging model</dt><dd>Power-law fit to this card\'s temperature history</dd>'
                + ('<dt>Recommended action</dt><dd><span class="st st-watch">Lower operating point to 0.83 V in the next window</span></dd><dt>Approval</dt><dd>Waiting for your approval; re-measured after the change</dd></dl></div></div>' if tune else
                   '<dt>Recommended action</dt><dd><span class="st st-act">Schedule a repair window</span></dd><dt>Approval</dt><dd>Waiting for your change process</dd></dl></div></div>'))
        body = f'<div class="mock-body">{_mock_nav("Cards")}{main}</div>'
        label = ("Card detail screen for one healthy card with a recommended lower operating point of 0.83 V awaiting approval." if tune else
                 "Card detail screen for one card: median slack 33.7%, weakest element 8.2%, time to threshold 1.4 years, with a slack histogram, an aging curve, and a recommended repair window awaiting approval.")
    else:
        sp = S.spark(S.series(3, 30, 3.1, 0.05, 0.1), 300, 64)
        br = S.bars([9, 8, 8, 7, 7, 6, 6, 5, 5, 4, 4, 3, 2, 1], 300, 64, low=0)
        main = (f'<div class="mock-main"><div class="mock-head"><strong>Program: far-edge RF units</strong><span>24 boards · 3 platforms · mission month 14</span></div>'
                f'<div class="mock-tiles"><div><small>Nominal</small><b class="green">23</b></div><div><small>Watch</small><b class="amber">1</b></div><div><small>Median time to threshold</small><b>6.9 yrs</b></div><div><small>Config changes</small><b>0</b></div></div>'
                f'<div class="mock-two"><div class="mock-panel"><div class="ph"><strong>Path delay increase, hottest board</strong><span>fitted</span></div>{sp}</div>'
                f'<div class="mock-panel"><div class="ph"><strong>Time to threshold by board</strong><span>years</span></div>{br}</div></div>'
                f'<div class="mock-panel mock-table-wrap"><div class="ph"><strong>Watch list</strong><span>1 of 24</span></div>'
                f'<table class="mock-table"><thead><tr><th>Board</th><th>Platform</th><th>Enclosure temp.</th><th>Time to threshold</th><th>Status</th></tr></thead><tbody>'
                f'<tr><td>RF-11</td><td>Airborne radar</td><td>68 °C</td><td>3.9 yrs</td><td><span class="st st-watch">Watch</span></td></tr>'
                f'<tr><td>RF-04</td><td>Ground station</td><td>41 °C</td><td>9.8 yrs</td><td><span class="st st-ok">Nominal</span></td></tr>'
                f'</tbody></table></div></div>')
        body = f'<div class="mock-body">{_mock_nav("Reports")}{main}</div>'
        label = "Program screen for 24 far-edge boards: 23 nominal, 1 to watch, median time to threshold 6.9 years, with the hottest board's aging curve and a watch list."
    return f'<div class="{cls}" role="img" aria-label="Illustrative product screen. {esc(label)}">{bar}{body}</div>'


def mock_figure(arg, light=False):
    kind, _, caption = arg.partition("|")
    caption = caption.strip() or "Illustrative product screen with example data."
    return f'<figure class="figure">{mock(kind.strip(), light)}<figcaption class="mock-caption">{esc(caption)}</figcaption></figure>'


def margin_figure(uid):
    leg = ('<span><i class="sw-ink3"></i>Fleet of chips</span><span><i class="sw-blue"></i>LUT links</span>'
           '<span><i class="sw-orange"></i>Carry links</span><span><i class="sw-gold"></i>Per-chip sign-off</span>')
    return (f'<figure class="figure"><div class="scroll-x">{S.margin_chart(uid)}</div>'
            f'<p class="scroll-hint">Scroll sideways to see the whole chart.</p>'
            f'{figure_bar(leg, "<span>Illustrative, not to scale. *Fluid Silicon measurements.</span>")}</figure>')


def aging_figure(uid, compact=False):
    leg = ('<span><i class="sw-blue"></i>45 °C</span><span><i class="sw-gold"></i>55 °C</span><span><i class="sw-red"></i>70 °C</span>')
    if compact:
        return f'<figure class="figure">{S.aging_chart(uid, compact=True)}{figure_bar(leg, "<span>Illustrative model for one card.</span>")}</figure>'
    return (f'<figure class="figure"><div class="scroll-x">{S.aging_chart(uid)}</div>'
            f'<p class="scroll-hint">Scroll sideways to see the whole chart.</p>'
            f'{figure_bar(leg, "<span>Illustrative model for one card. Hotter enclosures age faster.</span>")}</figure>')


def margin_half_figure(uid):
    leg = ('<span><i class="sw-blue"></i>LUT links</span><span><i class="sw-orange"></i>Carry links</span><span><i class="sw-gold"></i>Per-chip sign-off</span>')
    return f'<figure class="figure">{S.margin_chart_half(uid)}{figure_bar(leg, "<span>Illustrative, not to scale.</span>")}</figure>'


def eeo():
    return ('<p class="eeo">Fluid Silicon is an equal opportunity employer. We consider all qualified applicants without regard to race, color, religion, '
            'sex (including pregnancy), sexual orientation, gender identity or expression, national origin, ancestry, age, disability, genetic information, '
            'veteran status or any other status protected by law. If you need an accommodation at any point in the process, email '
            f'<a href="mailto:{FACTS["careers"]}">{FACTS["careers"]}</a>.</p>')


def about_blurb():
    return ('<p>Fluid Silicon builds in-system timing measurement for FPGAs. Its health layer measures setup slack on every LUT and carry chain '
            'at operating frequency while the design runs, flags the paths losing margin and predicts when each device will need attention.</p>')


def cite(key):
    t, u = CITES[key]
    return f'<a href="{u}" rel="noopener">{esc(t)}</a>'


def fill(key, text):
    return f'<span class="fill" data-fill="{key}">{esc(text)}</span>'




def fabric_svg(uid, weak=False, n=12):
    """A chip: package with pads, and on the die a floorplan of clock regions and logic columns with the health layer's
    sensor cells (orange) embedded in the columns, the way they sit in a real placement. A slow sweep line shows the
    measurement pass (CSS animation, off with reduced motion). weak=True marks weak regions found by the measurement."""
    import random
    rnd = random.Random(uid)
    W = 360
    pk, die = 22, 44                      # package inset, die inset
    out = [f'<svg class="fabric" id="{uid}" viewBox="0 0 {W} {W}" role="img" aria-label="{esc("A chip die with the health layer" + (" and weak regions marked" if weak else "") + ": sensor cells embedded in the logic columns of every clock region.")}">']
    out.append(f'<rect x="{pk}" y="{pk}" width="{W - 2 * pk}" height="{W - 2 * pk}" rx="10" fill="#2a2a2a" stroke="#3a3a3a"/>')
    # pads on all four sides
    for k in range(14):
        t = pk + 14 + k * ((W - 2 * pk - 28) / 13)
        for x, y, w, h in ((t - 3, 6, 6, 12), (t - 3, W - 18, 6, 12), (6, t - 3, 12, 6), (W - 18, t - 3, 12, 6)):
            out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="1" fill="#b9912e"/>')
    out.append(f'<rect x="{die}" y="{die}" width="{W - 2 * die}" height="{W - 2 * die}" rx="3" fill="#0b0b0b"/>')
    # clock regions: 2 across, 3 down
    cols, rows = 2, 3
    rw, rh = (W - 2 * die) / cols, (W - 2 * die) / rows
    colors = ["#7fbf3f", "#5b6de8", "#3f7fd6", "#c94fb8", "#d8544f", "#3fbf9f"]
    for r in range(rows):
        for c in range(cols):
            x0, y0 = die + c * rw, die + r * rh
            k = r * cols + c
            out.append(f'<rect x="{x0 + 1.5:.1f}" y="{y0 + 1.5:.1f}" width="{rw - 3:.1f}" height="{rh - 3:.1f}" fill="none" stroke="{colors[k]}" stroke-width="1" opacity=".55"/>')
            out.append(f'<text x="{x0 + 4:.1f}" y="{y0 + rh - 4:.1f}" font-family="ui-monospace, Menlo, monospace" font-size="6.5" fill="{colors[k]}" opacity=".8" aria-hidden="true">X{c}Y{rows - 1 - r}</text>')
            # logic columns: faint stripes, and sensor cells in a few of them
            ncol = 9
            sensor_cols = sorted(rnd.sample(range(1, ncol), 4))
            for ci in range(ncol):
                cx = x0 + 6 + ci * (rw - 12) / (ncol - 1)
                out.append(f'<rect x="{cx - 1.2:.1f}" y="{y0 + 5:.1f}" width="2.4" height="{rh - 14:.1f}" fill="#8892a6" opacity=".14"/>')
                if ci in sensor_cols:
                    step = rnd.choice([9, 10, 11])
                    off = rnd.uniform(0, step)
                    yy = y0 + 7 + off
                    while yy < y0 + rh - 10:
                        wide = rnd.random() < .35
                        out.append(f'<rect class="cell" x="{cx - (3.5 if wide else 2.2):.1f}" y="{yy:.1f}" width="{7 if wide else 4.4}" height="3" fill="#f06024"/>')
                        yy += step
    if weak:
        for (c, r) in ((1, 0), (0, 2)):
            x0, y0 = die + c * rw + rnd.uniform(8, rw * .45), die + r * rh + rnd.uniform(8, rh * .45)
            out.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{rw * .4:.1f}" height="{rh * .38:.1f}" rx="2" fill="#e0b52a" fill-opacity=".10" stroke="#e0b52a" stroke-width="1.2" stroke-dasharray="4 3"/>')
    # the sweep: a faint band that moves down the die
    out.append(f'<g class="sweep"><rect x="{die}" y="{die - 14}" width="{W - 2 * die}" height="14" fill="url(#{uid}-sw)"/></g>')
    out.append(f'<defs><linearGradient id="{uid}-sw" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f06024" stop-opacity="0"/><stop offset="1" stop-color="#f06024" stop-opacity=".45"/></linearGradient>'
               f'<clipPath id="{uid}-clip"><rect x="{die}" y="{die}" width="{W - 2 * die}" height="{W - 2 * die}"/></clipPath></defs>')
    out.append('</svg>')
    svg = "".join(out)
    return svg.replace('<g class="sweep">', f'<g class="sweep" clip-path="url(#{uid}-clip)">')



def hero_stack(uid="hero"):
    """Home hero visual: the chip in front, that chip's own screen behind, its weakest element linked to the slack map."""
    # from a cell on the die to the ringed element on the chip's slack map; the points are measured on the page
    # (1200 to 1600 px wide, where the overlay is drawn) and the overlay is hidden below that
    link = ('<svg class="link" viewBox="0 0 700 540" preserveAspectRatio="none" aria-hidden="true">'
            '<path d="M282 303 C 370 262, 520 268, 606 307"/><circle cx="282" cy="303" r="4.5"/><circle cx="606" cy="307" r="3"/></svg>')
    tags = ('<div class="tag tag--chip"><span class="dot"></span>Measured in-system<br><small>every LUT and carry chain, at speed</small></div>'
            '<div class="tag tag--device"><span class="dot dot--gold"></span>Per-device result<br><small>example: worst slack 8.2%, at X84Y212</small></div>')
    return (f'<figure class="figure hero-figure"><div class="hero-stack">{mock("device")}<div class="hero-chip">{fabric_svg(uid + "-fab")}</div>{link}{tags}</div>'
            f'<figcaption class="mock-caption">Illustrative screen with example data.</figcaption></figure>')


def team_grid():
    out = ['<div class="team-rail" id="team"><div class="team">']
    for t in C.TEAM:
        creds = "".join(f'<li>{esc(c)}</li>' for c in t["creds"])
        links = ""
        for kind, url in t.get("links", []):
            if not url:
                continue
            ic, lbl, cls = {"linkedin": (LINKEDIN, "LinkedIn", "social--li"), "scholar": (SCHOLAR, "Google Scholar", "social--gs"), "penn": (PENN, "Penn faculty page", "social--penn")}[kind]
            links += f'<a class="social {cls}" href="{url}" rel="noopener" aria-label="{esc(t["name"])} on {lbl}" title="{lbl}">{ic}</a>'
        out.append(f'<article class="person"><img class="photo" src="/assets/img/team/{t["slug"]}.jpg" alt="{esc(t["name"])}" width="128" height="128">'
                   f'<div class="who"><h3>{esc(t["name"])}</h3><span class="role">{esc(t["role"])}</span><p>{esc(t["bio"])}</p><ul class="creds" aria-label="Credentials">{creds}</ul><div class="links">{links}</div></div></article>')
    out.append('</div><div class="team-nav"><button type="button" data-rail="-1" aria-label="Previous team member"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M15 6l-6 6 6 6"/></svg></button><button type="button" data-rail="1" aria-label="Next team member"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg></button></div></div>')
    return "".join(out)


def prize_quote():
    q, who = C.PRIZE_QUOTE
    return f'<figure class="quote"><blockquote>{esc(q)}</blockquote><figcaption>{esc(who)}. {cite("penn")}</figcaption></figure>'


def whynow():
    out = ['<div class="whynow">']
    for v, t, d, href in C.WHYNOW:
        out.append(f'<div><div class="v">{esc(v)}</div><h3>{esc(t)}</h3><p>{esc(d)}</p><a class="arrow-link" href="{href}">Read more</a></div>')
    out.append('</div>')
    out.append('<p class="footnote mt-20">Margin and precision figures are Fluid Silicon measurements and vary with variation pattern, workload, vendor and age.</p>')
    return "".join(out)


def culture_grid():
    return '<div class="culture">' + "".join(f'<div>{icon_box(ic)}<div><h3>{esc(t)}</h3><p>{esc(d)}</p></div></div>' for ic, t, d in C.CULTURE) + '</div>'



def industries_all():
    """All six industries on one page, each an anchored section: lead, three figures, four pillars, the solutions that apply."""
    jump = '<nav class="jump" aria-label="Industries on this page">' + "".join(f'<a href="#{i["slug"]}">{esc(i["name"])}</a>' for i in C.INDUSTRIES) + '</nav>'
    out = [f'<div class="sec--tight sec--line"><div class="wrap" style="padding-block:16px">{jump}</div></div>']
    for n, i in enumerate(C.INDUSTRIES):
        stats = "".join(f'<div><div class="v">{esc(v)}</div><div class="k">{esc(k)}</div></div>' for v, k in i["stats"])
        pillars = "".join(f'<div class="feature">{icon_box(ic)}<h3>{esc(t)}</h3><p>{esc(d)}</p></div>' for ic, t, d in i["pillars"])
        sols = "".join(f'<a class="sol-chip" href="/solutions/{sl}/">{icon_box(C.SOL[sl]["icon"])}<span>{esc(C.SOL[sl]["name"])}</span></a>' for sl in i["modules"][:4])
        art = photo_or_art(i["art"], i["slug"], f"ind-{i['slug']}")
        raised = " sec--raised" if n % 2 else ""
        out.append(f'''<section class="sec{raised} ind-sec" id="{i["slug"]}" aria-labelledby="ind-{i["slug"]}-h">
  <div class="wrap">
    <div class="ind-head">
      <div class="stack">
        <p class="kicker">Industry</p>
        <h2 id="ind-{i["slug"]}-h">{esc(i["name"])}</h2>
        <p class="lead">{esc(i["lead"])}</p>
        <div class="ind-stats">{stats}</div>
      </div>
      <div class="ind-art" aria-hidden="true">{art}</div>
    </div>
    <div class="grid grid-4 mt-28">{pillars}</div>
    <div class="ind-sols"><span class="lbl">Solutions that apply</span>{sols}</div>
  </div>
</section>''')
    return "".join(out)


# ------------------------------------------------------------------ structure v3 components
def photo_or_art(kind, name, uid, alt=""):
    """A stock photo drops in when src/assets/img/photos/<name>.jpg exists; otherwise the drawn scene."""
    photo = os.path.join(SRC, "assets", "img", "photos", f"{name}.jpg")
    if os.path.exists(photo):
        return f'<img class="photo" src="/assets/img/photos/{name}.jpg" alt="{esc(alt)}" loading="lazy" width="1280" height="800">'
    return S.industry_art(kind, uid)


def metrics(items, note="", cols=6):
    cls = "metrics metrics--3" if cols == 3 else "metrics"
    out = [f'<div class="{cls}" role="list">']
    for v, k in items:
        sup = '<sup>*</sup>' if v.endswith("*") else ""
        out.append(f'<div class="metric" role="listitem"><div class="v">{esc(v.rstrip("*"))}{sup}</div><div class="k">{esc(k.rstrip("*"))}{"*" if k.endswith("*") else ""}</div></div>')
    out.append('</div>')
    if note:
        out.append(f'<p class="footnote">{note}</p>')
    return "".join(out)


HOME_METRICS = [
    (FACTS["margin"] + "*", "timing margin a chip carries today for the worst-case corner"),
    (FACTS["precision"], "per-link measurement precision, error plus drift"),
    (FACTS["sweep"], "to measure every logic element on a chip"),
    (FACTS["lut"], "of LUTs, and under 5% of flip-flops, on a production shell"),
    (FACTS["delay"], "delay impact on your design"),
    ("0", "downtime while monitoring runs"),
]
METRIC_NOTE = "*Fluid Silicon measurements. Varies with variation pattern, workload, vendor and device age."


def problem_grid():
    """The home page's problem cards: the production problem as the headline, the solution that answers it as the link."""
    out = ['<div class="sol-grid">']
    for sdef in C.SOLUTIONS:
        t, d = sdef["problem"]
        out.append(f'<a class="sol-card" href="/solutions/{sdef["slug"]}/">{icon_box(sdef["icon"])}<h3>{esc(t)}</h3><p>{esc(d)}</p>'
                   f'<span class="go">{esc(sdef["name"])}</span></a>')
    out.append('</div>')
    return "".join(out)


def sol_grid(current=None, icons=False, dark=False):
    cls = "sol-grid sol-grid--icons" if icons else "sol-grid"
    out = [f'<div class="{cls}">']
    for sdef in C.SOLUTIONS:
        cur = " is-current" if sdef["slug"] == current else ""
        body = f'{icon_box(sdef["icon"])}<h3>{esc(sdef["name"])}</h3>'
        if not icons:
            body += f'<p>{esc(sdef["short"])}</p><span class="go">Explore</span>'
        out.append(f'<a class="sol-card{cur}" href="/solutions/{sdef["slug"]}/">{body}</a>')
    out.append('</div>')
    return "".join(out)


def ind_grid(current=None, tiles=True, limit=None):
    items = C.INDUSTRIES if limit is None else C.INDUSTRIES[:limit]
    if tiles:
        out = ['<div class="ind-grid">']
        for i in items:
            art = photo_or_art(i["art"], i["slug"], f"tile-{i['slug']}", alt="")
            out.append(f'<a class="ind-tile" href="/industries/#{i["slug"]}">{art}{icon_box(i["icon"])}<h3>{esc(i["name"])}</h3><p>{esc(i["short"])}</p><span class="go">Explore {esc(i["name"])} solutions</span></a>')
        out.append('</div>')
        return "".join(out)
    out = ['<div class="sol-grid sol-grid--icons">']
    for i in items:
        cur = " is-current" if i["slug"] == current else ""
        out.append(f'<a class="sol-card{cur}" href="/industries/#{i["slug"]}">{icon_box(i["icon"])}<h3>{esc(i["name"])}</h3></a>')
    out.append('</div>')
    return "".join(out)


def res_card(key, uid):
    r = C.RESOURCES[key]
    go = "Download" if r["path"].endswith(".pdf") else "Read"
    return (f'<a class="res-card" href="{r["path"]}" data-type="{esc(r["type"])}">{S.thumb(r["thumb"], uid)}<div class="body"><span class="type">{esc(r["type"])}</span>'
            f'<h3>{esc(r["title"])}</h3><p>{esc(r["desc"])}</p><span class="go">{go}</span></div></a>')


def res_grid(keys, uid="res"):
    cls = "res-grid res-grid--1" if len(keys) == 1 else "res-grid"
    return f'<div class="{cls}">' + "".join(res_card(k, f"{uid}-{n}") for n, k in enumerate(keys)) + '</div>'


def res_feature(key="brief", uid="feat"):
    r = C.RESOURCES[key]
    return (f'<div class="res-feature">{S.thumb(r["thumb"], uid)}<div class="stack"><span class="type">{esc(r["type"])}</span><h2>{esc(r["title"])}</h2>'
            f'<p>{esc(r["desc"])}</p><div class="btn-row"><a class="btn btn--primary" href="{r["path"]}">{"Download the brief (PDF)" if key == "brief" else "Read it"} {ARROW}</a></div></div></div>')


def news_cards(n=3):
    out = ['<div class="news-grid">']
    for item in C.NEWS[:n]:
        ext = ' rel="noopener"' if item["path"].startswith("http") else ""
        out.append(f'<a class="news-card" href="{item["path"]}"{ext}><span class="date">{esc(item["label"])}</span><h3>{esc(item["title"])}</h3><p>{esc(item["excerpt"])}</p><span class="src">{esc(item["source"])}</span></a>')
    out.append('</div>')
    return "".join(out)


def news_list(kinds=None):
    out = ['<div class="news-list">']
    for item in C.NEWS:
        if kinds and item["kind"] not in kinds:
            continue
        ext = ' rel="noopener"' if item["path"].startswith("http") else ""
        out.append(f'<article class="news-item"><span class="date">{esc(item["label"])}</span><div><h3><a href="{item["path"]}"{ext}>{esc(item["title"])}</a></h3><p>{esc(item["excerpt"])}</p><span class="src">{esc(item["source"])}</span></div></article>')
    out.append('</div>')
    return "".join(out)


def badges():
    items = ["AMD 7-series", "AMD UltraScale", "AMD UltraScale+", "Altera Agilex 7", "AMD Vivado and Altera Quartus flows", "Research origin: University of Pennsylvania"]
    return '<div class="badges">' + "".join(f'<span>{esc(i)}</span>' for i in items) + '</div>'


def quotes(keys):
    if not keys:
        return ""
    texts = {
        "fpga26": "Microsoft therefore maintains many FPGA parts and families in production simultaneously, supporting multiple board generations for a decade or longer. Currently, Azure has 5 generations of FPGA boards actively in deployment.",
        "nsdi": "Azure Accelerated Networking ... has been deployed on all new Azure servers since late 2015, on more than one million hosts.",
    }
    out = ['<div class="quote-grid">']
    for k in keys:
        out.append(f'<figure class="quote"><blockquote>{esc(texts[k])}</blockquote><figcaption>{cite(k)}</figcaption></figure>')
    out.append('</div>')
    return "".join(out)


def faq(items, open_first=True):
    out = ['<div class="faq">']
    for n, (q, a) in enumerate(items):
        a_html = a.replace("See device support.", 'See <a href="/technology/devices/">device support</a>.').replace("See security and integration.", 'See <a href="/technology/security/">security and integration</a>.').replace("Ask for a technical session.", '<a href="/demo/">Ask for a technical session.</a>')
        op = " open" if (open_first and n == 0) else ""
        out.append(f'<details{op}><summary>{esc(q)}</summary><div class="a"><p>{a_html}</p></div></details>')
    out.append('</div>')
    return "".join(out)


def tabs(uid, panels):
    """panels: list of (label, text_html, media_html). With JavaScript, one panel at a time; without, all in order."""
    btns, pans = [], []
    for n, (label, text, media) in enumerate(panels):
        sel = "true" if n == 0 else "false"
        btns.append(f'<button type="button" class="tab-btn" role="tab" id="{uid}-tab-{n}" aria-selected="{sel}" aria-controls="{uid}-panel-{n}">{esc(label)}</button>')
        hid = "" if n == 0 else " hidden"
        pans.append(f'<div class="tab-panel" role="tabpanel" id="{uid}-panel-{n}" aria-labelledby="{uid}-tab-{n}"{hid}><div class="stack"><h3>{esc(label)}</h3>{text}</div><div class="module-media">{media}</div></div>')
    return f'<div class="tabs" data-tabs="{uid}"><div class="tab-list" role="tablist">{"".join(btns)}</div>{"".join(pans)}</div>'


def visual(spec):
    """'kind:arg' → the component's HTML, so content.py can name a visual without writing HTML."""
    name, _, arg = spec.partition(":")
    return COMPONENTS[name](arg)


def module(n, text_html, media_html, anchor="", compact=False):
    flip = " module--flip" if n % 2 else ""
    comp = " module--compact" if compact else ""
    idattr = f' id="{anchor}"' if anchor else ""
    return f'<div class="module{flip}{comp}"{idattr}><div class="module-text">{text_html}</div><div class="module-media">{media_html}</div></div>'


def solution_page(sdef):
    slug = sdef["slug"]
    apps = "".join(f'<a class="app" href="#{i}">{icon_box(ic)}<h3>{esc(t)}</h3><p>{esc(d)}</p><span class="go">Learn more</span></a>' for i, ic, t, d in sdef["apps"])
    dives = []
    for n, d in enumerate(sdef["dives"]):
        bl = "".join(f"<li>{esc(b)}</li>" for b in d["bullets"])
        sub = f'<div class="sub"><h4>{esc(d["sub"][0])}</h4><p>{esc(d["sub"][1])}</p></div>' if d.get("sub") else ""
        cta_t, cta_h = d["cta"]
        cls = "btn btn--primary" if cta_h == "/demo/" else "btn btn--ghost"
        text = (f'<p class="kicker">{esc(d["kicker"])}</p><h3>{esc(d["title"])}</h3><ul class="bullets">{bl}</ul>{sub}'
                f'<div class="btn-row"><a class="{cls}" href="{cta_h}">{esc(cta_t)}{" " + ARROW if cls.endswith("primary") else ""}</a></div>')
        dives.append(module(n, text, visual(d["visual"]), anchor=d["id"]))
    body = f"""<section class="hero on-dark hero--inner" aria-labelledby="sol-h1">
  <div class="wrap">
    <div class="hero-copy">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span aria-hidden="true">/</span><a href="/solutions/">Solutions</a><span aria-hidden="true">/</span><span>{esc(sdef["name"])}</span></nav>
      <p class="kicker">Solution</p>
      <h1 id="sol-h1">{esc(sdef["name"])}</h1>
      <p class="lead">{esc(sdef["lead"])}</p>
      <div class="btn-row"><a class="btn btn--primary" href="/demo/">Request a demo {ARROW}</a><a class="btn btn--ghost" href="/assets/docs/fluid-silicon-technical-brief.pdf">Technical brief (PDF)</a></div>
    </div>
    <div class="hero-visual">{S.card_illustration(f"hero-{slug}")}</div>
  </div>
</section>

<section class="sec" aria-labelledby="sol-impact">
  <div class="wrap">
    <div class="sec-head"><p class="kicker">Measured impact</p><h2 id="sol-impact">On production shells, at realistic utilization.</h2></div>
    {metrics(sdef["impact"], METRIC_NOTE, cols=3)}
  </div>
</section>

<section class="sec sec--raised" aria-labelledby="sol-apps">
  <div class="wrap">
    <div class="sec-head"><p class="kicker">Applications</p><h2 id="sol-apps">Four applications, one measurement.</h2></div>
    <div class="apps">{apps}</div>
  </div>
</section>

<section class="sec" aria-label="Applications in depth">
  <div class="wrap">{"".join(dives)}</div>
</section>

<section class="sec sec--raised" aria-labelledby="sol-ind">
  <div class="wrap">
    <div class="sec-head"><p class="kicker">Industries</p><h2 id="sol-ind">Where it applies.</h2></div>
    {ind_grid(tiles=False)}
  </div>
</section>

<section class="sec" aria-labelledby="sol-res">
  <div class="wrap">
    <div class="eyebrow-row"><h2 id="sol-res">Resources</h2><a class="arrow-link" href="/blog/">Blog</a></div>
    {res_grid(sdef["resources"], uid=f"res-{slug}")}
  </div>
</section>

<section class="sec sec--raised" aria-labelledby="sol-faq">
  <div class="wrap split split--top">
    <div class="stack"><p class="kicker">FAQ</p><h2 id="sol-faq">Common questions.</h2><p class="muted">Sensor architecture, deployment mechanics and calibration methods are shared with evaluation partners under NDA.</p></div>
    {faq(sdef["faq"])}
  </div>
</section>

{cta_band()}"""
    meta = {"path": f"/solutions/{slug}/", "nav": "solutions", "doc_title": f"{sdef['name']} | Fluid Silicon", "description": sdef["lead"][:150].rsplit(" ", 1)[0] + "."}
    return meta, body


MODULE_VISUAL = {
    "card-qualification": "illus:illus-{u}", "power-performance": "margin_half:margin-{u}",
    "reliability-availability-serviceability": "mock_light:fleet|Fleet overview with healthy, watch and action counts. Illustrative screen.",
    "failure-prediction-diagnostics": "aging_c:aging-{u}", "fleet-operations": "device_summary:devsum-{u}",
    "lifecycle-second-life": "aging_c:aging-lc-{u}",
}


def industry_page(idef):
    slug = idef["slug"]
    stats = "".join(f'<div><div class="v">{esc(v)}</div><div class="k">{esc(k)}</div></div>' for v, k in idef["stats"])
    pillars = "".join(f'<div class="feature">{icon_box(ic)}<h3>{esc(t)}</h3><p>{esc(d)}</p></div>' for ic, t, d in idef["pillars"])
    mods = []
    for n, sslug in enumerate(idef["modules"]):
        sdef = C.SOL[sslug]
        bl = "".join(f"<li>{esc(b)}</li>" for b in C.MODULE_BULLETS[sslug])
        text = (f'<p class="kicker">{esc(sdef["name"])}</p><h3>{esc(sdef["short"])}</h3><ul class="bullets">{bl}</ul>'
                f'<p><a class="arrow-link" href="/solutions/{sslug}/">Explore {esc(sdef["name"] if sdef["name"] != "Reliability, Availability, Serviceability" else "RAS")}</a></p>')
        mods.append(module(n, text, visual(MODULE_VISUAL[sslug].replace("{u}", slug)), compact=True))
    q = quotes(idef["quotes"])
    qsec = f"""<section class="sec" aria-labelledby="ind-ctx">
  <div class="wrap">
    <div class="sec-head"><p class="kicker">Context</p><h2 id="ind-ctx">From the largest deployments.</h2></div>
    {q}
    <p class="footnote mt-20">Cited for context. Fluid Silicon is not affiliated with Microsoft.</p>
  </div>
</section>
""" if q else ""
    body = f"""<section class="hero on-dark hero--inner hero--art" aria-labelledby="ind-h1">
  <div class="hero-art" aria-hidden="true">{photo_or_art(idef["art"], idef["slug"], f"hero-{slug}")}</div>
  <div class="wrap">
    <div class="hero-copy">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span aria-hidden="true">/</span><a href="/industries/">Industries</a><span aria-hidden="true">/</span><span>{esc(idef["name"])}</span></nav>
      <p class="kicker">Industry</p>
      <h1 id="ind-h1">{esc(idef["name"])}</h1>
      <p class="lead">{esc(idef["lead"])}</p>
      <div class="btn-row"><a class="btn btn--primary" href="/demo/">Request a demo {ARROW}</a><a class="btn btn--ghost" href="/assets/docs/fluid-silicon-technical-brief.pdf">Technical brief (PDF)</a></div>
      <div class="hero-stats">{stats}</div>
    </div>
  </div>
</section>

<section class="sec" aria-labelledby="ind-pillars">
  <div class="wrap">
    <div class="sec-head"><p class="kicker">Why it matters here</p><h2 id="ind-pillars">What {esc(idef["name"].lower() if not idef["name"].isupper() else idef["name"])} teams get.</h2></div>
    <div class="grid grid-4">{pillars}</div>
  </div>
</section>

<section class="sec sec--raised" aria-labelledby="ind-sol">
  <div class="wrap">
    <div class="sec-head"><p class="kicker">By solution</p><h2 id="ind-sol">What applies to {esc(idef["name"].lower() if not idef["name"].isupper() else idef["name"])}.</h2></div>
    {"".join(mods)}
  </div>
</section>

{qsec}
<section class="sec sec--raised" aria-labelledby="ind-res">
  <div class="wrap">
    <div class="eyebrow-row"><h2 id="ind-res">Featured resources</h2><a class="arrow-link" href="/resources/">More resources</a></div>
    {res_grid(idef["resources"], uid=f"res-{slug}")}
  </div>
</section>

<section class="sec" aria-labelledby="ind-tech">
  <div class="wrap split">
    <div class="stack"><p class="kicker">Technology</p><h2 id="ind-tech">One health layer, four capabilities.</h2></div>
    <div class="stack"><p class="lead">Per-element timing measured on the chip, an aging model per card, and tuning and repair that run only in windows you schedule. Under 1% of LUTs, no downtime, AMD and Altera.</p><p><a class="arrow-link" href="/technology/">How it works</a></p></div>
  </div>
</section>

{cta_band()}"""
    meta = {"path": f"/industries/{slug}/", "nav": "solutions", "doc_title": f"{idef['name']} | Fluid Silicon", "description": idef["lead"][:150].rsplit(" ", 1)[0] + "."}
    return meta, body


def jobs_list():
    depts = sorted({j["dept"] for j in C.JOBS})
    types = sorted({j["type"] for j in C.JOBS})
    sel_d = "".join(f'<option value="{d}">{d}</option>' for d in depts)
    sel_t = "".join(f'<option value="{t}">{t}</option>' for t in types)
    rows = "".join(f'<li data-dept="{j["dept"]}" data-type="{j["type"]}"><a href="{j["path"]}"><span><span class="t">{esc(j["title"])}</span><br><span class="m">{esc(j["type"])} · {esc(j["dept"])} · {esc(j["loc"])} · On-site</span></span><span class="go">View role →</span></a></li>' for j in C.JOBS)
    return (f'<div class="jobs-filters" data-jobs-filters><div class="field"><label for="jobs-dept">Department</label><select id="jobs-dept" data-jobs-f="dept"><option value="all">All departments</option>{sel_d}</select></div>'
            f'<div class="field"><label for="jobs-type">Type</label><select id="jobs-type" data-jobs-f="type"><option value="all">All types</option>{sel_t}</select></div></div>'
            f'<ul class="jobs" data-jobs>{rows}</ul><p class="count-note" data-jobs-count aria-live="polite">Showing all {len(C.JOBS)} roles.</p>')


def values_grid():
    return '<div class="values">' + "".join(f'<div class="feature">{icon_box(ic)}<h3>{esc(t)}</h3><p>{esc(d)}</p></div>' for ic, t, d in C.VALUES) + '</div>'


def benefits_grid():
    out = ['<div class="benefits">']
    for ic, t, d in C.BENEFITS:
        out.append(f'<div class="benefit">{icon_box(ic)}<h3>{esc(t)}</h3><p>{expand(d) if "{{" in d else esc(d)}</p></div>')
    out.append('</div>')
    return "".join(out)


def presskit():
    return (f'<div class="kit">'
            f'<div class="kit-item"><div class="swatch swatch--light">{logo_svg("kit-light")}</div><h3>Logo on light</h3><p>SVG, for white and light backgrounds.</p><a href="/assets/img/logo-on-light.svg" download>Download SVG</a></div>'
            f'<div class="kit-item"><div class="swatch swatch--dark">{logo_svg("kit-dark", "dark")}</div><h3>Logo on dark</h3><p>SVG, for charcoal and dark backgrounds.</p><a href="/assets/img/logo-on-dark.svg" download>Download SVG</a></div>'
            f'<div class="kit-item"><div class="swatch swatch--orange"><img src="/assets/img/icon-192.png" width="64" height="64" alt="The Fluid Silicon mark: an IC package with an F traced in its pins"></div><h3>Mark</h3><p>PNG at 192 and 512 px, and SVG.</p><a href="/assets/img/mark.svg" download>Download SVG</a></div>'
            f'</div>')


def location_card():
    return ('<div class="location"><h3>Philadelphia, PA</h3><p>Fluid Silicon is based in Philadelphia, close to the University of Pennsylvania, where the research behind the platform began.</p>'
            f'<p><a href="mailto:{FACTS["contact"]}">{FACTS["contact"]}</a></p></div>')


def tech_tabs(which):
    P = lambda *ps: "".join(f"<p>{x}</p>" for x in ps)
    if which == "integration":
        panels = [
            ("Reserve", P("A small region of the device is reserved for the health layer: under 1% of LUTs and under 5% of flip-flops on a production shell.",
                          "How much, and where, is planned with your team during evaluation. This is the one thing integration asks of your build; your logic, routing and I/O are not touched."), S.card_illustration("tab-reserve")),
            ("Integrate", P("The health layer is added beside a design that is already in production, through the vendor's own flow: AMD Vivado for AMD parts, Altera Quartus for Altera parts.",
                            "No RTL changes, no new silicon, no JTAG exposure, and under 2% delay impact on your design."), S.card_illustration("tab-integrate")),
            ("Deploy", P("The platform runs on your site. Telemetry leaves each card in one vendor-neutral schema and lands in your existing monitoring; nothing leaves your network.",
                         "Read-only is the default. Voltage scaling, frequency scaling and repair are enabled separately, by policy; every action is scheduled and handshake-gated."), mock_figure("fleet|Fleet overview after deployment. Illustrative screen.", light=True)),
        ]
        return tabs("tabs-int", panels)
    if which == "characterization":
        panels = [
            ("Incoming", P("Every LUT and carry block measured at speed on arrival, about a second per card, in staging.",
                           "A per-card timing and variation report, read-only. Tail cards are known on day one."), margin_half_figure("margin-tab-in")),
            ("Weak-resource maps", P("Measured slack mapped across the chip's logic elements, with random, systematic and spatial variation shown separately.",
                                     "The map guides your next place-and-route, so critical paths avoid weak regions, and is re-measured for the life of the card. Your current build is not touched."), fabric_svg("fabric-map", weak=True)),
            ("Exit", P("Cards leaving service are measured the same way, so the exit report compares directly with the incoming one.",
                       "Evidence for warranty, vendor feedback, and resale, reuse or retirement decisions."), S.card_illustration("tab-exit")),
        ]
        return tabs("tabs-char", panels)
    panels = [
        ("Monitor", P("Every logic element swept in about a second while the design runs. One metric on every vendor: measured slack as a share of the clock period."), mock_figure("device|One chip: its slack map, its weakest element and that element's history. Illustrative screen.", light=True)),
        ("Model", P("An aging curve per card and per element, fitted to the card's own temperature history, with a predicted time-to-threshold. Outliers are flagged early."), aging_figure("aging-tab", compact=True)),
        ("Tune", P("Voltage and frequency held within the margin each device has measured, in windows you schedule, coordinated per device, per board or fleet-wide. Every change is re-measured."), mock_figure("tune|A recommended operating point awaiting approval. Illustrative screen.", light=True)),
        ("Repair", P("Nothing in your design moves until an element degrades toward your threshold. Then only that path is moved to a healthy resource, through your change process, and the card is re-measured within a second."), S.card_illustration("tab-repair")),
    ]
    return tabs("tabs-field", panels)


def search_index(pages):
    idx = []
    kinds = {"solutions": "Solution", "technology": "Technology", "resources": "Resource", "company": "Company", "partners": "Partners", "careers": "Careers", "demo": "Contact"}
    for meta, body in pages:
        if meta.get("noindex"):
            continue
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
        title = re.sub(r"<[^>]+>", "", h1.group(1)).strip() if h1 else meta["doc_title"].split(" | ")[0]
        nav = meta.get("nav", meta["route"])
        kind = "Industry" if meta["path"].startswith("/industries/") else "Blog" if meta["path"].startswith("/blog/") and meta["path"] != "/blog/" else kinds.get(nav, "Page")
        idx.append({"t": html.unescape(title), "d": meta["description"], "u": meta["path"], "p": meta["route"], "k": kind})
    r = C.RESOURCES["brief"]
    idx.append({"t": r["title"], "d": r["desc"], "u": r["path"], "p": "brief", "k": "Technical brief"})
    return idx

COMPONENTS = {
    "spec_strip": lambda a: spec_strip(),
    "spec_strip_bare": lambda a: spec_strip(note=False),
    "device_table": lambda a: device_table(a or "devices"),
    "device_summary": lambda a: device_table(a or "devsum", filters=False, compact=True),
    "cta": lambda a: cta_band(),
    "cta_careers": lambda a: cta_band("Help build hardware people can trust.", "FPGA and systems engineers, and interns, in Philadelphia. We reply to every application within five business days.", brief=False).replace('href="/demo/">Request a demo', 'href="/careers/">See open roles'),
    "lifecycle": lambda a: lifecycle(),
    "mock": lambda a: mock_figure(a),
    "mock_light": lambda a: mock_figure(a, light=True),
    "icon": lambda a: icon_box(a),
    "ic": lambda a: S.icon(a),
    "illus": lambda a: S.card_illustration(a or "illus"),
    "margin": lambda a: margin_figure(a),
    "aging": lambda a: aging_figure(a),
    "aging_c": lambda a: aging_figure(a, compact=True),
    "margin_half": lambda a: margin_half_figure(a),
    "eeo": lambda a: eeo(),
    "about": lambda a: about_blurb(),
    "cite": lambda a: cite(a),
    "arrow": lambda a: ARROW,
    "email": lambda a: FACTS["contact"],
    "careers_email": lambda a: FACTS["careers"],
    "updated": lambda a: "September 2026",
    "metrics_home": lambda a: metrics(HOME_METRICS, METRIC_NOTE),
    "sol_grid": lambda a: sol_grid(current=a or None),
    "problem_grid": lambda a: problem_grid(),
    "sol_icons": lambda a: sol_grid(current=a or None, icons=True),
    "ind_grid": lambda a: ind_grid(tiles=True),
    "ind_icons": lambda a: ind_grid(current=a or None, tiles=False),
    "res_grid": lambda a: res_grid([k.strip() for k in a.split(",")], uid="res-" + a.replace(",", "-")[:24]),
    "res_feature": lambda a: res_feature(a or "brief", uid="feat-" + (a or "brief")),
    "res_all": lambda a: res_grid(list(C.RESOURCES), uid="res-all"),
    "news_cards": lambda a: news_cards(int(a) if a else 3),
    "news_list": lambda a: news_list(a.split(",") if a else None),
    "badges": lambda a: badges(),
    "quotes": lambda a: quotes(a.split(",")),
    "tech_faq": lambda a: faq(C.TECH_FAQ),
    "jobs": lambda a: jobs_list(),
    "values": lambda a: values_grid(),
    "benefits": lambda a: benefits_grid(),
    "presskit": lambda a: presskit(),
    "location": lambda a: location_card(),
    "tech_tabs": lambda a: tech_tabs(a),
    "industries_all": lambda a: industries_all(),
    "hero_stack": lambda a: hero_stack(a or "hero"),
    "team": lambda a: team_grid(),
    "prize_quote": lambda a: prize_quote(),
    "whynow": lambda a: whynow(),
    "culture": lambda a: culture_grid(),
    "fabric": lambda a: fabric_svg(a or "fabric", weak=False),
    "fabric_weak": lambda a: fabric_svg(a or "fabric-w", weak=True),
    "art": lambda a: photo_or_art(a.split("|")[0], a.split("|")[1] if "|" in a else a.split("|")[0], "art-" + a.split("|")[0]),
}


def label_scrollers(body):
    """Horizontal scrollers (wide charts, tables) become focusable, labelled regions so keyboard users can scroll them.
    A chart is labelled by its own <title>; a table by its caption."""
    def chart(m):
        after = body[m.end():m.end() + 4000]
        t = re.search(r'<title id="([^"]+)"', after)
        label = f'aria-labelledby="{t.group(1)}"' if t else 'aria-label="Chart"'
        return f'<div class="{m.group(1)}" tabindex="0" role="region" {label} data-scroller>'
    body = re.sub(r'<div class="(scroll-x[^"]*)">', chart, body)

    def table(m):
        global _CAP_N
        _CAP_N += 1
        cid = f"cap-{_CAP_N}"
        block = m.group(0)
        if "<caption>" in block:
            block = block.replace("<caption>", f'<caption id="{cid}">', 1)
            return block.replace('<div class="table-wrap">', f'<div class="table-wrap" tabindex="0" role="region" aria-labelledby="{cid}" data-scroller>', 1)
        return block.replace('<div class="table-wrap">', '<div class="table-wrap" tabindex="0" role="region" aria-label="Table" data-scroller>', 1)
    return re.sub(r'<div class="table-wrap">.*?</table>', table, body, flags=re.S)


def expand(body):
    def rep(m):
        name, _, arg = m.group(1).partition(":")
        if name == "fill":
            key, _, text = arg.partition("|")
            return fill(key, text)
        if name not in COMPONENTS:
            raise KeyError(f"unknown component {name}")
        return COMPONENTS[name](arg)
    return re.sub(r"\{\{([a-z_]+(?::[^}]*)?)\}\}", rep, body)


# ------------------------------------------------------------------ page shell
def _tok(href):
    return ROUTES.get(href.partition("#")[0])


CUR = ' aria-current="page"'


def nav_html(active):
    items = []
    for entry in NAV:
        if entry[0] == "mega":
            _, key, label, hub, cols, foot = entry
            toks = {_tok(h) for _, links in cols for h, _, _ in links} | {_tok(hub)}
            cur = " is-current" if active in toks or active == key else ""
            col_html = []
            for heading, links in cols:
                lis = ""
                for h, t, d in links:
                    cur_a = CUR if (active == _tok(h) and "#" not in h) else ""
                    lis += f'<li><a href="{h}"{cur_a}><span class="t">{esc(t)}</span><span class="d">{esc(d)}</span></a></li>'
                hd = f'<p class="mega-h">{esc(heading)}</p>' if heading else ""
                col_html.append(f'<div class="mega-col">{hd}<ul>{lis}</ul></div>')
            if foot and foot[0] == "feature":
                r = C.RESOURCES[foot[1]]
                foot_html = f'<a class="mega-feature" href="{r["path"]}">{S.thumb(r["thumb"], "nav-" + foot[1])}<span><span class="t">{esc(r["title"])}</span><br><span class="d">{esc(r["type"])} · PDF</span></span></a>'
            elif foot:
                foot_html = f'<a class="mega-foot" href="{foot[0]}">{esc(foot[1])}</a>'
            else:
                foot_html = ""
            one = " nav-panel--one" if len(cols) == 1 else ""
            hub_cur = ' aria-current="page"' if active == key else ""
            items.append(f'<li class="nav-item"><a class="nav-link nav-nojs{cur}" href="{hub}"{hub_cur}>{label}</a>'
                         f'<button type="button" class="nav-trigger{cur}" aria-expanded="false" aria-controls="menu-{key}">{label}{CHEV}</button>'
                         f'<div class="nav-panel nav-panel--mega{one}" id="menu-{key}" hidden><div class="mega-cols">{"".join(col_html)}</div>{foot_html}</div></li>')
        else:
            _, key, label, href = entry
            cur = ' aria-current="page"' if active == key else ""
            items.append(f'<li class="nav-item"><a class="nav-link" href="{href}"{cur}>{label}</a></li>')
    DEMO_CUR = ' aria-current="page"' if active == "demo" else ""
    search = (f'<div class="search"><button type="button" class="search-btn" aria-expanded="false" aria-controls="search-box">{S.icon("search")}<span>Search</span></button>'
              f'<div class="search-box" id="search-box" hidden><label class="visually-hidden" for="search-q">Search the site</label>'
              f'<input type="search" id="search-q" placeholder="Search solutions, industries, resources" autocomplete="off">'
              f'<ul class="search-results" id="search-results" aria-label="Search results"></ul></div></div>')
    return f"""<header class="site-header">
  <div class="wrap">
    <a class="brand" href="/" aria-label="Fluid Silicon home">{logo_svg("logo-head")}</a>
    <button type="button" class="menu-btn" aria-expanded="false" aria-controls="site-nav"><span class="bars" aria-hidden="true"></span><span>Menu</span></button>
    <a class="menu-fallback" href="#footer-nav"><span class="bars" aria-hidden="true"></span><span>Menu</span></a>
    <nav class="nav" id="site-nav" aria-label="Main">
      <ul class="nav-list">{"".join(items)}</ul>
      {search}
      <div class="nav-cta"><a class="btn btn--primary" href="/demo/"{DEMO_CUR}>Request a demo</a></div>
    </nav>
  </div>
</header>"""


LEGAL_ENTITY = "Fluid Silicon Inc."      # registered name per the Sept 2026 business model deck; confirm exact form with counsel


def footer_html():
    sols = "".join(f'<li><a href="/solutions/{x["slug"]}/">{esc(x["name"])}</a></li>' for x in C.SOLUTIONS)
    inds = "".join(f'<li><a href="/industries/#{x["slug"]}">{esc(x["name"])}</a></li>' for x in C.INDUSTRIES)
    return f"""<footer class="site-footer">
  <div class="wrap">
    <div class="foot-top" id="footer-nav">
      <div class="foot-brand">
        <a class="brand" href="/" aria-label="Fluid Silicon home">{logo_svg("logo-foot", "dark")}</a>
      </div>
      <div class="foot-col"><h2>Solutions</h2><ul>{sols}<li><a href="/solutions/">All solutions</a></li></ul></div>
      <div class="foot-col"><h2>Industries</h2><ul>{inds}</ul></div>
      <div class="foot-col"><h2>Technology</h2><ul>
        <li><a href="/technology/">Overview</a></li><li><a href="/technology/security/">Security and integration</a></li>
        <li><a href="/technology/devices/">Device support</a></li>
        <li><a href="/blog/">Blog</a></li><li><a href="/assets/docs/fluid-silicon-technical-brief.pdf">Technical brief (PDF)</a></li></ul></div>
      <div class="foot-col"><h2>Company</h2><ul>
        <li><a href="/company/">About and team</a></li><li><a href="/company/#partners">Partners</a></li><li><a href="/company/news/">News and press</a></li><li><a href="/company/events/">Events</a></li>
        <li><a href="/careers/">Careers</a></li><li><a href="/contact/">Contact</a></li><li><a href="/demo/">Request a demo</a></li></ul></div>
    </div>
    <div class="foot-bottom">
      <p>© 2026 {LEGAL_ENTITY.rstrip('.')}. All rights reserved. AMD, Altera and their product names are trademarks of their respective owners. Fluid Silicon is not affiliated with or endorsed by them.</p>
      <div class="row"><a href="/terms/">Terms</a><a href="/privacy/">Privacy</a><span class="muted">Philadelphia, PA</span><a class="social social--li social--sm" href="{FACTS["linkedin"]}" rel="noopener" aria-label="Fluid Silicon on LinkedIn">{LINKEDIN}</a></div>
    </div>
  </div>
</footer>"""


ORG_LD = {
    "@context": "https://schema.org", "@type": "Organization", "name": "Fluid Silicon", "url": SITE_URL + "/",
    "logo": SITE_URL + "/assets/img/icon-512.png", "email": FACTS["contact"],
    "description": "Fluid Silicon builds FPGA health monitoring and timing measurement software: per-element timing measured on the chip while it runs, aging models, adaptive voltage and frequency scaling, and repair, for AMD and Altera FPGAs.",
    "address": {"@type": "PostalAddress", "addressLocality": "Philadelphia", "addressRegion": "PA", "addressCountry": "US"},
    "foundingLocation": {"@type": "Place", "name": "Philadelphia, PA"},
    "knowsAbout": ["FPGA health monitoring", "FPGA timing measurement", "FPGA aging", "adaptive voltage scaling", "reconfigurable computing", "process variation"],
    "sameAs": [FACTS["linkedin"], CITES["penn"][1]],
}
WEBSITE_LD = {"@context": "https://schema.org", "@type": "WebSite", "name": "Fluid Silicon", "url": SITE_URL + "/"}


def page_ld(meta, body):
    """Structured data derived from the page itself: FAQPage from any FAQ block, BlogPosting for posts."""
    out = []
    qa = re.findall(r"<details[^>]*><summary>(.*?)</summary><div class=\"a\"><p>(.*?)</p></div></details>", body, re.S)
    if qa:
        strip = lambda t: html.unescape(re.sub(r"<[^>]+>", "", t)).strip()
        out.append({"@context": "https://schema.org", "@type": "FAQPage",
                    "mainEntity": [{"@type": "Question", "name": strip(q), "acceptedAnswer": {"@type": "Answer", "text": strip(a)}} for q, a in qa]})
    if meta["path"].startswith("/blog/") and meta["path"] != "/blog/":
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
        out.append({"@context": "https://schema.org", "@type": "BlogPosting", "headline": html.unescape(re.sub(r"<[^>]+>", "", h1.group(1))).strip() if h1 else meta["doc_title"],
                    "description": meta["description"], "datePublished": POST_DATE + "T09:00:00-04:00", "dateModified": BUILD_DATE + "T09:00:00-04:00",
                    "author": {"@type": "Organization", "name": "Fluid Silicon", "url": SITE_URL + "/"},
                    "publisher": {"@type": "Organization", "name": "Fluid Silicon", "logo": {"@type": "ImageObject", "url": SITE_URL + "/assets/img/icon-512.png"}},
                    "image": SITE_URL + "/assets/img/og-image.png", "mainEntityOfPage": SITE_URL + meta["path"]})
    return out


# GitHub Pages can't send security headers, so the policy rides in a meta tag. The one inline script is allowed by its hash.
JS_FLAG = 'document.documentElement.classList.add("js")'
CSP = ("default-src 'self'; script-src 'self' 'sha256-qOhFsq0QMV2REqNwk5hGH5bZE9SkX6gt6yeyKdYPv+U='; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
       "font-src 'self'; connect-src 'self' https://script.google.com https://script.googleusercontent.com; form-action 'self'; "
       "base-uri 'self'; object-src 'none'; frame-src 'none'; manifest-src 'self'; upgrade-insecure-requests")


def head_html(meta):
    path = meta["path"]
    canon = SITE_URL + ("/404.html" if path == "/404.html" else path)
    title = meta["doc_title"]
    desc = meta["description"]
    lds = [ORG_LD, WEBSITE_LD] if path == "/" else []
    lds += meta.get("ld", [])
    lds += meta.get("auto_ld", [])
    ld = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in lds)
    robots = '<meta name="robots" content="noindex">' if meta.get("noindex") else ""
    return f'''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta http-equiv="Content-Security-Policy" content="{CSP}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<script>{JS_FLAG}</script>
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canon}">
{robots}
<meta name="theme-color" content="#ffffff">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Fluid Silicon">
<meta property="og:title" content="{esc(meta.get("og_title", title))}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{SITE_URL}/assets/img/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Fluid Silicon, a customizable platform for FPGA adaptation and resilience: at advanced nodes, every device is different.">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/assets/img/mark.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="preload" href="/assets/fonts/red-hat-display-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/red-hat-text-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/site.css">
<script src="/assets/js/config.js" defer></script>
<script src="/assets/js/site.js" defer></script>
{ld}'''


def page_doc(meta, body):
    active = meta.get("nav", meta["route"])
    return f'''<!doctype html>
<html lang="en">
<head>
{head_html(meta)}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{nav_html(active)}
<main id="main">
{body}
</main>
{footer_html()}
</body>
</html>
'''


# ------------------------------------------------------------------ pages
def load_pages():
    pages = []
    for fn in sorted(os.listdir(os.path.join(SRC, "pages"))):
        if not fn.endswith(".html"):
            continue
        raw = read(os.path.join(SRC, "pages", fn))
        m = re.match(r"\s*<!--meta\s*(\{.*?\})\s*-->", raw, re.S)
        if not m:
            raise ValueError(f"{fn}: missing meta block")
        meta = json.loads(m.group(1))
        meta["route"] = ROUTES[meta["path"]]
        body = label_scrollers(expand(raw[m.end():]))
        pages.append((meta, body))
    for sdef in C.SOLUTIONS:
        meta, body = solution_page(sdef)
        meta["route"] = ROUTES[meta["path"]]
        pages.append((meta, label_scrollers(body)))
    for meta, body in pages:
        meta["auto_ld"] = page_ld(meta, body)
    order = list(ROUTES)
    pages.sort(key=lambda mb: order.index(mb[0]["path"]))
    return pages


def out_path(base, path):
    if path.endswith(".html"):
        return os.path.join(base, path.lstrip("/"))
    return os.path.join(base, path.strip("/"), "index.html") if path != "/" else os.path.join(base, "index.html")


def write(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)


REDIRECTS = {**{f"/industries/{i['slug']}/": f"/industries/#{i['slug']}" for i in C.INDUSTRIES}, "/team/": "/company/#team", "/company/pressroom/": "/company/news/", "/partners/": "/company/#partners", "/resources/": "/blog/",
             "/jobs/fpga-engineer/": "/jobs/#fpga-engineer", "/jobs/systems-software-engineer/": "/jobs/#systems-software-engineer", "/jobs/internships/": "/jobs/#internships", "/why/": "/blog/the-fpga-margin-problem/", "/platform/": "/technology/",
             "/platform/security/": "/technology/security/", "/platform/devices/": "/technology/devices/",
             "/solutions/data-center/": "/industries/#data-center-cloud", "/solutions/aerospace-defense/": "/industries/#aerospace-defense"}


def redirect_doc(to):
    u = SITE_URL + to
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Moved | Fluid Silicon</title>'
            f'<link rel="canonical" href="{u}"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url={to}">'
            f'</head><body><p>This page has moved to <a href="{to}">{u}</a>.</p></body></html>')


def build_site(pages):
    out = os.path.join(DIST, "site")
    if os.path.exists(out):
        shutil.rmtree(out)
    shutil.copytree(os.path.join(SRC, "assets"), os.path.join(out, "assets"))
    for extra in ["CNAME", ".nojekyll", "robots.txt", "site.webmanifest", "favicon.ico", ".well-known/security.txt"]:
        src = os.path.join(SRC, extra)
        if os.path.exists(src):
            os.makedirs(os.path.dirname(os.path.join(out, extra)), exist_ok=True)
            shutil.copy(src, os.path.join(out, extra))
    for meta, body in pages:
        write(out_path(out, meta["path"]), page_doc(meta, body))
    for frm, to in REDIRECTS.items():
        write(out_path(out, frm), redirect_doc(to))
    urls = [m["path"] for m, _ in pages if m["path"] not in ("/404.html",) and not m.get("noindex")]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append(f"  <url><loc>{SITE_URL}{u}</loc><lastmod>{BUILD_DATE}</lastmod></url>")
    sm.append("</urlset>")
    write(os.path.join(out, "sitemap.xml"), "\n".join(sm) + "\n")
    write(os.path.join(out, "search-index.json"), json.dumps(search_index(pages), ensure_ascii=False))
    return out


# ------------------------------------------------------------------ preview (single file for the artifact viewer)
def to_preview_links(s):
    def href(m):
        attr, url = m.group(1), m.group(2)
        if url == "/assets/docs/fluid-silicon-technical-brief.pdf":
            return f'{attr}="#brief"'          # the viewer can't open files, so the preview shows the pages instead
        if url.startswith("/assets/") or url in ("/favicon.ico", "/site.webmanifest"):
            return f'{attr}="{url[1:]}"'
        if url.startswith("/") and not url.startswith("//"):
            path, _, frag = url.partition("#")
            path, _, query = path.partition("?")
            tok = ROUTES.get(path)
            if tok is None:
                return m.group(0)
            if query.startswith("role="):
                tok += "~" + query[5:]
            elif frag:
                tok += "~" + frag
            return f'{attr}="#{tok}"'
        return m.group(0)
    return re.sub(r'\b(href|src)="([^"]+)"', href, s)


BRIEF_PAGES = ["Cover: run every FPGA at its measured limits, with the six key figures",
               "01, the problem: why margins are set for a statistically rare chip, with the margin schematic and Azure context",
               "02, the platform: four capabilities and the health loop",
               "03, lifecycle and adoption: the health metric, specifications and the four adoption steps",
               "04, security and integration: the integration diagram and six guarantees",
               "05, devices and next steps: device support, markets and contact"]


def brief_pages(out):
    """Page images of the technical brief for the preview (the artifact viewer can't open a PDF). Needs pdftoppm; skipped without it."""
    pdf = os.path.join(SRC, "assets", "docs", "fluid-silicon-technical-brief.pdf")
    exe = shutil.which("pdftoppm")
    if not (exe and os.path.exists(pdf)):
        return []
    d = os.path.join(out, "assets", "brief")
    os.makedirs(d, exist_ok=True)
    import subprocess
    subprocess.run([exe, "-r", "110", "-png", pdf, os.path.join(d, "p")], check=True)
    return sorted(f for f in os.listdir(d) if f.endswith(".png"))


def brief_view(imgs):
    figs = "".join(f'<figure class="brief-page"><img src="assets/brief/{f}" width="935" height="1210" loading="lazy" alt="Technical brief, page {i+1} of {len(imgs)}. {esc(BRIEF_PAGES[i] if i < len(BRIEF_PAGES) else "")}"><figcaption>Page {i+1}</figcaption></figure>'
                   for i, f in enumerate(imgs))
    body = f'''<section class="page-hero" aria-labelledby="brief-h1"><div class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="#home">Home</a><span aria-hidden="true">/</span><a href="#platform">Platform</a><span aria-hidden="true">/</span><span>Technical brief</span></nav>
  <h1 id="brief-h1">Technical brief</h1>
  <p class="lead">Six pages for engineers and buyers: the problem, the platform, adoption, security and integration, and device support. On fluidsilicon.com this link opens the PDF. In this preview the pages are shown as images.</p>
</div></section>
<section class="sec" aria-label="Brief pages"><div class="wrap"><div class="brief-pages">{figs or '<p class="muted">Run tools_assets.py to generate the brief, then rebuild.</p>'}</div></div></section>'''
    return f'<div data-route="brief" data-title="Technical brief | Fluid Silicon" data-nav="platform" id="view-brief">\n{body}\n</div>'


def build_preview(pages):
    out = os.path.join(DIST, "preview")
    if os.path.exists(out):
        shutil.rmtree(out)
    shutil.copytree(os.path.join(SRC, "assets"), os.path.join(out, "assets"))
    brief_imgs = brief_pages(out)
    views = []
    for meta, body in pages:
        tok = meta["route"]
        active = meta.get("nav", tok)
        act = ' class="is-active"' if tok == "home" else ""
        views.append(f'<div data-route="{tok}" data-title="{esc(meta["doc_title"])}" data-nav="{active}" id="view-{tok}"{act}>\n{body}\n</div>')
    views.append(brief_view(brief_imgs))
    doc = f'''<title>Fluid Silicon</title>
<meta name="description" content="Preview of the Fluid Silicon website.">
<link rel="stylesheet" href="assets/css/site.css">
<script>document.documentElement.classList.add("js","is-preview");window.FS_PREVIEW=true;window.FS_INDEX={json.dumps(search_index(pages), ensure_ascii=False)};</script>
<a class="skip" href="#main">Skip to content</a>
{nav_html("home")}
<main id="main">
{"".join(views)}
</main>
{footer_html()}
<script src="assets/js/config.js"></script>
<script src="assets/js/site.js"></script>
'''
    doc = to_preview_links(doc)
    write(os.path.join(out, "index.html"), doc)
    return out


def build_standalone(prev):
    """One self-contained HTML file (styles, scripts, fonts and images inlined) to open locally or send privately."""
    import base64
    def data_uri(path, mime):
        with open(path, "rb") as f:
            return f"data:{mime};base64," + base64.b64encode(f.read()).decode()
    doc = read(os.path.join(prev, "index.html"))
    css = read(os.path.join(prev, "assets", "css", "site.css"))
    css = re.sub(r'url\("\.\./fonts/([^"]+)"\)', lambda m: 'url("' + data_uri(os.path.join(prev, "assets", "fonts", m.group(1)), "font/woff2") + '")', css)
    doc = doc.replace('<link rel="stylesheet" href="assets/css/site.css">', "<style>\n" + css + "\n</style>")
    for name in ("config.js", "site.js"):
        js = read(os.path.join(prev, "assets", "js", name)).replace("</script", "<\\/script")
        doc = doc.replace(f'<script src="assets/js/{name}"></script>', "<script>\n" + js + "\n</script>")
    doc = re.sub(r'src="(assets/(?:brief|img)/[^"]+\.(png|jpg))"', lambda m: 'src="' + data_uri(os.path.join(prev, m.group(1)), "image/png" if m.group(2) == "png" else "image/jpeg") + '"', doc)
    head, _, body = doc.partition('<a class="skip"')
    out = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
           + head.replace("<title>Fluid Silicon</title>", "<title>Fluid Silicon website preview</title>")
           + '</head>\n<body>\n<a class="skip"' + body + '\n</body>\n</html>\n')
    path = os.path.join(DIST, "fluid-silicon-preview.html")
    write(path, out)
    return path


def report_fills(pages):
    found = []
    for meta, body in pages:
        for m in re.finditer(r'data-fill="([^"]+)"', body):
            found.append((meta["path"], m.group(1)))
    return found


if __name__ == "__main__":
    pages = load_pages()
    site = build_site(pages)
    prev = build_preview(pages)
    one = build_standalone(prev)
    fills = report_fills(pages)
    print(f"built {len(pages)} pages -> {site}\npreview -> {prev}\none-file preview -> {one}")
    if fills:
        print("placeholders to fill before launch:")
        for p, k in fills:
            print(f"  {p}: {k}")
