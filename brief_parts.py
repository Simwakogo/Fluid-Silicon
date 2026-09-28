"""Build-time SVG for Fluid Silicon diagrams and charts.

Every figure is complete without JavaScript. site.js adds motion (tokens, packets,
the hero sweep) and interaction (toggles, the fleet inspector) on top.
Colors come from site.css classes, so the SVG and the page share one palette.
"""
import math, random, json, html

esc = html.escape


def _lines(x, y, lines, cls="t-body", dy=17, anchor=None):
    a = f' text-anchor="{anchor}"' if anchor else ""
    return "".join(f'<text x="{x}" y="{y + i*dy}" class="{cls}"{a}>{esc(t)}</text>' for i, t in enumerate(lines))


# ---------------------------------------------------------------- health loop (a card's lifecycle)
# Layout follows the company's technology slide: characterization before deployment, a production frame in which
# monitoring feeds modelling and compensation and both feed back into monitoring, and characterization after service.
LOOP_STAGES = [
    ("Characterize and map", "Before deployment", ["LUTs and carry blocks measured at speed.", "Weak resources mapped around."]),
    ("Monitor", "In production", ["Every logic element swept in", "about one second while your", "design keeps running."]),
    ("Model", "In production, feeds back into monitoring", ["An aging curve per card,", "per element. Predicts", "time-to-threshold."]),
    ("Tune and repair", "In production, feeds back into monitoring", ["Adaptive frequency scaling finds the Fmax a chip can sustain. Adaptive voltage scaling gives better compute per watt. Repair swaps degrading resources for healthier, faster ones."]),
    ("Characterize", "After deployment", ["Cards leaving service measured at speed, with the evidence", "to resell, reuse or retire them."]),
]
LOOP_TUNE_COLS = [
    (["Adaptive frequency", "scaling"], ["Finds the Fmax the chip", "can sustain."]),
    (["Adaptive voltage", "scaling"], ["Better compute", "per watt."]),
    (["Repair"], ["Degrading resources", "swapped for healthier,", "faster ones."]),
]


def health_loop(uid):
    p = []
    p.append(f'<svg class="dg" id="{uid}" data-anim="loop" viewBox="0 0 1100 684" role="img" aria-labelledby="{uid}-t {uid}-d">')
    p.append(f'<title id="{uid}-t">The Fluid Silicon health loop, over the life of a card</title>')
    p.append(f'<desc id="{uid}-d">Before deployment: characterize and map. LUTs and carry blocks are measured at speed and weak resources mapped around. '
             f'In production, three connected stages: monitoring sweeps every logic element in about one second while the design keeps running; '
             f'it feeds a model, an aging curve per card and per element that predicts time-to-threshold, and it feeds tuning and repair: adaptive frequency scaling, adaptive voltage scaling and repair. '
             f'Both the model and the tuning feed back into monitoring, so every change is measured again. After deployment: cards leaving service are characterized at speed, with the evidence to resell, reuse or retire them.</desc>')
    p.append(f'<defs><marker id="{uid}-ab" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0 .5 L8 4.5 L0 8.5 Z" style="fill:var(--orange-deep)"/></marker>'
             f'<marker id="{uid}-al" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0 .5 L8 4.5 L0 8.5 Z" style="fill:var(--olive)"/></marker></defs>')
    p.append('<text x="32" y="34" class="t-eyebrow">FLUID SILICON / THE HEALTH LOOP</text>')
    # band labels
    p.append('<text x="40" y="104" class="t-tag">BEFORE DEPLOYMENT</text>')
    p.append('<text x="40" y="259" class="t-tag">IN PRODUCTION</text>')
    p.append('<text x="40" y="594" class="t-tag">AFTER DEPLOYMENT</text>')
    # production frame
    p.append('<rect class="frame-prod" x="230" y="184" width="846" height="332" rx="12"/>')
    # arrows between bands (drawn), and the split and returns inside the frame
    p.append(f'<path class="arrow-band" d="M550 140 V204" marker-end="url(#{uid}-ab)"/>')
    p.append(f'<path class="arrow-band" d="M550 516 V546" marker-end="url(#{uid}-ab)"/>')
    p.append('<path class="arrow-loop" d="M550 302 V470"/>')
    p.append(f'<path class="arrow-loop" d="M550 470 H478" marker-end="url(#{uid}-al)"/>')
    p.append(f'<path class="arrow-loop" d="M550 470 H622" marker-end="url(#{uid}-al)"/>')
    p.append(f'<path class="arrow-loop" d="M262 340 V255 H416" marker-end="url(#{uid}-al)"/>')
    p.append(f'<path class="arrow-loop" d="M1046 340 V255 H684" marker-end="url(#{uid}-al)"/>')
    # token routes (invisible; site.js moves the tokens along them)
    for k, d in [("in", "M550 100 V255"), ("down", "M550 255 V470"), ("left", "M550 470 H262"), ("right", "M550 470 H1046"),
                 ("retl", "M262 470 V255 H550"), ("retr", "M1046 470 V255 H550"), ("out", "M550 255 V590")]:
        p.append(f'<path id="{uid}-p-{k}" d="{d}" fill="none" stroke="none"/>')
    # stages
    def stage(i, x, y, w, h, title, lines, tx=None):
        tx = x + 20 if tx is None else tx
        g = [f'<g class="stage" data-i="{i}">', f'<rect class="box" x="{x}" y="{y}" width="{w}" height="{h}" rx="10"/>',
             f'<text x="{tx}" y="{y+28}" class="t-lbl">{esc(title)}</text>']
        if lines:
            g.append(_lines(tx, y + 52, lines))
        return "".join(g)
    p.append(stage(0, 330, 60, 440, 80, LOOP_STAGES[0][0], LOOP_STAGES[0][2]) + '</g>')
    p.append(stage(1, 420, 208, 260, 94, LOOP_STAGES[1][0], LOOP_STAGES[1][2]) + '</g>')
    p.append(stage(2, 250, 340, 220, 148, LOOP_STAGES[2][0], LOOP_STAGES[2][2]) + '</g>')
    t = [f'<g class="stage" data-i="3">', '<rect class="box" x="620" y="340" width="436" height="148" rx="10"/>',
         f'<text x="640" y="368" class="t-lbl">{esc(LOOP_STAGES[3][0])}</text>']
    for j, (head, body) in enumerate(LOOP_TUNE_COLS):
        x = 636 + j * 138
        t.append(_lines(x, 394, head, cls="t-strong", dy=16))
        t.append(_lines(x, 394 + 16 * len(head) + 4, body, cls="t-small", dy=15))
    t.append('</g>')
    p.append("".join(t))
    p.append(stage(4, 280, 550, 540, 80, LOOP_STAGES[4][0], LOOP_STAGES[4][2]) + '</g>')
    p.append('<text x="32" y="666" class="t-tag">VENDOR-NEUTRAL · DESIGN-AGNOSTIC · ZERO DOWNTIME · OPT-IN ACTIONS</text>')
    p.append('<g class="loop-token tok-a" visibility="hidden"><circle class="halo" r="12"/><circle class="token" r="7"/></g>')
    p.append('<g class="loop-token tok-b" visibility="hidden"><circle class="halo" r="12"/><circle class="token" r="7"/></g>')
    p.append('</svg>')
    return "".join(p)


