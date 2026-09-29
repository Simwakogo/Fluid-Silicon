#!/usr/bin/env python3
"""Generate the site's binary assets from the same sources as the pages.

    python3 tools_assets.py

Writes into src/ (build.py then copies them to dist/site):
  favicon.ico, assets/img/{apple-touch-icon,icon-192,icon-512,icon-maskable-512,og-image}.png,
  assets/docs/fluid-silicon-technical-brief.pdf, site.webmanifest, robots.txt, CNAME, .nojekyll

Needs Playwright with Chromium and Pillow. Nothing here is needed at runtime.
"""
import io, json, os, re, sys, html
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import build as B          # facts, devices, logo, routes
import brief_parts as S      # the brief keeps its own frozen diagrams and stylesheet

SRC = os.path.join(ROOT, "src")
TMP = os.path.join(ROOT, "_tmp")
IMG = os.path.join(SRC, "assets", "img")
DOCS = os.path.join(SRC, "assets", "docs")
esc = html.escape
os.makedirs(TMP, exist_ok=True)
os.makedirs(DOCS, exist_ok=True)

MARK = open(os.path.join(IMG, "mark.svg"), encoding="utf-8").read()
MARK_INNER = re.search(r'<g class="fs-mark">(.*)</g></svg>', MARK, re.S).group(1)
TRACES = re.search(r'(<g fill="none" stroke="#FFFFFF".*)', MARK_INNER, re.S).group(1)
LOGO_LIGHT = re.sub(r"<title>.*?</title>", "", open(os.path.join(IMG, "logo-on-light.svg"), encoding="utf-8").read())


def svg_page(svg, size, bg="transparent"):
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0;background:{bg}}}'
            f'svg{{display:block;width:{size}px;height:{size}px}}</style></head><body>{svg}</body></html>')


def maskable_svg():
    # full-bleed orange, the F traces kept inside the 80% safe zone
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" fill="#F06024"/>'
            f'<g transform="translate(32 32) scale(.72) translate(-31 -31)">{TRACES}</g></svg>')


def write_text(path, s):
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)