def health_loop_list():
    items = []
    for i, (lbl, when, body) in enumerate(LOOP_STAGES):
        items.append(f'<li><h3>{esc(lbl)}</h3><p>{esc(" ".join(body))}</p><p class="meta">{esc(when)}</p></li>')
    return '<ol class="steps">' + "".join(items) + '</ol><p class="footnote">Monitoring, modelling and tuning form a loop in production. Every measurement tightens the next margin.</p>'


# ---------------------------------------------------------------- integration flow
def _lock(x, y, cls="lock"):
    return (f'<g class="{cls}" transform="translate({x} {y})"><rect x="-7" y="-2" width="14" height="11" rx="2"/>'
            f'<path d="M-4 -2 V-5 A4 4 0 0 1 4 -5 V-2"/></g>')


def integration_flow(uid):
    p = [f'<svg class="dg" id="{uid}" data-anim="flow" viewBox="0 0 1100 580" role="img" aria-labelledby="{uid}-t {uid}-d">',
         f'<title id="{uid}-t">How the health layer fits a production system</title>',
         f'<desc id="{uid}-d">Three zones. On the FPGA card, your design keeps its logic, routing and I/O as built, and a small health layer measures per-element timing at operating speed, '
         f'using under 1% of LUTs and under 5% of flip-flops and adding under 2% delay. '
         f'On the host server, Fluid Silicon software collects per-element telemetry from each card and applies only approved actions, in the windows you set. It is read-only by default and needs no JTAG exposure. '
         f'In your fleet, a health service keeps one vendor-neutral metric, aging models and alerts, and feeds your monitoring. Your orchestration sets maintenance windows, approvals and policy. '
         f'Telemetry flows from the card to your fleet. Approved actions flow back to the card only through a handshake.</desc>',
         f'<defs><marker id="{uid}-g" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0 .5 L8 4.5 L0 8.5 Z" style="fill:var(--green)"/></marker>'
         f'<marker id="{uid}-b" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0 .5 L8 4.5 L0 8.5 Z" style="fill:var(--blue)"/></marker></defs>']
    # zones: card | host | fleet
    for x, name in [(24, "FPGA CARD"), (390, "HOST SERVER"), (756, "YOUR FLEET")]:
        p.append(f'<rect class="zone" x="{x}" y="40" width="320" height="520" rx="12"/>')
        p.append(f'<text x="{x+18}" y="68" class="t-eyebrow">{name}</text>')
    # card: your design + health layer
    p.append('<rect class="box" x="44" y="92" width="280" height="236" rx="10"/>')
    p.append('<text x="64" y="124" class="t-lbl">Your design</text>')
    p.append(_lines(64, 150, ["Logic, routing and I/O stay", "exactly as you built them.", "Your computation runs", "without interruption."]))
    p.append(_lock(298, 118))
    p.append('<text x="64" y="306" class="t-mono t-green">DESIGN INTEGRITY</text>')
    p.append('<rect class="box-olive" x="44" y="352" width="280" height="184" rx="10"/>')
    p.append('<text x="64" y="384" class="t-lbl">Fluid Silicon health layer</text>')
    p.append(_lines(64, 410, ["Measures per-element timing", "at operating speed."]))
    p.append('<text x="64" y="486" class="t-mono">&lt; 1% LUTs · &lt; 5% FFs</text>')
    p.append('<text x="64" y="508" class="t-mono">&lt; 2% delay · 0 downtime</text>')
    # host: one tall box with its guardrails
    p.append('<rect class="box" x="410" y="92" width="280" height="444" rx="10"/>')
    p.append('<text x="430" y="124" class="t-lbl">Fluid Silicon software</text>')
    p.append(_lines(430, 150, ["Collects per-element telemetry", "from each card. Applies only", "approved actions, in the", "windows you set."]))
    p.append('<line x1="430" y1="232" x2="670" y2="232" style="stroke:var(--line-2);stroke-width:1"/>')
    p.append(_lock(438, 256)); p.append('<text x="456" y="264" class="t-mono t-green">READ-ONLY BY DEFAULT</text>')
    p.append(_lock(438, 288)); p.append('<text x="456" y="296" class="t-mono t-green">NO JTAG EXPOSURE</text>')
    p.append('<text x="430" y="372" class="t-small">Approved actions can be scoped per</text>')
    for i, w in enumerate(["device", "server", "fleet"]):
        x = 430 + i * 82
        p.append(f'<rect x="{x}" y="384" width="74" height="26" rx="13" class="scope-pill"/>')
        p.append(f'<text x="{x+37}" y="401" class="t-small t-ink" text-anchor="middle">{w}</text>')
    p.append(_lock(438, 478, "lock lock-blue")); p.append('<text x="456" y="486" class="t-mono t-blue">HANDSHAKE-GATED</text>')
    # fleet
    p.append('<rect class="box" x="776" y="92" width="280" height="140" rx="10"/>')
    p.append('<text x="796" y="124" class="t-lbl">Health service</text>')
    p.append(_lines(796, 150, ["One vendor-neutral metric and", "telemetry schema. Aging models,", "alert thresholds, fleet views."]))
    p.append('<rect class="box-dark" x="776" y="256" width="280" height="96" rx="10"/>')
    p.append('<text x="796" y="288" class="t-lbl">Your monitoring</text>')
    p.append(_lines(796, 312, ["Dashboards, tickets and", "capacity plans."]))
    p.append('<rect class="box-dark" x="776" y="376" width="280" height="160" rx="10"/>')
    p.append('<text x="796" y="408" class="t-lbl">Your orchestration</text>')
    p.append(_lines(796, 432, ["Maintenance windows, approvals", "and policy. Nothing changes", "until you say so."]))
    # flows: every segment is horizontal or vertical, labels sit in the gutters
    for c, d in [("g", "M324 404 H410"), ("g", "M690 162 H776"), ("g", "M916 232 V256"),
                 ("b", "M776 470 H690"), ("b", "M410 482 H324")]:
        kind = "green" if c == "g" else "blue"
        p.append(f'<path class="flow-{kind}" data-flow="{kind}" d="{d}" marker-end="url(#{uid}-{c})"/>')
    p.append(_lines(367, 380, ["per-element", "slack"], cls="t-small t-green", dy=14, anchor="middle"))
    p.append('<text x="733" y="152" class="t-small t-green" text-anchor="middle">telemetry</text>')
    p.append(_lines(733, 446, ["approved", "actions"], cls="t-small t-blue", dy=14, anchor="middle"))
    p.append(_lines(367, 504, ["approved", "actions"], cls="t-small t-blue", dy=14, anchor="middle"))
    p.append('</svg>')
    return "".join(p)


def integration_list():
    """Phone version of the integration diagram: the three zones stacked, with the two flows between them."""
    link = ('<li class="fz-link" aria-hidden="true"><span class="dn">↓ telemetry</span><span class="up">↑ approved actions</span></li>')
    guard = lambda t, c="": f'<li class="guard{c}">{t}</li>'
    return ('<div class="flow-mobile"><ol class="fz-list">'
            '<li class="fz"><p class="fz-eyebrow">FPGA card</p>'
            '<div class="blk"><h3>Your design</h3><p>Logic, routing and I/O stay exactly as you built them. Your computation runs without interruption.</p></div>'
            '<div class="blk blk--olive"><h3>Fluid Silicon health layer</h3><p>Measures per-element timing at operating speed.</p>'
            '<p class="mono-sm">&lt; 1% LUTs · &lt; 5% FFs · &lt; 2% delay · 0 downtime</p></div></li>'
            + link +
            '<li class="fz"><p class="fz-eyebrow">Host server</p>'
            '<div class="blk"><h3>Fluid Silicon software</h3><p>Collects per-element telemetry from each card. Applies only approved actions, in the windows you set, per device, per server or across the fleet.</p>'
            '<ul class="guards">' + guard("Read-only by default") + guard("No JTAG exposure") + guard("Handshake-gated", " guard--blue") + '</ul></div></li>'
            + link +
            '<li class="fz"><p class="fz-eyebrow">Your fleet</p>'
            '<div class="blk"><h3>Health service</h3><p>One vendor-neutral metric and telemetry schema. Aging models, alert thresholds, fleet views.</p></div>'
            '<div class="blk blk--dark"><h3>Your monitoring</h3><p>Dashboards, tickets and capacity plans.</p></div>'
            '<div class="blk blk--dark"><h3>Your orchestration</h3><p>Maintenance windows, approvals and policy. Nothing changes until you say so.</p></div></li>'
            '</ol></div>')


# ---------------------------------------------------------------- fleet mesh
MESH_COLS = [
    ("AMD", "Virtex UltraScale+", "16 nm", "ok"),
    ("Altera", "Agilex 7 F-Series", "10 nm class", "select"),
    ("AMD", "Versal AI Core", "7 nm", "dev"),
]
MESH_DATA = [
    # per card: slack %, weakest %, time-to-threshold, action, state
    (38.4, 17.9, "9.1 yrs", "Keep in service. Voltage trim available.", "ok"),
    (35.2, 16.4, "8.4 yrs", "Keep in service.", "ok"),
    (None, None, None, "Monitoring in development for this family.", "dev"),
    (41.0, 19.3, "10+ yrs", "Keep in service. Frequency headroom 6%.", "ok"),
    (33.7, 8.2, "1.4 yrs", "Degrading LUT cluster. Schedule a repair window.", "warn"),
    (None, None, None, "Monitoring in development for this family.", "dev"),
    (36.9, 18.8, "8.9 yrs", "Keep in service.", "ok"),
    (34.1, 15.1, "7.7 yrs", "Keep in service.", "ok"),
    (None, None, None, "Monitoring in development for this family.", "dev"),
]