# ------------------------------------------------------------------ open graph image
def og_html():
    """1200 x 630 social image: charcoal background, headline, and the chip floorplan from the site's hero."""
    FONTS = "file://" + os.path.join(B.SRC, "assets", "fonts")
    logo = B.logo_svg("og-logo", "dark")
    chip = B.fabric_svg("og-chip")
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family: "Red Hat Display"; src: url("{FONTS}/red-hat-display-latin-wght-normal.woff2"); font-weight: 300 900; }}
@font-face {{ font-family: "Red Hat Text"; src: url("{FONTS}/red-hat-text-latin-wght-normal.woff2"); font-weight: 300 700; }}
html, body {{ margin: 0; }}
.og {{ position: relative; width: 1200px; height: 630px; box-sizing: border-box; padding: 64px 0 56px 72px; display: grid; grid-template-columns: 600px 1fr; gap: 24px; align-items: center;
       background: #121212; background-image: radial-gradient(700px 420px at 82% 40%, rgba(240, 96, 36, .22), transparent 65%); font-family: "Red Hat Text", sans-serif; overflow: hidden; }}
.left {{ display: grid; gap: 22px; align-content: center; }}
.left svg {{ width: 260px; height: auto; }}
h1 {{ margin: 0; font: 650 72px/1.02 "Red Hat Display", sans-serif; letter-spacing: -0.025em; color: #f4f2ed; }}
.sub {{ margin: 0; font-size: 24px; line-height: 1.4; color: #c3bfb6; max-width: 26ch; }}
.right {{ display: grid; place-items: center; }}
.right svg {{ width: 470px; height: auto; filter: drop-shadow(0 24px 48px rgba(0, 0, 0, .6)); }}
.right .sweep {{ display: none; }}
.bar {{ position: absolute; left: 0; right: 0; bottom: 0; height: 8px; background: linear-gradient(90deg, #f06024 0 34%, #a67c00 34% 67%, #6c602a 67%); }}
</style></head><body><div class="og">
<div class="left">{logo}
<h1>See what every chip can really do.</h1>
<p class="sub">Every logic element measured while the chip runs, in production, with no downtime. Starting with AMD and Altera FPGAs.</p></div>
<div class="right">{chip}</div><div class="bar"></div></div></body></html>'''


# ------------------------------------------------------------------ technical brief (print, light theme)
BRIEF_CSS = '''
@page { size: Letter; margin: 0.62in 0.62in 0.8in; }
:root { color-scheme: light;
  --bg: #ffffff; --bg-2: #faf9f6; --panel: #ffffff; --panel-2: #f5f3ee; --line: #e3dfd6; --line-2: #cfcac0;
  --ink: #111111; --ink-2: #3a3833; --ink-3: #5f5b53;
  --gold: #8a6500; --gold-deep: #8a6500; --olive: #8c7a2e; --olive-deep: #f3ecd2;
  --orange: #d4531b; --orange-deep: #c64e00; --green: #1f8f3f; --blue: #0b78ad; }
html, body { background: #fff !important; color: var(--ink); }
body { margin: 0; font: 400 10.5pt/1.5 var(--font-text); -webkit-print-color-adjust: exact; print-color-adjust: exact; }
h1, h2, h3 { font-family: var(--font-display); color: var(--ink); margin: 0; letter-spacing: -.01em; }
h1 { font-size: 30pt; line-height: 1.05; font-weight: 600; letter-spacing: -.025em; max-width: 16ch; }
h2 { font-size: 16pt; font-weight: 600; margin: 0 0 8px; }
h3 { font-size: 11pt; font-weight: 600; margin: 0 0 4px; }
p { margin: 0 0 8px; color: var(--ink-2); }
p + p { margin-top: 0; }
a { color: var(--ink); }
.page { break-after: page; }
.page:last-child { break-after: auto; }
h2 { break-after: avoid; }
.cover { display: grid; grid-template-columns: 1.35fr .9fr; gap: 26px; align-items: center; margin-top: 8px; }
.cover-art { margin: 0; }
.cover-art svg { width: 100%; height: auto; display: block; }
.cover-art figcaption { font-size: 7.5pt; color: var(--ink-3); margin-top: 6px; text-align: center; }
.toc { margin-top: 26px; border-top: 1px solid var(--line); padding-top: 14px; }
.toc ol { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; }
.toc li { font: 600 10pt/1.3 var(--font-display); color: var(--ink); }
.toc li span { display: block; font: 600 8pt/1 var(--font-mono); color: var(--orange-deep); margin-bottom: 5px; }
.top { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--line); padding-bottom: 14px; margin-bottom: 26px; }
.top svg { height: 22px; width: auto; }
.top .bmeta { font: 500 8pt/1 var(--font-mono); letter-spacing: .12em; text-transform: uppercase; color: var(--ink-3); }
.kick { font: 600 8pt/1 var(--font-mono); letter-spacing: .14em; text-transform: uppercase; color: var(--gold); margin: 0 0 10px; }
.blead { font-size: 12.5pt; line-height: 1.5; color: var(--ink-2); max-width: 60ch; margin: 14px 0 0; }
.bsec { margin-top: 26px; }
.sec-intro { max-width: 70ch; }
.specs-b { display: grid; grid-template-columns: repeat(3, 1fr); border: 1px solid var(--line); border-radius: 8px; overflow: hidden; margin-top: 24px; }
.specs-b > div { padding: 12px 14px; border-right: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.specs-b > div:nth-child(3n) { border-right: 0; }
.specs-b > div:nth-child(n+4) { border-bottom: 0; }
.specs-b .v { font: 600 20pt/1 var(--font-display); color: var(--orange-deep); letter-spacing: -.02em; }
.specs-b .v sup { font-size: 10pt; color: var(--ink-3); }
.specs-b .k { font-size: 8.5pt; line-height: 1.35; color: var(--ink-2); margin-top: 6px; }
.fn { font-size: 7.8pt; color: var(--ink-3); margin-top: 6px; }
.cols { display: grid; gap: 14px; }
.cols-2 { grid-template-columns: 1fr 1fr; }
.cols-3 { grid-template-columns: 1fr 1fr 1fr; }
.cols-4 { grid-template-columns: 1fr 1fr 1fr 1fr; }
.box-b { border: 1px solid var(--line); border-radius: 8px; padding: 12px 14px; background: var(--bg-2); break-inside: avoid; }
.box-b p { font-size: 9.2pt; line-height: 1.45; margin: 0; }
.tag-b { font: 600 7.5pt/1 var(--font-mono); letter-spacing: .12em; text-transform: uppercase; color: var(--gold); margin: 0 0 6px !important; }
.fig { border: 1px solid var(--line); border-radius: 8px; padding: 10px; margin-top: 12px; break-inside: avoid; background: #fff; }
.fig svg { width: 100%; height: auto; display: block; }
.fig .cap { font-size: 7.8pt; color: var(--ink-3); margin: 6px 2px 0; }
.fig--loop svg { width: 84%; margin: 0 auto; }
.fig-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.legend-b { display: flex; gap: 14px; flex-wrap: wrap; font-size: 7.8pt; color: var(--ink-3); margin: 6px 2px 0; }
.legend-b i { display: inline-block; width: 14px; height: 3px; border-radius: 2px; vertical-align: 2px; margin-right: 6px; }
table.bt { width: 100%; border-collapse: collapse; font-size: 9pt; margin-top: 10px; }
table.bt th, table.bt td { text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }
table.bt thead th { font: 600 7.5pt/1.2 var(--font-mono); letter-spacing: .08em; text-transform: uppercase; color: var(--ink-3); background: var(--bg-2); }
table.bt tbody th { color: var(--ink); font-weight: 600; }
table.bt td { color: var(--ink-2); }
.st { display: inline-block; font: 600 8pt/1 var(--font-text); padding: 3px 8px; border-radius: 999px; border: 1px solid; }
.st-ok { color: #1f7a3a; border-color: #9fd3ad; background: #eef8f1; }
.st-select { color: #7a5a00; border-color: #e1c77a; background: #fbf5e2; }
.st-dev { color: #5f5b53; border-color: #d5d0c6; background: #fff; }
ol.steps-b { list-style: none; margin: 10px 0 0; padding: 0; display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; counter-reset: s; }
ol.steps-b li { counter-increment: s; border-top: 2px solid var(--orange); padding-top: 8px; break-inside: avoid; }
ol.steps-b li::before { content: "0" counter(s); font: 600 8pt/1 var(--font-mono); color: var(--orange-deep); display: block; margin-bottom: 6px; }
ol.steps-b p { font-size: 9pt; margin: 0 0 4px; }
ol.steps-b .bm { font: 500 7.5pt/1.3 var(--font-mono); color: var(--ink-3); letter-spacing: .04em; }
ul.b { margin: 6px 0 0; padding-left: 16px; }
ul.b li { color: var(--ink-2); font-size: 9.4pt; margin-bottom: 4px; }
.note-b { border-left: 3px solid var(--olive); background: var(--olive-deep); padding: 10px 14px; border-radius: 0 6px 6px 0; font-size: 9.2pt; color: var(--ink); margin-top: 14px; break-inside: avoid; }
.contact { display: grid; grid-template-columns: 1.3fr 1fr; gap: 18px; align-items: end; border-top: 1px solid var(--line); padding-top: 16px; margin-top: 22px; break-inside: avoid; }
.contact .bbig { font: 600 15pt/1.2 var(--font-display); color: var(--ink); }
.contact dl { margin: 0; display: grid; grid-template-columns: auto 1fr; gap: 4px 12px; font-size: 9.2pt; }
.contact dt { color: var(--ink-3); font: 500 7.5pt/1.8 var(--font-mono); letter-spacing: .08em; text-transform: uppercase; }
.contact dd { margin: 0; color: var(--ink); }
.quote-b { border-left: 3px solid var(--gold); padding: 4px 0 4px 14px; margin: 0; }
.quote-b blockquote { margin: 0 0 4px; font: 500 11pt/1.4 var(--font-display); color: var(--ink); }
.quote-b figcaption, .bsrc { font-size: 7.8pt; color: var(--ink-3); }
.stat-b .v { font: 600 26pt/1 var(--font-display); color: var(--orange-deep); letter-spacing: -.02em; }
/* diagrams on paper */
.dg text { fill: var(--ink-2); }
.dg .t-title, .dg .t-lbl, .dg .t-strong, .dg .t-ink, .dg .t-conv { fill: var(--ink); }
.dg .t-small { fill: var(--ink-3); }
.dg .box { fill: #f7f5f0; stroke: #cfcac0; }
.dg .box-olive { fill: #f3ecd2; stroke: #b9a55a; }
.dg .box-dark { fill: #ffffff; stroke: #cfcac0; }
.dg .zone { stroke: #c9c4b8; }
.dg .frame-prod { stroke: #b9a55a; }
.dg .loop-token { display: none; }
.dg .axis { stroke: #bdb8ad; }
.dg .grid-line { stroke: #ebe7df; }
.dg .curve-fleet { fill: rgba(60, 58, 52, .07); stroke: #6b675f; }
.dg .curve-lut { fill: rgba(11, 120, 173, .10); }
.dg .curve-carry { fill: rgba(212, 83, 27, .08); }
.dg .margin-band { fill: rgba(138, 101, 0, .14); }
.dg .scope-pill { fill: rgba(11, 120, 173, .06); stroke: rgba(11, 120, 173, .5); }
.dg .knock { stroke: #fff; }
'''


def brief_html():
    loop = S.health_loop("b-loop")
    flow = S.integration_flow("b-flow")
    ma, mb = S.margin_charts("b-margin")
    pkg, _, _ = S.hero_package("b-pkg")
    F = B.FACTS
    specs = [(F["margin"], "*", "timing margin a chip carries today to cover the worst-case corner"),
             (F["precision"], "", "per-link measurement precision, error plus drift"),
             ("≈ 1 s", "", "to measure every logic element on the chip"),
             (F["lut"], "", "of LUTs and under 5% of flip-flops on a production shell"),
             (F["delay"], "", "delay impact on your design"),
             ("0", "", "downtime while monitoring runs")]
    spec_html = "".join(f'<div><div class="v">{esc(v)}{"<sup>" + s + "</sup>" if s else ""}</div><div class="k">{esc(k)}</div></div>' for v, s, k in specs)
    st_cls = {"ok": "st-ok", "select": "st-select", "dev": "st-dev"}
    rows = "".join(f'<tr><td>{v}</td><th>{esc(f)}</th><td>{esc(n)}</td><td><span class="st {st_cls[s]}">{B.STATUS[s][0]}</span></td><td>{esc(note)}</td></tr>'
                   for v, f, n, s, note in B.DEVICES)
    nsdi_t, nsdi_u = B.CITES["nsdi"]
    f26_t, f26_u = B.CITES["fpga26"]
    top = lambda label: f'<div class="top">{LOGO_LIGHT}<span class="bmeta">{label}</span></div>'
    box = lambda tag, h, p: f'<div class="box-b"><p class="tag-b">{tag}</p><h3>{h}</h3><p>{p}</p></div>'
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Fluid Silicon technical brief</title>
<meta name="author" content="Fluid Silicon"><meta name="description" content="Timing health for FPGA fleets: what Fluid Silicon measures, what it changes and how it fits production systems.">
<link rel="stylesheet" href="../src/assets/css/brief.css"><style>{BRIEF_CSS}</style></head><body>

<section class="page" id="p1">
  {top("Technical brief · September 2026")}
  <div class="cover">
    <div>
      <p class="kick">Timing health for FPGA fleets</p>
      <h1>Run every FPGA at its measured limits.</h1>
      <p class="blead">Vendor timing models are built for the slowest die, at the hottest corner, at the end of its life. Fluid Silicon measures each of your chips in production, at speed and with no downtime, so you can reclaim margin, see failure coming and retire hardware on evidence.</p>
    </div>
    <figure class="cover-art">{pkg}<figcaption>Illustrative die. Each cell stands for one logic element's measured slack.</figcaption></figure>
  </div>
  <div class="specs-b">{spec_html}</div>
  <p class="fn">*Fluid Silicon measurements. Varies with variation pattern, workload, vendor and device age.</p>
  <div class="toc"><p class="kick">In this brief</p><ol>
    <li><span>01</span>The problem</li><li><span>02</span>The platform</li><li><span>03</span>Lifecycle and adoption</li>
    <li><span>04</span>Security and integration</li><li><span>05</span>Devices and next steps</li></ol></div>
</section>

<section class="page" id="p2">
  {top("01 · The problem")}
  <h2>Margins are set once, for a chip that is statistically rare.</h2>
  <p class="sec-intro">Vendor timing models cover the worst die: highly defective, at elevated voltage, at high temperature and at the end of its life. Most of your chips are nowhere near that corner, yet every one of them runs as if it were.</p>
  <div class="cols cols-3" style="margin-top:12px">
    {box("Variation", "Variation you only see at scale", "At 16, 14 and 7 nm, defects show up as more than 20% random variation on top of systematic variation. A fleet-wide margin has to cover the worst chip.")}
    {box("Aging", "Aging nobody measured", "Timing drifts with time, temperature and voltage. Cards now stay in service six years and longer, in hotter racks than anyone planned for.")}
    {box("Visibility", "Silicon as a black box", "When a card fails, nobody can say which logic caused it. There is no health signal to plan around and no evidence to attribute errors.")}
  </div>
  <div class="fig"><div class="fig-2">{ma}{mb}</div>
    <div class="legend-b"><span><i style="background:#6b675f"></i>Fleet of chips</span><span><i style="background:var(--blue)"></i>LUT links</span><span><i style="background:var(--orange)"></i>Carry links</span><span><i style="background:var(--gold)"></i>Per-chip sign-off</span></div>
    <p class="cap">Schematic, not to scale. Measured per chip, the margin each chip needs shrinks to measurement error plus drift until the next measurement. *Fluid Silicon measurements.</p></div>
  <div class="bsec">
    <h2>FPGA fleets are now infrastructure.</h2>
    <div class="cols cols-2" style="align-items:start;margin-top:10px">
      <div class="stat-b"><div class="v">&gt;1M</div><p style="margin-top:6px">Azure hosts with FPGA-based SmartNICs, deployed on all new Azure servers since late 2015.</p><p class="bsrc">{esc(nsdi_t)}. {nsdi_u}</p></div>
      <figure class="quote-b"><blockquote>“Currently, Azure has 5 generations of FPGA boards actively in deployment.”</blockquote><figcaption>{esc(f26_t)}. {f26_u}. The same paper describes supporting multiple board generations for a decade or longer. Cited for context; Fluid Silicon is not affiliated with Microsoft.</figcaption></figure>
    </div>
  </div>
</section>

<section class="page" id="p3">
  {top("02 · The platform")}
  <h2>A timing-health layer for FPGA fleets.</h2>
  <p class="sec-intro">Fluid Silicon gives each FPGA fine-grained timing introspection. Chips measure the health of their own logic at speed, tune voltage and frequency to what they can sustain, and route around resources that degrade. Monitoring and modeling are read-only. Tuning and repair are separate, opt-in steps.</p>
  <div class="cols cols-2" style="margin-top:12px">
    {box("Monitor", "Per-element timing, at operating speed", "Timing slack on individual logic elements, including LUTs, carry blocks and the links between them. A full sweep takes about one second, with each link resolved to under 20 ps.")}
    {box("Model", "An aging curve for every card", "Each element is tracked for the life of the card, its aging fitted to its own temperature history, with a predicted time-to-threshold. Outliers are flagged early.")}
    {box("Tune", "Voltage and frequency, per chip", "Adaptive frequency scaling finds the Fmax a chip can sustain for long periods. Adaptive voltage scaling trims voltage for better compute per watt. Both can be coordinated per device, per server or across the fleet.")}
    {box("Repair", "Swap out what is degrading", "Defective or degrading resources are replaced with healthier, faster ones, inside the maintenance windows you schedule.")}
  </div>
  <div class="fig fig--loop">{loop}<p class="cap">The health loop runs for the life of each card: characterization before deployment, a monitoring, modelling and tuning loop in production, and characterization after service. Every measurement tightens the next margin.</p></div>
</section>

<section class="page" id="p4">
  {top("03 · Lifecycle and adoption")}
  <h2>Across the whole life of a card.</h2>
  <div class="cols cols-3" style="margin-top:10px">
    {box("Before deployment", "Characterize and map", "Measure every LUT and carry block at speed to expose weak resources, then keep critical paths away from them.")}
    {box("In production", "Monitor, model, compensate", "Watch timing online while the design runs, model how each chip changes with time and temperature, and adapt as it does.")}
    {box("After deployment", "Decide what happens next", "Characterize cards leaving service so you can resell, reuse or retire them, with data to support the decision.")}
  </div>
  <div class="bsec">
    <h2>One health metric, on every vendor.</h2>
    <p class="sec-intro">Measured slack as a share of the clock period, per logic-element link. The same number means the same thing on an AMD part and an Altera part, so fleet dashboards, alert thresholds and aging models work across both.</p>
    <table class="bt"><thead><tr><th>Measure</th><th>Value</th></tr></thead><tbody>
      <tr><th>Margin a chip carries today for the worst-case corner</th><td>30–54%*</td></tr>
      <tr><th>Margin needed with per-chip measurement</th><td>Measurement error plus drift</td></tr>
      <tr><th>Per-link precision (error plus drift)</th><td>&lt; 20 ps</td></tr>
      <tr><th>Time to measure every logic element</th><td>≈ 1 s</td></tr>
      <tr><th>LUT and flip-flop overhead on a production shell</th><td>&lt; 1% LUTs · &lt; 5% FFs</td></tr>
      <tr><th>Delay impact on your design</th><td>&lt; 2%</td></tr>
      <tr><th>Downtime to monitor</th><td>None</td></tr>
    </tbody></table>
    <p class="fn">*Fluid Silicon measurements; they vary with variation pattern, workload, vendor and device age.</p>
  </div>
  <div class="bsec">
    <h2>Adopt it one step at a time.</h2>
    <p class="sec-intro">Every step is opt-in, and you can stay at any step as long as you want.</p>
    <ol class="steps-b">
      <li><h3>Evaluate</h3><p>A sample of cards in a staging environment, with a per-card timing and variation report.</p><p class="bm">Read-only</p></li>
      <li><h3>Observe</h3><p>Monitoring and aging models in production. Operating points do not change.</p><p class="bm">Read-only</p></li>
      <li><h3>Optimize</h3><p>Voltage and frequency tuning per policy, in the windows you schedule.</p><p class="bm">Opt-in · scheduled · handshake-gated</p></li>
      <li><h3>Repair</h3><p>Degrading resources swapped for healthy ones, through your change process.</p><p class="bm">Opt-in · scheduled · handshake-gated</p></li>
    </ol>
  </div>
</section>

<section class="page" id="p5">
  {top("04 · Security and integration")}
  <h2>Built to run beside production designs.</h2>
  <p class="sec-intro">Telemetry flows out from each card to your fleet. Actions flow back only after you approve them, and only through a handshake.</p>
  <div class="fig">{flow}<div class="legend-b"><span><i style="background:var(--green)"></i>Telemetry</span><span><i style="background:var(--blue)"></i>Approved actions</span></div></div>
  <div class="cols cols-3" style="margin-top:12px">
    {box("Integrity", "Your design stays intact", "Logic, routing and I/O are left as you built them. The health layer occupies a small, fixed region beside them.")}
    {box("Access", "No JTAG exposure", "No debug port has to be opened on production systems for monitoring to work.")}
    {box("Availability", "Zero downtime", "Your design keeps computing for the whole measurement. A full sweep takes about a second.")}
    {box("Footprint", "Small and design-agnostic", "Under 1% of LUTs and 5% of flip-flops on a production shell, with under 2% added delay.")}
    {box("Control", "Deterministic, scheduled changes", "Voltage, frequency and repair actions are opt-in, scheduled and handshake-gated.")}
    {box("Data", "One vendor-neutral view", "The same health metric, telemetry schema, alert thresholds and aging model on AMD and Altera parts.")}
  </div>
</section>

<section class="page" id="p6">
  {top("05 · Devices and next steps")}
  <h2>Supported devices.</h2>
  <p class="sec-intro">One platform across AMD and Altera families, with the vendor-specific integration handled by Fluid Silicon.</p>
  <table class="bt"><thead><tr><th>Vendor</th><th>Family</th><th>Process node</th><th>Status</th><th>Notes</th></tr></thead><tbody>{rows}</tbody></table>
  <p class="fn">Status as of September 2026. RF-sampling adaptive SoCs for far-edge systems are on the roadmap.</p>
  <div class="bsec">
    <h2>Where it is used.</h2>
    <div class="cols cols-2" style="margin-top:10px">
      {box("Data center and hyperscale", "Multi-vendor fleets, years in service", "Catch a failing chip before it costs capacity or sends errors downstream, trim voltage to cut power and raise frequency where a chip can hold it.")}
      {box("Aerospace and defense", "Far-edge systems on tight power budgets", "Self-monitoring and repair from defects and degradation, aging prediction for mission planning, and adaptive voltage scaling where every watt counts. It complements radiation mitigation rather than replacing it.")}
    </div>
  </div>
  <div class="note-b">Sensor architecture, deployment mechanics and calibration methods are shared with evaluation partners under NDA.</div>
  <div class="contact">
    <div><p class="kick">Next step</p><p class="bbig">See per-element timing live on a supported device, then talk through an evaluation on your own cards.</p></div>
    <dl><dt>Demo</dt><dd>fluidsilicon.com/demo</dd><dt>Email</dt><dd>{F["contact"]}</dd><dt>Based in</dt><dd>Philadelphia, PA</dd></dl>
  </div>
  <p class="fn" style="margin-top:14px">AMD, Altera and their product names are trademarks of their respective owners. Fluid Silicon is not affiliated with or endorsed by them. © 2026 Fluid Silicon.</p>
</section>
</body></html>"""


FOOTER = ('<div style="width:100%;font:500 7.5px Helvetica,Arial,sans-serif;color:#77736b;padding:0 0.62in;display:flex;justify-content:space-between;letter-spacing:.06em">'
          '<span>FLUID SILICON · TECHNICAL BRIEF · SEPTEMBER 2026</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')


def main(only=None):
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page()
        if only == "og":
            p = os.path.join(TMP, "og.html"); write_text(p, og_html())
            pg.set_viewport_size({"width": 1200, "height": 630})
            pg.goto("file://" + p); pg.wait_for_timeout(500)
            Image.open(io.BytesIO(pg.screenshot())).convert("RGB").save(os.path.join(IMG, "og-image.png"), optimize=True)
            br.close(); print("og-image.png written"); return
        # icons
        shots = {}
        for size in (16, 32, 48, 180, 192, 512):
            pg.set_viewport_size({"width": size, "height": size})
            opaque = size == 180          # iOS paints transparent corners black; fill them with the package edge color
            pg.set_content(svg_page(MARK, size, "#C64E00" if opaque else "transparent"))
            shots[size] = pg.screenshot(omit_background=not opaque)
        pg.set_viewport_size({"width": 512, "height": 512})
        pg.set_content(svg_page(maskable_svg(), 512))
        Image.open(io.BytesIO(pg.screenshot())).save(os.path.join(IMG, "icon-maskable-512.png"), optimize=True)
        for size, name in [(180, "apple-touch-icon.png"), (192, "icon-192.png"), (512, "icon-512.png")]:
            Image.open(io.BytesIO(shots[size])).save(os.path.join(IMG, name), optimize=True)
        ico = [Image.open(io.BytesIO(shots[s])).convert("RGBA") for s in (16, 32, 48)]
        ico[2].save(os.path.join(SRC, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)], append_images=ico[:2])
        # open graph image
        p = os.path.join(TMP, "og.html"); write_text(p, og_html())
        pg.set_viewport_size({"width": 1200, "height": 630})
        pg.goto("file://" + p); pg.wait_for_timeout(500)
        Image.open(io.BytesIO(pg.screenshot())).convert("RGB").save(os.path.join(IMG, "og-image.png"), optimize=True)
        # technical brief
        p = os.path.join(TMP, "brief.html"); write_text(p, brief_html())
        pg.goto("file://" + p); pg.wait_for_timeout(500)
        pg.pdf(path=os.path.join(DOCS, "fluid-silicon-technical-brief.pdf"), format="Letter", print_background=True,
               display_header_footer=True, header_template="<span></span>", footer_template=FOOTER,
               margin={"top": "0.62in", "bottom": "0.8in", "left": "0.62in", "right": "0.62in"}, prefer_css_page_size=False)
        br.close()
    # text files
    manifest = {"name": "Fluid Silicon", "short_name": "Fluid Silicon", "description": "Timing health for FPGA fleets.",
                "start_url": "/", "scope": "/", "display": "browser", "background_color": "#ffffff", "theme_color": "#ffffff",
                "icons": [{"src": "/assets/img/icon-192.png", "sizes": "192x192", "type": "image/png"},
                          {"src": "/assets/img/icon-512.png", "sizes": "512x512", "type": "image/png"},
                          {"src": "/assets/img/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}
    write_text(os.path.join(SRC, "site.webmanifest"), json.dumps(manifest, indent=2) + "\n")
    write_text(os.path.join(SRC, "robots.txt"), f"User-agent: *\nAllow: /\n\nSitemap: {B.SITE_URL}/sitemap.xml\n")
    write_text(os.path.join(SRC, "CNAME"), "fluidsilicon.com\n")
    write_text(os.path.join(SRC, ".nojekyll"), "")
    print("assets written")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