def fleet_mesh(uid):
    cx = [250, 500, 750]; cy = [150, 320, 490]
    rx = [125, 375, 625, 875]; ry = [65, 235, 405, 575]
    p = [f'<svg class="dg" id="{uid}" data-anim="flow" data-mesh="1" viewBox="0 0 1000 640" role="group" aria-labelledby="{uid}-t">',
         f'<title id="{uid}-t">Illustrative multi-vendor FPGA fleet. Select a card to inspect its health.</title>',
         f'<defs><marker id="{uid}-g" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="userSpaceOnUse"><path d="M0 .5 L7 4 L0 7.5 Z" style="fill:var(--green)"/></marker>'
         f'<marker id="{uid}-b" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="userSpaceOnUse"><path d="M0 .5 L7 4 L0 7.5 Z" style="fill:var(--blue)"/></marker>'
         f'<marker id="{uid}-w" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="userSpaceOnUse"><path d="M0 .5 L7 4 L0 7.5 Z" style="fill:#9a968e"/></marker></defs>']
    # router mesh
    for y in ry:
        p.append(f'<path class="mesh" d="M{rx[0]} {y} H{rx[-1]}"/>')
    for x in rx:
        p.append(f'<path class="mesh" d="M{x} {ry[0]} V{ry[-1]}"/>')
    for x in rx:
        for y in ry:
            p.append(f'<rect class="router" x="{x-9}" y="{y-9}" width="18" height="18" rx="2"/>')
    # chip to router diagonals
    for x in cx:
        for y in cy:
            for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                x1, y1 = x + dx*62, y + dy*62
                x2, y2 = x + dx*112, y + dy*72
                p.append(f'<path class="mesh" d="M{x1} {y1} L{x2 - dx*8} {y2 - dy*6}" marker-end="url(#{uid}-w)"/>')
    # telemetry and control between neighbours
    for y in cy:
        for a, b in zip(cx, cx[1:]):
            p.append(f'<path class="flow-green" data-flow="green" d="M{a+66} {y-14} H{b-66}" marker-end="url(#{uid}-g)"/>')
            p.append(f'<path class="flow-blue" data-flow="blue" d="M{b-66} {y+14} H{a+66}" marker-end="url(#{uid}-b)"/>')
    for x in cx:
        for a, b in zip(cy, cy[1:]):
            p.append(f'<path class="flow-green" data-flow="green" d="M{x} {a+66} V{b-66}" marker-end="url(#{uid}-g)"/>')
    k = 0
    for r, y in enumerate(cy):
        for c, x in enumerate(cx):
            vendor, fam, node, status = MESH_COLS[c]
            slack, weak, ttt, action, state = MESH_DATA[k]
            led = {"ok": "led-ok", "warn": "led-warn", "dev": "led-dev"}[state]
            st = {"ok": "Supported", "select": "Select devices", "dev": "In development"}[status]
            info = {"part": f"{vendor} {fam}", "node": node, "status": st, "slack": slack, "weak": weak, "ttt": ttt, "action": action, "state": state, "slot": f"Rack slot {chr(65+r)}{c+1}"}
            label = f'{vendor} {fam}, slot {chr(65+r)}{c+1}. ' + (f'Median slack {slack}%, time-to-threshold {ttt}. {action}' if slack else action)
            p.append(f'<g class="card-hit" tabindex="0" role="button" aria-label="{esc(label)}" data-card=\'{esc(json.dumps(info))}\'>')
            p.append(f'<rect class="chip" x="{x-60}" y="{y-60}" width="120" height="120" rx="6"/>')
            p.append(f'<rect class="chip-die" x="{x-46}" y="{y-46}" width="92" height="92" rx="3"/>')
            p.append(f'<text x="{x}" y="{y-20}" class="t-mono" text-anchor="middle">{esc(vendor.upper())}</text>')
            fam_lines = fam.split(" ", 1) if len(fam) > 12 else [fam]
            for j, fl in enumerate(fam_lines):
                p.append(f'<text x="{x}" y="{y+2+j*16}" class="t-strong" text-anchor="middle">{esc(fl)}</text>')
            p.append(f'<text x="{x}" y="{y+38}" class="t-small" text-anchor="middle">{esc(node)}</text>')
            p.append(f'<circle class="{led}" cx="{x+44}" cy="{y-44}" r="5"/>')
            p.append('</g>')
            k += 1
    p.append('</svg>')
    return "".join(p)


# ---------------------------------------------------------------- RF chain (aerospace)
def _icon(kind, x, y):
    """Line icons for platforms, 48x48 around (x, y)."""
    g = f'<g class="icon-stroke" transform="translate({x} {y})">'
    if kind == "satellite":
        g += ('<rect x="-7" y="-7" width="14" height="14" rx="2" transform="rotate(45)"/>'
              '<path d="M-10 -10 L-22 -22 M-26 -18 L-18 -26 L-6 -14 L-14 -6 Z"/>'
              '<path d="M10 10 L22 22 M26 18 L18 26 L6 14 L14 6 Z"/>'
              '<path d="M12 -4 A10 10 0 0 1 4 -12 M16 -8 A16 16 0 0 1 8 -16"/>')
    elif kind == "aircraft":
        g += ('<path d="M-24 0 H18 Q24 0 24 3 Q24 6 18 6 H-24 Z" transform="translate(0 -3)"/>'
              '<path d="M-2 -1 L-12 -18 H-6 L10 -1 M-2 3 L-12 20 H-6 L10 3 M-20 -1 L-24 -10 H-19 L-13 -1 M-20 3 L-24 12 H-19 L-13 3"/>')
    elif kind == "radar":
        g += ('<path d="M-18 -14 A22 22 0 0 0 10 14 Z"/><path d="M-4 0 L6 -10"/><circle cx="8" cy="-12" r="2.5"/>'
              '<path d="M-6 8 L-12 22 H6 L0 10"/><path d="M14 -18 A10 10 0 0 1 20 -8 M16 -26 A18 18 0 0 1 28 -10"/>')
    else:  # tower
        g += ('<path d="M0 -14 L-12 22 M0 -14 L12 22 M-8 10 H8 M-5 0 H5 M-10 16 L8 4 M10 16 L-8 4"/><circle cx="0" cy="-18" r="3"/>'
              '<path d="M-10 -22 A12 12 0 0 0 -10 -12 M10 -22 A12 12 0 0 1 10 -12 M-16 -28 A20 20 0 0 0 -16 -6 M16 -28 A20 20 0 0 1 16 -6"/>')
    return g + '</g>'


RF_CAPS = ["Self-monitoring and repair", "Aging prediction", "Adaptive voltage scaling"]


def rf_chain(uid):
    p = [f'<svg class="dg" id="{uid}" data-anim="flow" viewBox="0 0 1000 510" role="img" aria-labelledby="{uid}-t {uid}-d">',
         f'<title id="{uid}-t">Far-edge RF processing with a health layer</title>',
         f'<desc id="{uid}-d">Signals from 1 MHz to 18 GHz connect satellites, aircraft, radar and ground stations to far-edge processing. '
         f'Received signals run on a shared bus through an amplifier into analog-to-digital converters and an RF-sampling adaptive SoC. Transmit signals leave the SoC through digital-to-analog converters, an amplifier and a shared bus back to each platform. '
         f'A Fluid Silicon health layer around the SoC provides self-monitoring and repair, aging prediction and adaptive voltage scaling. RF-sampling adaptive SoCs, such as AMD Versal RF, are on the Fluid Silicon roadmap.</desc>',
         f'<defs><linearGradient id="{uid}-sp" x1="0" y1="0" x2="0" y2="1"><stop offset="0" style="stop-color:var(--gold-deep)"/><stop offset=".35" style="stop-color:var(--olive)"/><stop offset=".7" style="stop-color:#5a5a5a"/><stop offset="1" style="stop-color:#262626"/></linearGradient>'
         f'<marker id="{uid}-g" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0 .5 L8 4.5 L0 8.5 Z" style="fill:var(--green)"/></marker>'
         f'<marker id="{uid}-w" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0 .5 L8 4.5 L0 8.5 Z" style="fill:#d9d6cf"/></marker></defs>']
    # spectrum ladder
    p.append(f'<path d="M40 98 L62 76 L84 98 V458 H40 Z" style="fill:url(#{uid}-sp)"/>')
    for yy in [182, 272, 362]:
        p.append(f'<path d="M40 {yy+18} L62 {yy} L84 {yy+18}" style="fill:none;stroke:#050505;stroke-width:3"/>')
    p.append('<text x="62" y="60" class="t-mono" text-anchor="middle">18 GHz</text>')
    p.append('<text x="62" y="484" class="t-mono" text-anchor="middle">1 MHz</text>')
    # platforms
    kinds = [("satellite", "Satellites"), ("aircraft", "Aircraft"), ("radar", "Radar"), ("tower", "Ground stations")]
    ys = [88, 184, 280, 376]
    for (k, name), y in zip(kinds, ys):
        p.append(f'<rect class="tile" x="104" y="{y}" width="192" height="84" rx="6"/>')
        p.append(_icon(k, 142, y + 42))
        p.append(f'<text x="180" y="{y+47}" class="t-strong">{name}</text>')
    # shared buses: transmit (white) fans out at x=324, receive (green) gathers at x=412
    TXB, RXB, TXY, RXY = 324, 412, 232, 354
    for y in ys:
        p.append(f'<path class="flow-white" data-flow="white" d="M452 {TXY} H{TXB} V{y+26} H296" marker-end="url(#{uid}-w)"/>')
    # receive lines pass over the transmit bus: a knockout underneath opens a small gap at each crossing
    rx = [f"M296 {y+60} H{RXB} V{RXY} H452" for y in ys]
    for d in rx:
        p.append(f'<path class="knock" d="{d}"/>')
    for d in rx:
        p.append(f'<path class="flow-green" data-flow="green" d="{d}" marker-end="url(#{uid}-g)"/>')
    # amplifiers
    p.append(f'<path d="M488 {TXY-18} L452 {TXY} L488 {TXY+18} Z" style="fill:#e9e6df"/>')
    p.append(f'<path d="M452 {RXY-18} L488 {RXY} L452 {RXY+18} Z" style="fill:var(--green)"/>')
    p.append(f'<path class="flow-white" data-flow="white" d="M560 {TXY} H488"/>')
    p.append(f'<path class="flow-green" data-flow="green" d="M488 {RXY} H560" marker-end="url(#{uid}-g)"/>')
    # far-edge processing frame
    p.append('<rect class="frame-blue" x="512" y="64" width="468" height="420" rx="10"/>')
    p.append('<text x="532" y="92" class="t-tag t-blue">FAR-EDGE PROCESSING</text>')
    # converters: DAC on the transmit side, ADC on the receive side
    p.append('<rect x="560" y="128" width="112" height="320" rx="16" style="fill:var(--olive);stroke:none"/>')
    p.append('<line x1="576" y1="292" x2="656" y2="292" style="stroke:#0a0a0a;stroke-width:1.5;opacity:.5"/>')
    p.append(_lines(616, 204, ["Digital to", "analog", "converters"], cls="t-small t-conv", dy=16, anchor="middle"))
    p.append(_lines(616, 334, ["Analog to", "digital", "converters"], cls="t-small t-conv", dy=16, anchor="middle"))
    p.append(f'<path class="flow-white" data-flow="white" d="M700 {TXY} H672" marker-end="url(#{uid}-w)"/>')
    p.append(f'<path class="flow-green" data-flow="green" d="M672 {RXY} H700" marker-end="url(#{uid}-g)"/>')
    # SoC with the health layer around it
    p.append('<rect class="health-ring" x="700" y="128" width="264" height="264" rx="10"/>')
    p.append('<rect class="chip" x="716" y="144" width="232" height="232" rx="8"/>')
    p.append('<rect class="chip-die" x="738" y="166" width="188" height="188" rx="4"/>')
    p.append(_lines(832, 244, ["RF-sampling", "adaptive SoC"], cls="t-lbl", dy=22, anchor="middle"))
    p.append('<text x="832" y="300" class="t-small" text-anchor="middle">On the roadmap,</text>')
    p.append('<text x="832" y="318" class="t-small" text-anchor="middle">such as AMD Versal RF</text>')
    p.append('<text x="832" y="420" class="t-mono t-gold" text-anchor="middle">FLUID SILICON HEALTH LAYER</text>')
    p.append('</svg>')
    return "".join(p)


# ---------------------------------------------------------------- margin charts
def _bell(x0, mu, sigma, h, y0, skew=0.0, x_from=None, x_to=None, step=3):
    pts = []
    a, b = (x_from or mu - 4*sigma), (x_to or mu + 5*sigma)
    x = a
    while x <= b:
        z = (x - mu) / sigma
        dens = math.exp(-0.5*z*z) * (1 + math.erf(skew*z/math.sqrt(2)))
        pts.append((x, y0 - h*dens))
        x += step
    return pts


def _area(pts, y0):
    d = f"M{pts[0][0]:.1f} {y0} " + " ".join(f"L{x:.1f} {y:.1f}" for x, y in pts) + f" L{pts[-1][0]:.1f} {y0} Z"
    return d


def margin_charts(uid):
    y0 = 262
    # panel A: fleet
    fleet = _bell(0, 170, 44, 96, y0, skew=2.2, x_from=66, x_to=430)
    peak_x = max(fleet, key=lambda p: -p[1])[0]
    a = [f'<svg class="dg" id="{uid}-a" viewBox="0 0 520 320" role="img" aria-labelledby="{uid}-a-t {uid}-a-d">',
         f'<title id="{uid}-a-t">Today: one margin for the whole fleet</title>',
         f'<desc id="{uid}-a-d">Schematic. A wide distribution of chip path delays across a fleet. The worst-case corner sits far to the right of the typical chip, so every chip carries 30 to 54 percent timing margin.</desc>',
         f'<defs><marker id="{uid}-m" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto-start-reverse" markerUnits="userSpaceOnUse"><path d="M0 .5 L7 4 L0 7.5 Z" style="fill:var(--gold)"/></marker></defs>',
         '<text x="20" y="28" class="t-lbl">Today: one margin for the fleet</text>',
         f'<line class="axis" x1="40" y1="{y0}" x2="500" y2="{y0}"/>',
         f'<path class="curve-fleet" d="{_area(fleet, y0)}"/>',
         f'<line class="corner" x1="462" y1="64" x2="462" y2="{y0}"/>',
         '<text x="456" y="82" class="t-small t-orange" text-anchor="end">Worst-case corner</text>',
         f'<line x1="{peak_x:.0f}" y1="118" x2="456" y2="118" style="stroke:var(--gold);stroke-width:1.6" marker-start="url(#{uid}-m)" marker-end="url(#{uid}-m)"/>',
         f'<text x="{(peak_x+456)/2:.0f}" y="108" class="t-strong t-gold" text-anchor="middle">30–54% timing margin*</text>',
         f'<text x="{peak_x:.0f}" y="{y0+20}" class="t-small" text-anchor="middle">typical chip</text>',
         f'<text x="500" y="{y0+44}" class="t-small" text-anchor="end">Path delay →</text>',
         '<text x="40" y="306" class="t-small">Fleet distribution of chips</text>',
         '</svg>']
    # panel B: per chip
    chips = [(150, "Chip A"), (250, "Chip B"), (338, "Chip C")]
    b = [f'<svg class="dg" id="{uid}-b" viewBox="0 0 520 320" role="img" aria-labelledby="{uid}-b-t {uid}-b-d">',
         f'<title id="{uid}-b-t">Measured: a margin per chip</title>',
         f'<desc id="{uid}-b-d">Schematic. Each chip is measured separately. LUT links and carry links form narrow distributions per chip, and each chip needs only its own measurement error plus drift, under 20 picoseconds per link, instead of the fleet-wide corner.</desc>',
         '<text x="20" y="28" class="t-lbl">Measured: a margin per chip</text>',
         f'<line class="axis" x1="40" y1="{y0}" x2="500" y2="{y0}"/>',
         f'<line class="corner" x1="462" y1="64" x2="462" y2="{y0}" style="opacity:.35"/>',
         '<text x="456" y="82" class="t-small" text-anchor="end" style="opacity:.7">Fleet corner, no longer needed</text>']
    for i, (mu, name) in enumerate(chips):
        lut = _bell(0, mu, 13, 112 - i*8, y0, x_from=mu-44, x_to=mu+48, step=2)
        car = _bell(0, mu+9, 12, 84 - i*6, y0, x_from=mu-36, x_to=mu+52, step=2)
        so = mu + 58
        # the only margin each chip needs: from its own slowest measured links to its sign-off
        b.append(f'<rect class="margin-band" x="{mu+40}" y="{y0-128}" width="{so-(mu+40)}" height="128"/>')
        b.append(f'<path class="curve-lut" d="{_area(lut, y0)}"/>')
        b.append(f'<path class="curve-carry" d="{_area(car, y0)}"/>')
        b.append(f'<line class="signoff" x1="{so}" y1="{y0-128}" x2="{so}" y2="{y0}"/>')
        b.append(f'<text x="{mu+4}" y="{y0+20}" class="t-mono" text-anchor="middle">{name}</text>')
    b.append(f'<path d="M{150+49} {y0-128} V{y0-146} H{150+62}" style="stroke:var(--gold);stroke-width:1.2;fill:none"/>')
    b.append(f'<text x="{150+66}" y="{y0-142}" class="t-small t-gold">Per-chip margin: error + drift, &lt; 20 ps</text>')
    b.append(f'<text x="500" y="{y0+44}" class="t-small" text-anchor="end">Path delay →</text>')
    b.append('<text x="40" y="306" class="t-small">Per-chip distributions</text>')
    b.append('</svg>')
    return "".join(a), "".join(b)


# ---------------------------------------------------------------- aging chart
AGING_TEMPS = {"45": 3.5, "55": 4.0, "70": 4.6}
AGING_N, AGING_THR = 0.2, 6.0


def aging_series(temp):
    A = AGING_TEMPS[temp]
    rng = random.Random(int(temp) * 7919)
    pts = []
    t = 0.25
    while t <= 3.001:
        base = A * t**AGING_N
        pts.append((round(t, 2), round(base + rng.uniform(-0.18, 0.18), 3), round(0.22 + 0.05*t, 3)))
        t += 0.25
    tstar = (AGING_THR / A) ** (1/AGING_N)
    return A, pts, tstar


AGING_GEOM = {"x0": 70, "x1": 840, "y0": 316, "y1": 44}


def aging_label_pos(tx, vis, G=AGING_GEOM):
    """Label sits at the foot of the crossing marker, on whichever side has room."""
    if not vis:
        return G["x1"] - 10, "end"
    return (tx + 10, "start") if tx < G["x1"] - 270 else (tx - 10, "end")


def aging_chart(uid, temp="55"):
    G = AGING_GEOM
    X0, X1, Y0, Y1 = G["x0"], G["x1"], G["y0"], G["y1"]
    sx = lambda t: X0 + (X1-X0) * t/10
    sy = lambda v: Y0 - (Y0-Y1) * v/8
    A, pts, tstar = aging_series(temp)
    fit = " ".join(f"{'M' if i==0 else 'L'}{sx(t):.1f} {sy(A*t**AGING_N):.1f}" for i, t in enumerate([0.05 + k*0.05 for k in range(60)]))
    proj = " ".join(f"{'M' if i==0 else 'L'}{sx(t):.1f} {sy(A*t**AGING_N):.1f}" for i, t in enumerate([3 + k*0.1 for k in range(71)]))
    band_top = " ".join(f"L{sx(t):.1f} {sy(v+w):.1f}" for t, v, w in pts)
    band_bot = " ".join(f"L{sx(t):.1f} {sy(v-w):.1f}" for t, v, w in reversed(pts))
    band = "M" + band_top[1:] + " " + band_bot + " Z"
    geom = ",".join(str(G[k]) for k in ["x0", "x1", "y0", "y1"])
    p = [f'<svg class="dg" id="{uid}" data-chart="aging" data-temp="{temp}" data-geom="{geom}" viewBox="0 0 880 380" role="img" aria-labelledby="{uid}-t {uid}-d">',
         f'<title id="{uid}-t">Illustrative aging model for one card</title>',
         f'<desc id="{uid}-d">Path delay increase over years in service. Measured points for the first three years lie on a fitted aging curve, projected forward. '
         f'The chart can be switched between 45, 55 and 70 degrees Celsius. At 55 degrees the projection crosses the 6 percent alert threshold at about 7.6 years; '
         f'at 45 degrees, about 14.7 years; at 70 degrees, about 3.8 years.</desc>']
    for v in [0, 2, 4, 6, 8]:
        p.append(f'<line class="grid-line" x1="{X0}" y1="{sy(v):.1f}" x2="{X1}" y2="{sy(v):.1f}"/>')
        p.append(f'<text x="{X0-10}" y="{sy(v)+4:.1f}" class="t-small" text-anchor="end">{v}%</text>')
    for t in [0, 2, 4, 6, 8, 10]:
        p.append(f'<text x="{sx(t):.1f}" y="{Y0+22}" class="t-small" text-anchor="middle">{t}</text>')
    p.append(f'<line class="axis" x1="{X0}" y1="{Y0}" x2="{X1}" y2="{Y0}"/>')
    p.append(f'<text x="{(X0+X1)/2:.0f}" y="{Y0+48}" class="t-small" text-anchor="middle">Years in service</text>')
    p.append(f'<text x="18" y="{(Y0+Y1)/2:.0f}" class="t-small" text-anchor="middle" transform="rotate(-90 18 {(Y0+Y1)/2:.0f})">Path delay increase</text>')
    p.append(f'<line class="threshold" x1="{X0}" y1="{sy(AGING_THR):.1f}" x2="{X1}" y2="{sy(AGING_THR):.1f}"/>')
    p.append(f'<text x="{X0+8}" y="{sy(AGING_THR)-9:.1f}" class="t-small t-orange">Alert threshold: margin used up</text>')
    p.append(f'<line class="marker-line" x1="{sx(3):.1f}" y1="{Y1}" x2="{sx(3):.1f}" y2="{Y0}"/>')
    p.append(f'<text x="{sx(3)+6:.1f}" y="{Y1+12}" class="t-small">Today</text>')
    p.append(f'<path class="band" data-part="band" d="{band}"/>')
    p.append(f'<path class="fit" data-part="fit" d="{fit}"/>')
    p.append(f'<path class="proj" data-part="proj" d="{proj}"/>')
    p.append('<g data-part="pts">' + "".join(f'<circle class="pt" cx="{sx(t):.1f}" cy="{sy(v):.1f}" r="3.2"/>' for t, v, w in pts) + '</g>')
    vis = tstar <= 10
    tx = sx(min(tstar, 10))
    vis_attr = '' if vis else ' visibility="hidden"'
    p.append(f'<g data-part="cross"{vis_attr}><line class="marker-line" x1="{tx:.1f}" y1="{sy(AGING_THR):.1f}" x2="{tx:.1f}" y2="{Y0}"/>'
             f'<circle cx="{tx:.1f}" cy="{sy(AGING_THR):.1f}" r="6" style="fill:var(--bg);stroke:var(--gold);stroke-width:2"/></g>')
    label = f"Time-to-threshold: {tstar:.1f} years" if vis else "Time-to-threshold: beyond 10 years"
    lx, anc = aging_label_pos(tx, vis)
    p.append(f'<text data-part="label" x="{lx:.1f}" y="{Y0-14}" class="t-strong t-gold" text-anchor="{anc}">{label}</text>')
    p.append('</svg>')
    return "".join(p)


def aging_js_data():
    out = {}
    for t in AGING_TEMPS:
        A, pts, tstar = aging_series(t)
        out[t] = {"A": A, "pts": pts, "tstar": round(tstar, 2)}
    return {"n": AGING_N, "thr": AGING_THR, "temps": out}


# ---------------------------------------------------------------- variation maps
def _ramp(v):
    v = max(0.0, min(1.0, v))
    stops = [(0.0, (38, 33, 14)), (0.45, (108, 96, 42)), (0.75, (210, 162, 30)), (1.0, (243, 221, 143))]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if v <= b:
            f = (v - a) / (b - a)
            return "#%02x%02x%02x" % tuple(int(ca[i] + (cb[i]-ca[i])*f) for i in range(3))
    return "#f3dd8f"


def variation_map(kind, uid, n=16):
    rng = random.Random({"random": 11, "systematic": 23, "spatial": 37}[kind])
    cells = []
    blocks = [[rng.random() for _ in range(4)] for _ in range(4)]
    for r in range(n):
        for c in range(n):
            if kind == "random":
                v = rng.random()
            elif kind == "systematic":
                v = 0.15 + 0.8 * (c / (n-1) * 0.6 + (1 - r/(n-1)) * 0.4) + rng.uniform(-0.04, 0.04)
            else:
                v = 0.2 + 0.7 * blocks[r // 4][c // 4] + rng.uniform(-0.05, 0.05)
            cells.append(f'<rect x="{c*10}" y="{r*10}" width="9" height="9" fill="{_ramp(v)}"/>')
    title = {"random": "Random variation", "systematic": "Systematic variation", "spatial": "Spatial variation, down-sampled"}[kind]
    return (f'<svg viewBox="-2 -2 162 162" role="img" aria-label="Schematic map: {title} across a die" id="{uid}">'
            f'<rect x="-2" y="-2" width="162" height="162" fill="#0a0a0a"/>' + "".join(cells) + '</svg>')


# ---------------------------------------------------------------- hero package
def hero_field(n=22, seed=2026):
    rng = random.Random(seed)
    vals = []
    for r in range(n):
        for c in range(n):
            sysv = 0.5 * (c/(n-1)) + 0.5 * (r/(n-1))
            spat = math.sin(c*0.45) * math.cos(r*0.38)
            v = 0.52 + 0.20*(1-sysv) + 0.08*spat + rng.gauss(0, 0.07)
            vals.append(v)
    for idx in [rng.randrange(n*n) for _ in range(5)]:
        vals[idx] = rng.uniform(0.02, 0.14)
    vals = [round(max(0.0, min(1.0, v)), 3) for v in vals]
    return vals


def slack_pct(v):
    return 8 + v * 52


def hero_package(uid):
    n = 22
    vals = hero_field(n)
    S, P0 = 520, 84
    tile = 16
    p = [f'<svg viewBox="0 0 {S} {S}" aria-hidden="true" focusable="false">']
    # pins on four sides
    for i in range(18):
        o = 70 + i * 21.2
        p.append(f'<rect x="{o:.1f}" y="14" width="9" height="22" rx="1.5" style="fill:var(--gold-deep);opacity:.75"/>')
        p.append(f'<rect x="{o:.1f}" y="{S-36}" width="9" height="22" rx="1.5" style="fill:var(--gold-deep);opacity:.75"/>')
        p.append(f'<rect x="14" y="{o:.1f}" width="22" height="9" rx="1.5" style="fill:var(--gold-deep);opacity:.75"/>')
        p.append(f'<rect x="{S-36}" y="{o:.1f}" width="22" height="9" rx="1.5" style="fill:var(--gold-deep);opacity:.75"/>')
    p.append(f'<rect x="36" y="36" width="{S-72}" height="{S-72}" rx="10" style="fill:#151515;stroke:#3a3a3a;stroke-width:1.5"/>')
    p.append(f'<rect x="46" y="46" width="{S-92}" height="{S-92}" rx="6" style="fill:#101010;stroke:#262626"/>')
    p.append('<circle cx="66" cy="66" r="6" style="fill:#262626"/>')
    p.append(f'<rect x="{P0-6}" y="{P0-6}" width="{n*tile+12}" height="{n*tile+12}" rx="4" style="fill:#080808;stroke:#2a2a2a"/>')
    for r in range(n):
        for c in range(n):
            v = vals[r*n + c]
            col = "#f06024" if v < 0.18 else _ramp(v)
            p.append(f'<rect x="{P0 + c*tile}" y="{P0 + r*tile}" width="{tile-2}" height="{tile-2}" rx="1.5" fill="{col}"/>')
    p.append(f'<text x="{S/2}" y="{S-54}" text-anchor="middle" style="font:500 11px var(--font-mono);fill:#6b675f;letter-spacing:.14em">PER-ELEMENT SLACK · LIVE</text>')
    p.append('</svg>')
    sl = sorted(slack_pct(v) for v in vals)
    med = sl[len(sl)//2]
    flagged = sum(1 for v in vals if v < 0.18)
    stats = {"median": round(med, 1), "min": round(sl[0], 1), "flagged": flagged}
    return "".join(p), vals, stats


# ---------------------------------------------------------------- hero background traces (echo of the logo's F)
def hero_traces(kind="home"):
    """Background circuit traces that echo the logo's F. The page variant keeps to the right edge."""
    if kind == "page":
        # nested L-shaped traces rising from the bottom edge, like the two traces in the logo's F; they never cross
        out = ['<svg class="hero-traces hero-traces--page" viewBox="0 0 1440 420" preserveAspectRatio="xMaxYMid slice" aria-hidden="true" focusable="false"><g class="trace-g">']
        ends = [1392, 1296, 1368, 1248, 1330]
        for i, xe in enumerate(ends):
            x = 1010 + i * 30
            y = 96 + i * 46
            out.append(f'<path d="M{x} 430 V{y+12} Q{x} {y} {x+12} {y} H{xe}"/><circle cx="{xe+7}" cy="{y}" r="7"/>')
        out.append('</g></svg>')
        return "".join(out)
    rng = random.Random(7)
    out = ['<svg class="hero-traces" viewBox="0 0 1440 720" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false"><g class="trace-g">']
    for i in range(16):
        x = rng.randrange(-40, 1400); y = rng.randrange(20, 700)
        up = rng.randrange(40, 160); run = rng.randrange(60, 260)
        out.append(f'<path d="M{x} {y} V{y-up+10} Q{x} {y-up} {x+10} {y-up} H{x+run}"/><circle cx="{x+run+7}" cy="{y-up}" r="7"/>')
    out.append('</g></svg>')
    return "".join(out)


def market_icon(kind):
    """Small decorative line art for the market cards."""
    if kind == "dc":
        g = ['<svg class="market-art" viewBox="0 0 120 120" aria-hidden="true" focusable="false">']
        for r in range(3):
            for c in range(3):
                x, y = 12 + c*36, 12 + r*36
                cls = "ma-chip ma-warn" if (r, c) == (1, 1) else "ma-chip"
                g.append(f'<rect class="{cls}" x="{x}" y="{y}" width="24" height="24" rx="3"/>')
        for r in range(3):
            g.append(f'<path class="ma-link" d="M36 {24+r*36} H48 M72 {24+r*36} H84"/>')
            g.append(f'<path class="ma-link" d="M{24+r*36} 36 V48 M{24+r*36} 72 V84"/>')
        g.append('</svg>')
        return "".join(g)
    return ('<svg class="market-art" viewBox="0 0 120 120" aria-hidden="true" focusable="false">'
            '<g transform="translate(60 60) scale(1.7)" class="ma-sat">'
            '<rect x="-7" y="-7" width="14" height="14" rx="2" transform="rotate(45)"/>'
            '<path d="M-10 -10 L-22 -22 M-26 -18 L-18 -26 L-6 -14 L-14 -6 Z"/>'
            '<path d="M10 10 L22 22 M26 18 L18 26 L6 14 L14 6 Z"/>'
            '<path d="M12 -4 A10 10 0 0 1 4 -12 M16 -8 A16 16 0 0 1 8 -16"/></g></svg>')
