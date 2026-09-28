"""Build-time SVG for the Fluid Silicon site: line icons, an FPGA card illustration and two charts.

Everything here is static. Colors come from CSS classes on the page (light theme), except the
illustration, which carries its own shades so it looks the same wherever it is placed.
"""
import math, random, html

esc = html.escape

# ---------------------------------------------------------------- line icons (24 x 24, stroke)
ICONS = {
    "chip": '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 6V3M15 6V3M9 21v-3M15 21v-3M6 9H3M6 15H3M21 9h-3M21 15h-3"/><rect x="10" y="10" width="4" height="4" rx=".5"/>',
    "variation": '<path d="M3 17l4-6 4 3 4-8 3 5 3-2"/><path d="M3 21h18"/>',
    "aging": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/><path d="M3.5 9.5A9 9 0 0 1 6 5.5"/>',
    "visibility": '<path d="M3 3l18 18"/><path d="M10.6 6.3A9.8 9.8 0 0 1 12 6.2c5 0 8.6 3.7 9.8 5.8a1.4 1.4 0 0 1 0 1.4 12.6 12.6 0 0 1-2.9 3.3"/><path d="M6.6 6.7A12.7 12.7 0 0 0 2.2 12a1.4 1.4 0 0 0 0 1.4c1.2 2.1 4.8 5.8 9.8 5.8a10 10 0 0 0 4.4-1"/><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/>',
    "monitor": '<path d="M3 12h4l2.5-6 3 12 2.5-6h6"/>',
    "model": '<path d="M4 19c3-9 8-13 16-13"/><path d="M4 19h16M4 19V5"/><circle cx="10" cy="12.5" r="1.3"/><circle cx="15" cy="8.6" r="1.3"/>',
    "tune": '<path d="M4 8h9M17 8h3M4 16h3M11 16h9"/><circle cx="15" cy="8" r="2.2"/><circle cx="9" cy="16" r="2.2"/>',
    "repair": '<path d="M14.5 6.5a4 4 0 0 0 4.7 4.7L21 13l-3.4 3.4-1.8-1.8-8.2 8.2a1.6 1.6 0 0 1-2.3-2.3l8.2-8.2-1.8-1.8L15 7.1a4 4 0 0 0-.5-.6z"/><path d="M3 21l3-3"/>',
    "shield": '<path d="M12 3l7 3v6c0 4.5-3 7.6-7 9-4-1.4-7-4.5-7-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
    "layers": '<path d="M12 4l9 4.5-9 4.5-9-4.5z"/><path d="M3 13l9 4.5 9-4.5M3 17.5L12 22l9-4.5"/>',
    "bolt": '<path d="M13 3L5 13h6l-1 8 8-11h-6z"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="M8.5 12.2l2.4 2.4 4.8-5"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    "flag": '<path d="M5 21V4"/><path d="M5 4h11l-2 4 2 4H5"/>',
    "rack": '<rect x="4" y="3" width="16" height="18" rx="1.5"/><path d="M4 9h16M4 15h16"/><circle cx="8" cy="6" r=".9"/><circle cx="8" cy="12" r=".9"/><circle cx="8" cy="18" r=".9"/>',
    "satellite": '<rect x="9" y="9" width="6" height="6" rx="1" transform="rotate(45 12 12)"/><path d="M8.5 8.5L3.5 3.5M15.5 15.5l5 5"/><path d="M2 6l4-4 3 3-4 4zM15 19l4-4 3 3-4 4z"/>',
    "plane": '<path d="M10.5 20l1.5-6 6-4.5a2 2 0 0 0-2.4-3.2L10 10 4 8l-1.5 1.5 4.5 3-1 3-2.5.5L3 17l4.5 1.5L9 22z"/>',
    "radar": '<path d="M4 12a8 8 0 0 1 13.7-5.6"/><path d="M8 12a4 4 0 0 1 6.9-2.8"/><path d="M12 12l7-7"/><path d="M12 12v9M8 21h8"/>',
    "tower": '<path d="M12 3v18M8 21l4-9 4 9M9.5 11.5h5"/><path d="M6.5 8.5a7.5 7.5 0 0 1 11 0M8.7 10.7a4.5 4.5 0 0 1 6.6 0"/>',
    "thermo": '<path d="M10 14.5V5a2 2 0 0 1 4 0v9.5a3.5 3.5 0 1 1-4 0z"/><path d="M12 9v6"/>',
    "power": '<path d="M12 3v9"/><path d="M7 6.5a7.5 7.5 0 1 0 10 0"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.3-4.3"/>',
    "doc": '<path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5M10 13h6M10 17h6"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
}


def icon(name, cls="ic"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{ICONS[name]}</svg>'


# ---------------------------------------------------------------- FPGA accelerator card, isometric
def _iso(x, y, z=0.0):
    """Isometric projection: x runs right-down, y runs left-down, z up."""
    return (0.866 * (x - y), 0.5 * (x + y) - z)


def _poly(points, fill, extra=""):
    d = " ".join(f"{px:.1f},{py:.1f}" for px, py in points)
    return f'<polygon points="{d}" fill="{fill}"{extra}/>'


def _box(p, x, y, z, l, w, h, top, left, right, extra=""):
    """A box on the card: base corner (x, y) at height z, size l along x, w along y, h tall."""
    out = [_poly([p(x, y, z + h), p(x + l, y, z + h), p(x + l, y + w, z + h), p(x, y + w, z + h)], top, extra),
           _poly([p(x, y + w, z), p(x + l, y + w, z), p(x + l, y + w, z + h), p(x, y + w, z + h)], left, extra),
           _poly([p(x + l, y, z), p(x + l, y + w, z), p(x + l, y + w, z + h), p(x + l, y, z + h)], right, extra)]
    return "".join(out)


def card_illustration(uid, glow=True):
    """A full-height FPGA accelerator card. Neutral colors: the card is the customer's, not ours."""
    L, W, T = 330, 132, 5           # PCB length, width, thickness
    p = lambda a, b, c: _iso(a - L / 2, b - W / 2, c)
    parts = [f'<svg class="illus" viewBox="0 0 640 400" role="img" aria-labelledby="{uid}-t"><title id="{uid}-t">An FPGA accelerator card, drawn in isometric view</title>',
             f'<defs><filter id="{uid}-sh" x="-20%" y="-20%" width="140%" height="160%"><feGaussianBlur stdDeviation="10"/></filter>'
             f'<linearGradient id="{uid}-lid" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4a4a4a"/><stop offset="1" stop-color="#2a2a2a"/></linearGradient>'
             f'<linearGradient id="{uid}-pcb" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1f3a30"/><stop offset="1" stop-color="#16291f"/></linearGradient></defs>',
             '<g transform="translate(320 214)">',
             f'<ellipse cx="0" cy="116" rx="236" ry="44" fill="#000" opacity=".11" filter="url(#{uid}-sh)"/>']
    # bracket (metal) at the back end, standing up
    parts.append(_poly([p(-6, 0, 0), p(-6, W, 0), p(-6, W, 70), p(-6, 0, 70)], "#c9ccd1"))
    parts.append(_poly([p(-6, 0, 70), p(-1, 0, 70), p(-1, W, 70), p(-6, W, 70)], "#e2e4e7"))
    parts.append(_poly([p(-6, W, 0), p(-1, W, 0), p(-1, W, 70), p(-6, W, 70)], "#aeb2b8"))
    # PCB slab
    parts.append(_box(p, 0, 0, 0, L, W, T, f"url(#{uid}-pcb)", "#101c16", "#142419"))
    # faint traces on the top face
    rng = random.Random(3)
    tr = []
    for i in range(14):
        x0 = rng.uniform(20, L - 60); y0 = rng.uniform(10, W - 10); run = rng.uniform(30, 90)
        a, b = p(x0, y0, T + 0.2), p(x0 + run, y0, T + 0.2)
        tr.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}"/>')
    parts.append('<g stroke="#2d5a47" stroke-width="1" opacity=".7">' + "".join(tr) + '</g>')
    # PCIe edge connector along the front edge, gold fingers
    parts.append(_box(p, 40, W - 3, -8, 150, 3, 8, "#b8912a", "#8f6f1c", "#d4ab3a"))
    fingers = []
    for i in range(26):
        x = 44 + i * 5.6
        a, b = p(x, W, -7), p(x, W, -1)
        fingers.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}"/>')
    parts.append('<g stroke="#6b520f" stroke-width=".8">' + "".join(fingers) + '</g>')
    # network cages at the bracket end
    parts.append(_box(p, 2, 14, T, 46, 24, 16, "#8d9298", "#5f646a", "#767b81"))
    parts.append(_box(p, 2, 46, T, 46, 24, 16, "#8d9298", "#5f646a", "#767b81"))
    # memory modules
    for k in range(4):
        parts.append(_box(p, 230 + k * 22, 18, T, 14, 44, 3, "#2f2f2f", "#1c1c1c", "#262626"))
    # power stage and small parts
    for k in range(6):
        parts.append(_box(p, 70 + k * 12, 108, T, 8, 10, 6, "#4b4f55", "#33363b", "#3e4247"))
    for k in range(5):
        parts.append(_box(p, 240 + k * 16, 96, T, 9, 9, 5, "#2b2b2b", "#191919", "#222"))
    # the FPGA package: substrate, then lid
    parts.append(_box(p, 96, 30, T, 104, 80, 3, "#3b6b44", "#264a2e", "#2f5a38"))
    parts.append(_box(p, 104, 36, T + 3, 88, 68, 9, f"url(#{uid}-lid)", "#1d1d1d", "#262626"))
    if glow:
        # a measured-slack grid on the lid: the one hint of what the product sees
        g = []
        for i in range(8):
            for j in range(6):
                x = 112 + i * 9.4; y = 42 + j * 9.4
                c = p(x + 3, y + 3, T + 12.2)
                v = 0.35 + 0.65 * rng.random()
                g.append(f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="1.6" fill="#f0c24a" opacity="{v:.2f}"/>')
        parts.append("".join(g))
    parts.append('</g></svg>')
    return "".join(parts)


# ---------------------------------------------------------------- charts
def _bell(mu, sigma, h, y0, skew=0.0, x_from=None, x_to=None, step=3):
    pts = []
    a, b = (x_from or mu - 4 * sigma), (x_to or mu + 5 * sigma)
    x = a
    while x <= b:
        z = (x - mu) / sigma
        dens = math.exp(-0.5 * z * z) * (1 + math.erf(skew * z / math.sqrt(2)))
        pts.append((x, y0 - h * dens))
        x += step
    return pts


def _area(pts, y0):
    return f"M{pts[0][0]:.1f} {y0} " + " ".join(f"L{x:.1f} {y:.1f}" for x, y in pts) + f" L{pts[-1][0]:.1f} {y0} Z"


def margin_chart(uid):
    """Two panels: one margin for the whole fleet, versus a margin per chip."""
    y0 = 236
    p = [f'<svg class="chart" viewBox="0 0 1100 320" role="img" aria-labelledby="{uid}-t {uid}-d">',
         f'<title id="{uid}-t">One margin for the fleet, compared with a margin per chip</title>',
         f'<desc id="{uid}-d">Left: a wide distribution of path delays across a fleet, with the worst-case corner far to the right of the typical chip, so every chip carries 30 to 54 percent timing margin. '
         f'Right: three chips measured separately, each with narrow distributions for LUT links and carry links, and each signed off at its own measured delay plus under 20 picoseconds of error and drift.</desc>',
         f'<defs><marker id="{uid}-m" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto-start-reverse" markerUnits="userSpaceOnUse"><path d="M0 .5 L7 4 L0 7.5 Z" class="c-gold-fill"/></marker></defs>']
    fleet = _bell(170, 44, 96, y0, skew=2.2, x_from=66, x_to=430)
    peak_x = max(fleet, key=lambda q: -q[1])[0]
    p += ['<text x="40" y="34" class="c-title">Today: one margin for the whole fleet</text>',
          f'<line class="c-axis" x1="40" y1="{y0}" x2="510" y2="{y0}"/>',
          f'<path class="c-fleet" d="{_area(fleet, y0)}"/>',
          f'<line class="c-corner" x1="470" y1="70" x2="470" y2="{y0}"/>',
          '<text x="462" y="62" class="c-small c-red" text-anchor="end">Worst-case corner</text>',
          f'<line x1="{peak_x:.0f}" y1="118" x2="462" y2="118" class="c-gold" marker-start="url(#{uid}-m)" marker-end="url(#{uid}-m)"/>',
          f'<text x="{(peak_x + 462) / 2:.0f}" y="108" class="c-strong c-gold-text" text-anchor="middle">30–54% timing margin*</text>',
          f'<text x="{peak_x:.0f}" y="{y0 + 22}" class="c-small" text-anchor="middle">typical chip</text>',
          f'<text x="510" y="{y0 + 44}" class="c-small" text-anchor="end">Path delay →</text>']
    ox = 570
    chips = [(150, "Chip A"), (250, "Chip B"), (338, "Chip C")]
    p += ['<text x="610" y="34" class="c-title">Measured: a margin per chip</text>',
          f'<line class="c-axis" x1="{ox + 40}" y1="{y0}" x2="{ox + 500}" y2="{y0}"/>',
          f'<line class="c-corner c-faint" x1="{ox + 470}" y1="70" x2="{ox + 470}" y2="{y0}"/>',
          f'<text x="{ox + 462}" y="62" class="c-small" text-anchor="end">Fleet corner, no longer needed</text>']
    for i, (mu, name) in enumerate(chips):
        mu += ox
        lut = _bell(mu, 13, 112 - i * 8, y0, x_from=mu - 44, x_to=mu + 48, step=2)
        car = _bell(mu + 9, 12, 84 - i * 6, y0, x_from=mu - 36, x_to=mu + 52, step=2)
        so = mu + 58
        p.append(f'<rect class="c-band" x="{mu + 40}" y="{y0 - 128}" width="{so - (mu + 40)}" height="128"/>')
        p.append(f'<path class="c-lut" d="{_area(lut, y0)}"/>')
        p.append(f'<path class="c-carry" d="{_area(car, y0)}"/>')
        p.append(f'<line class="c-signoff" x1="{so}" y1="{y0 - 128}" x2="{so}" y2="{y0}"/>')
        p.append(f'<text x="{mu + 4}" y="{y0 + 22}" class="c-small" text-anchor="middle">{name}</text>')
    p.append(f'<path d="M{ox + 199} {y0 - 128} V{y0 - 146} H{ox + 212}" class="c-gold" fill="none"/>')
    p.append(f'<text x="{ox + 216}" y="{y0 - 142}" class="c-small c-gold-text">Per-chip margin: error + drift, under 20 ps</text>')
    p.append(f'<text x="{ox + 500}" y="{y0 + 44}" class="c-small" text-anchor="end">Path delay →</text>')
    p.append('</svg>')
    return "".join(p)


AGING_TEMPS = {"45": 3.5, "55": 4.0, "70": 4.6}
AGING_N, AGING_THR = 0.2, 6.0


def aging_series(temp):
    A = AGING_TEMPS[temp]
    rng = random.Random(int(temp) * 7919)
    pts, t = [], 0.25
    while t <= 3.001:
        base = A * t ** AGING_N
        pts.append((round(t, 2), round(base + rng.uniform(-0.18, 0.18), 3), round(0.22 + 0.05 * t, 3)))
        t += 0.25
    return A, pts, (AGING_THR / A) ** (1 / AGING_N)


def aging_chart(uid, compact=False):
    """Three temperature curves on one chart: the same board ages at very different rates. compact: a 640 x 400 box for half-width columns."""
    X0, X1, Y0, Y1, W, H = (60, 616, 340, 40, 640, 400) if compact else (70, 1040, 300, 40, 1100, 360)
    sx = lambda t: X0 + (X1 - X0) * t / 10
    sy = lambda v: Y0 - (Y0 - Y1) * v / 8
    p = [f'<svg class="chart{" chart--fit" if compact else ""}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="{uid}-t {uid}-d">',
         f'<title id="{uid}-t">Illustrative aging model for one card at three temperatures</title>',
         f'<desc id="{uid}-d">Path delay increase over years in service. Measured points for the first three years lie on a fitted aging curve, projected forward. '
         f'At 70 degrees Celsius the projection crosses the 6 percent alert threshold at about 3.8 years, at 55 degrees at about 7.6 years, and at 45 degrees beyond 10 years.</desc>']
    for v in [0, 2, 4, 6, 8]:
        p.append(f'<line class="c-grid" x1="{X0}" y1="{sy(v):.1f}" x2="{X1}" y2="{sy(v):.1f}"/>')
        p.append(f'<text x="{X0 - 10}" y="{sy(v) + 4:.1f}" class="c-small" text-anchor="end">{v}%</text>')
    for t in [0, 2, 4, 6, 8, 10]:
        p.append(f'<text x="{sx(t):.1f}" y="{Y0 + 22}" class="c-small" text-anchor="middle">{t}</text>')
    p.append(f'<line class="c-axis" x1="{X0}" y1="{Y0}" x2="{X1}" y2="{Y0}"/>')
    p.append(f'<text x="{(X0 + X1) / 2:.0f}" y="{Y0 + 46}" class="c-small" text-anchor="middle">Years in service</text>')
    lx = X0 - 46
    p.append(f'<text x="{lx}" y="{(Y0 + Y1) / 2:.0f}" class="c-small" text-anchor="middle" transform="rotate(-90 {lx} {(Y0 + Y1) / 2:.0f})">Path delay increase</text>')
    p.append(f'<line class="c-threshold" x1="{X0}" y1="{sy(AGING_THR):.1f}" x2="{X1}" y2="{sy(AGING_THR):.1f}"/>')
    p.append(f'<text x="{X0 + 8}" y="{sy(AGING_THR) - 9:.1f}" class="c-small c-red">{"Alert threshold" if compact else "Alert threshold: margin used up"}</text>')
    p.append(f'<line class="c-marker" x1="{sx(3):.1f}" y1="{Y1}" x2="{sx(3):.1f}" y2="{Y0}"/>')
    p.append(f'<text x="{sx(3) + 6:.1f}" y="{Y1 + 12}" class="c-small">Today</text>')
    styles = {"45": "c-cool", "55": "c-mid", "70": "c-hot"}
    for temp in ["45", "55", "70"]:
        A, pts, tstar = aging_series(temp)
        fit = " ".join(f"{'M' if i == 0 else 'L'}{sx(t):.1f} {sy(A * t ** AGING_N):.1f}" for i, t in enumerate([0.05 + k * 0.05 for k in range(60)]))
        proj = " ".join(f"{'M' if i == 0 else 'L'}{sx(t):.1f} {sy(A * t ** AGING_N):.1f}" for i, t in enumerate([3 + k * 0.1 for k in range(71)]))
        cls = styles[temp]
        p.append(f'<path class="c-fit {cls}" d="{fit}"/>')
        p.append(f'<path class="c-proj {cls}" d="{proj}"/>')
        p.append("".join(f'<circle class="c-pt {cls}" cx="{sx(t):.1f}" cy="{sy(v):.1f}" r="2.8"/>' for t, v, w in pts))
        if tstar <= 10:
            tx = sx(tstar)
            p.append(f'<line class="c-marker" x1="{tx:.1f}" y1="{sy(AGING_THR) + 6:.1f}" x2="{tx:.1f}" y2="{Y0 - 44}"/>')
            p.append(f'<circle cx="{tx:.1f}" cy="{sy(AGING_THR):.1f}" r="5.5" class="c-cross {cls}"/>')
            p.append(f'<text x="{tx:.1f}" y="{Y0 - 26}" class="c-strong" text-anchor="middle">{temp} °C: {tstar:.1f} {"yrs" if compact else "years"}</text>')
        else:
            p.append(f'<text x="{X1}" y="{sy(A * 10 ** AGING_N) + 20:.1f}" class="c-strong" text-anchor="end">{temp} °C: {"> 10 yrs" if compact else "beyond 10 years"}</text>')
    p.append('</svg>')
    return "".join(p)


# ---------------------------------------------------------------- small charts for the product screens
def spark(values, w=300, h=56, cls="spark"):
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    n = len(values)
    pts = [(i * w / (n - 1), h - 6 - (v - lo) / span * (h - 12)) for i, v in enumerate(values)]
    line = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f} {y:.1f}" for i, (x, y) in enumerate(pts))
    area = line + f" L{w} {h} L0 {h} Z"
    return (f'<svg class="{cls}" viewBox="0 0 {w} {h}" aria-hidden="true" focusable="false" preserveAspectRatio="none">'
            f'<path class="spark-area" d="{area}"/><path class="spark-line" d="{line}"/>'
            f'<circle class="spark-end" cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="3"/></svg>')


def bars(values, w=300, h=64, cls="bars", low=2):
    n = len(values); hi = max(values) or 1; gap = 2
    bw = (w - gap * (n - 1)) / n
    out = [f'<svg class="{cls}" viewBox="0 0 {w} {h}" aria-hidden="true" focusable="false" preserveAspectRatio="none">']
    for i, v in enumerate(values):
        bh = v / hi * (h - 4)
        out.append(f'<rect x="{i * (bw + gap):.1f}" y="{h - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="1.5" class="{"bar-low" if i < low else "bar"}"/>')
    out.append('</svg>')
    return "".join(out)


def series(seed, n, base, drift, noise):
    rng = random.Random(seed)
    vals, v = [], base
    for i in range(n):
        v += drift + rng.uniform(-noise, noise)
        vals.append(round(v, 2))
    return vals


# ---------------------------------------------------------------- industry art (dark tiles; a photo can replace any of them)
_ART_BG = ('<defs><linearGradient id="{u}-g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#262421"/><stop offset="1" stop-color="#121212"/></linearGradient>'
           '<radialGradient id="{u}-glow" cx="0.7" cy="0.25" r="0.6"><stop offset="0" stop-color="#f06024" stop-opacity=".22"/><stop offset="1" stop-color="#f06024" stop-opacity="0"/></radialGradient></defs>'
           '<rect width="640" height="400" fill="url(#{u}-g)"/><rect width="640" height="400" fill="url(#{u}-glow)"/>')


def _floor(p, x0, x1, y0, y1, step=40, stroke="#2e2c28"):
    out = []
    x = x0
    while x <= x1:
        a, b = p(x, y0, 0), p(x, y1, 0)
        out.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}"/>'); x += step
    y = y0
    while y <= y1:
        a, b = p(x0, y, 0), p(x1, y, 0)
        out.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}"/>'); y += step
    return f'<g stroke="{stroke}" stroke-width="1">' + "".join(out) + '</g>'


def _leds(p, x, y, z, n, dx, colors, r=1.6):
    out = []
    for i in range(n):
        c = p(x + i * dx, y, z)
        out.append(f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{r}" fill="{colors[i % len(colors)]}"/>')
    return "".join(out)


def industry_art(kind, uid):
    """Six stylized scenes in the brand palette, drawn isometrically. Static, no text."""
    p = lambda a, b, c: _iso(a, b, c)
    head = f'<svg class="art" viewBox="0 0 640 400" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">{_ART_BG.format(u=uid)}'
    parts = [head]
    G = lambda tx, ty: f'<g transform="translate({tx} {ty})">'
    if kind == "racks":
        parts.append(G(330, 150))
        parts.append(_floor(p, -80, 360, -60, 200))
        for i in range(4):
            x = 20 + i * 84
            parts.append(_box(p, x, 20, 0, 60, 100, 190, "#3a3835", "#22201d", "#2c2a27"))
            for k in range(9):
                z = 14 + k * 19
                parts.append(_box(p, x + 60, 24 + 0, z, 0.1, 92, 12, "#2c2a27", "#1a1917", "#333130"))
                parts.append(_leds(p, x + 60.2, 30, z + 6, 3, 6, ["#f0c24a", "#1f8f3f", "#f0c24a"]))
        parts.append('</g>')
    elif kind == "accelerators":
        parts.append(G(330, 150))
        parts.append(_floor(p, -80, 360, -60, 200))
        for i in range(2):
            x = 60 + i * 150
            parts.append(_box(p, x, 20, 0, 110, 100, 190, "#3a3835", "#22201d", "#2c2a27"))
            for k in range(6):
                z = 12 + k * 30
                parts.append(_box(p, x + 110, 26, z, 0.1, 88, 22, "#2c2a27", "#1a1917", "#2f2d2a"))
                for j in range(4):
                    parts.append(_box(p, x + 111, 32 + j * 20, z + 3, 0.1, 14, 16, "#4b4744", "#2a2825", "#f06024" if (j + k) % 3 == 0 else "#6b5a24"))
        parts.append('</g>')
    elif kind == "satellite":
        rng = random.Random(11)
        for i in range(70):
            parts.append(f'<circle cx="{rng.uniform(0, 640):.0f}" cy="{rng.uniform(0, 400):.0f}" r="{rng.uniform(.4, 1.5):.1f}" fill="#fff" opacity="{rng.uniform(.25, .85):.2f}"/>')
        # Earth's limb, lower left
        parts.append(f'<defs><radialGradient id="{uid}-earth" cx="0.35" cy="0.3" r="0.8"><stop offset="0" stop-color="#2b5f9e"/><stop offset=".55" stop-color="#173a63"/><stop offset="1" stop-color="#0b1e36"/></radialGradient></defs>')
        parts.append(f'<circle cx="40" cy="600" r="380" fill="none" stroke="#6ea8ff" stroke-width="18" opacity=".12"/>')
        parts.append(f'<circle cx="40" cy="600" r="372" fill="url(#{uid}-earth)"/>')
        parts.append(f'<circle cx="40" cy="600" r="372" fill="none" stroke="#8fc1ff" stroke-width="1.5" opacity=".7"/>')
        parts.append(G(400, 190))
        BL, BW, BH = 64, 52, 78                      # bus: length along x, width along y, height
        ZC = BH / 2                                  # the wing axis runs through the bus at mid height
        WL, WH, WT = 170, 44, 2.5                    # wing length along y, height (z), thickness (x)
        def wing(y0, y1):
            # a slab standing on edge, along y, centred on the bus axis; cell grid on its visible +x face
            ya, yb = min(y0, y1), max(y0, y1)
            out = [_box(p, -WT / 2, ya, ZC - WH / 2, WT, yb - ya, WH, "#2b4f80", "#0f2440", "#173355")]
            for k in range(1, 7):
                yy = ya + k * (yb - ya) / 7
                q1, q2 = p(WT / 2 + .1, yy, ZC - WH / 2 + 2), p(WT / 2 + .1, yy, ZC + WH / 2 - 2)
                out.append(f'<line x1="{q1[0]:.1f}" y1="{q1[1]:.1f}" x2="{q2[0]:.1f}" y2="{q2[1]:.1f}" stroke="#5b8fd6" stroke-width="1" opacity=".9"/>')
            for zz in (ZC - WH / 6, ZC + WH / 6):
                q1, q2 = p(WT / 2 + .1, ya + 2, zz), p(WT / 2 + .1, yb - 2, zz)
                out.append(f'<line x1="{q1[0]:.1f}" y1="{q1[1]:.1f}" x2="{q2[0]:.1f}" y2="{q2[1]:.1f}" stroke="#5b8fd6" stroke-width="1" opacity=".9"/>')
            return "".join(out)
        def boom(y0, y1):
            a1, a2 = p(0, y0, ZC), p(0, y1, ZC)
            return f'<line x1="{a1[0]:.1f}" y1="{a1[1]:.1f}" x2="{a2[0]:.1f}" y2="{a2[1]:.1f}" stroke="#c9ccd1" stroke-width="3"/>'
        gap = 14
        # far wing (behind the bus), then the bus, then the near wing, so the array reads as one axis through the centre
        parts.append(wing(-BW / 2 - gap - WL, -BW / 2 - gap))
        parts.append(boom(-BW / 2 - gap, -BW / 2 + 4))
        # the bus: gold multilayer insulation, with a dark radiator panel on one face
        parts.append(_box(p, -BL / 2, -BW / 2, 0, BL, BW, BH, "#d9b654", "#8a6a1c", "#b9912e"))
        parts.append(_box(p, -BL / 2 + 8, BW / 2 + 0.1, 12, BL - 16, 0.1, BH - 24, "#2a2a2a", "#161616", "#3a3a3a"))
        parts.append(boom(BW / 2 - 4, BW / 2 + gap))
        parts.append(wing(BW / 2 + gap, BW / 2 + gap + WL))
        # dish on the +x face, pointing toward the viewer, with feed
        cx, cy, cz = BL / 2 + 6, 0, BH * 0.55
        rim = []
        for i in range(48):
            t = 2 * math.pi * i / 48
            q = p(cx, cy + 34 * math.cos(t), cz + 34 * math.sin(t))
            rim.append(f"{q[0]:.1f},{q[1]:.1f}")
        inner = []
        for i in range(48):
            t = 2 * math.pi * i / 48
            q = p(cx + 4, cy + 22 * math.cos(t), cz + 22 * math.sin(t))
            inner.append(f"{q[0]:.1f},{q[1]:.1f}")
        parts.append(f'<polygon points="{" ".join(rim)}" fill="#e6e8eb" stroke="#9aa0a6" stroke-width="1.5"/>')
        parts.append(f'<polygon points="{" ".join(inner)}" fill="#cfd3d8" opacity=".9"/>')
        f0, f1 = p(cx, cy, cz), p(cx + 30, cy, cz)
        parts.append(f'<line x1="{f0[0]:.1f}" y1="{f0[1]:.1f}" x2="{f1[0]:.1f}" y2="{f1[1]:.1f}" stroke="#c9ccd1" stroke-width="2.5"/>')
        parts.append(f'<circle cx="{f1[0]:.1f}" cy="{f1[1]:.1f}" r="3.5" fill="#f06024"/>')
        # a small antenna mast on top
        m0, m1 = p(-10, -10, BH), p(-10, -10, BH + 34)
        parts.append(f'<line x1="{m0[0]:.1f}" y1="{m0[1]:.1f}" x2="{m1[0]:.1f}" y2="{m1[1]:.1f}" stroke="#c9ccd1" stroke-width="2"/>')
        parts.append(f'<circle cx="{m1[0]:.1f}" cy="{m1[1]:.1f}" r="3" fill="#f0c24a"/>')
        parts.append('</g>')
    elif kind == "tower":
        parts.append(G(320, 380))
        # lattice mast
        for x in (-22, 22):
            parts.append(f'<line x1="{x}" y1="0" x2="{x * 0.35:.1f}" y2="-330" stroke="#8d9298" stroke-width="3"/>')
        y = 0
        k = 0
        while y > -320:
            w = 22 - (22 - 7.7) * (-y / 330)
            w2 = 22 - (22 - 7.7) * (-(y - 28) / 330)
            parts.append(f'<line x1="{-w:.1f}" y1="{y}" x2="{w:.1f}" y2="{y}" stroke="#6a6f75" stroke-width="1.5"/>')
            if k % 2 == 0:
                parts.append(f'<line x1="{-w:.1f}" y1="{y}" x2="{w2:.1f}" y2="{y - 28}" stroke="#6a6f75" stroke-width="1"/>')
            else:
                parts.append(f'<line x1="{w:.1f}" y1="{y}" x2="{-w2:.1f}" y2="{y - 28}" stroke="#6a6f75" stroke-width="1"/>')
            y -= 28; k += 1
        # antenna panels
        for i, ang in enumerate((-1, 0, 1)):
            x = ang * 34
            parts.append(f'<rect x="{x - 7}" y="-330" width="14" height="46" rx="3" fill="#dfe2e6" stroke="#9aa0a6"/>')
            parts.append(f'<line x1="{x}" y1="-284" x2="{ang * 8}" y2="-262" stroke="#8d9298" stroke-width="2"/>')
        parts.append('<circle cx="0" cy="-352" r="4" fill="#f06024"/><line x1="0" y1="-330" x2="0" y2="-352" stroke="#8d9298" stroke-width="2"/>')
        parts.append('</g>')
        # cabinet at the base
        parts.append(G(430, 300))
        parts.append(_box(p, 0, 0, 0, 50, 40, 70, "#3a3835", "#22201d", "#2c2a27"))
        parts.append(_leds(p, 50.2, 8, 40, 3, 10, ["#1f8f3f", "#f0c24a", "#1f8f3f"]))
        parts.append('</g>')
    elif kind == "bench":
        parts.append(G(330, 180))
        parts.append(_floor(p, -120, 320, -80, 200, step=50, stroke="#2a2825"))
        # oscilloscope
        parts.append(_box(p, 120, -40, 0, 150, 110, 90, "#d9d4c8", "#8f8a7e", "#b9b3a5"))
        s0, s1, s2, s3 = p(270.1, -30, 80), p(270.1, 60, 80), p(270.1, 60, 20), p(270.1, -30, 20)
        parts.append(f'<polygon points="{s0[0]:.1f},{s0[1]:.1f} {s1[0]:.1f},{s1[1]:.1f} {s2[0]:.1f},{s2[1]:.1f} {s3[0]:.1f},{s3[1]:.1f}" fill="#111"/>')
        # a trace on the screen
        pts = []
        for i in range(31):
            t = i / 30
            yv = -30 + 90 * t
            zv = 50 + 22 * math.sin(t * 12.6) * (1 if int(t * 4) % 2 == 0 else 0.35)
            q = p(270.3, yv, zv)
            pts.append(f"{q[0]:.1f},{q[1]:.1f}")
        parts.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="#f0c24a" stroke-width="2"/>')
        for k in range(4):
            parts.append(_leds(p, 270.2, -20 + k * 22, 10, 1, 0, ["#8f8a7e"], r=3))
        # board under test
        parts.append(_box(p, -60, 20, 0, 150, 90, 4, "#1f3a30", "#101c16", "#142419"))
        parts.append(_box(p, -10, 40, 4, 44, 44, 8, "#2a2a2a", "#1a1a1a", "#222"))
        for i in range(5):
            for j in range(5):
                c = p(-4 + i * 8, 46 + j * 8, 12.2)
                parts.append(f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="1.3" fill="#f0c24a" opacity=".8"/>')
        # probe
        a, b = p(40, 60, 14), p(150, -20, 60)
        parts.append(f'<path d="M{a[0]:.1f} {a[1]:.1f} C {a[0] + 40:.1f} {a[1] - 60:.1f}, {b[0] - 40:.1f} {b[1] + 30:.1f}, {b[0]:.1f} {b[1]:.1f}" fill="none" stroke="#f06024" stroke-width="2"/>')
        parts.append('</g>')
    else:  # factory: a conveyor of cards passing a scanner
        parts.append(G(320, 170))
        parts.append(_floor(p, -140, 340, -60, 220, step=50, stroke="#2a2825"))
        parts.append(_box(p, -120, 40, 0, 440, 70, 16, "#3a3835", "#22201d", "#2c2a27"))
        for i in range(5):
            x = -100 + i * 88
            parts.append(_box(p, x, 52, 16, 64, 46, 3, "#1f3a30", "#101c16", "#142419"))
            parts.append(_box(p, x + 20, 62, 19, 24, 24, 6, "#2a2a2a", "#1a1a1a", "#222"))
        # scanner arch
        parts.append(_box(p, 150, 30, 0, 12, 90, 90, "#d9d4c8", "#8f8a7e", "#b9b3a5"))
        parts.append(_box(p, 150, 30, 90, 12, 90, 10, "#d9d4c8", "#8f8a7e", "#b9b3a5"))
        a, b = p(156, 40, 88), p(156, 110, 88)
        c, d = p(156, 40, 16), p(156, 110, 16)
        parts.append(f'<polygon points="{a[0]:.1f},{a[1]:.1f} {b[0]:.1f},{b[1]:.1f} {d[0]:.1f},{d[1]:.1f} {c[0]:.1f},{c[1]:.1f}" fill="#f0c24a" opacity=".22"/>')
        parts.append('</g>')
    parts.append('</svg>')
    return "".join(parts)


# ---------------------------------------------------------------- resource thumbnails (16:10, light, an icon in gold)
def thumb(kind, uid):
    icon_for = {"brief": "doc", "margin": "variation", "aging": "aging", "fleet": "rack", "power": "power", "steps": "check", "shield": "shield", "chip": "chip"}
    name = icon_for.get(kind, "doc")
    out = [f'<svg class="thumb" viewBox="0 0 400 250" aria-hidden="true" focusable="false">',
           f'<defs><linearGradient id="{uid}-t" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f6f4ef"/><stop offset="1" stop-color="#f3ecd6"/></linearGradient></defs>',
           f'<rect width="400" height="250" fill="url(#{uid}-t)"/>']
    if kind == "brief":
        out.append('<rect x="130" y="40" width="140" height="180" rx="6" fill="#fff" stroke="#e5e1d8"/>'
                   '<rect x="150" y="66" width="80" height="8" rx="2" fill="#15130f"/><rect x="150" y="84" width="100" height="5" rx="2" fill="#cfc9bc"/>'
                   '<rect x="150" y="96" width="90" height="5" rx="2" fill="#cfc9bc"/><rect x="150" y="108" width="100" height="5" rx="2" fill="#cfc9bc"/>'
                   '<rect x="150" y="132" width="100" height="40" rx="3" fill="#f3ecd6"/><rect x="150" y="184" width="60" height="5" rx="2" fill="#cfc9bc"/>'
                   '<rect x="130" y="40" width="140" height="6" fill="#f06024"/>')
    else:
        out.append(f'<g transform="translate(152 77) scale(4)" fill="none" stroke="#a67c00" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</g>')
    rng = random.Random(len(kind))
    for i in range(6):
        x, y = rng.uniform(20, 380), rng.uniform(20, 230)
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="2" fill="#a67c00" opacity=".25"/>')
    out.append('</svg>')
    return "".join(out)


def margin_chart_half(uid):
    """The per-chip half of the margin chart, in a 600 x 340 box for half-width columns."""
    y0 = 256
    p = [f'<svg class="chart chart--fit" viewBox="0 0 600 340" role="img" aria-labelledby="{uid}-t {uid}-d">',
         f'<title id="{uid}-t">A margin per chip instead of one for the fleet</title>',
         f'<desc id="{uid}-d">Three chips measured separately, each with narrow distributions of LUT and carry link delays, and each signed off at its own measured delay plus under 20 picoseconds of error and drift. The fleet-wide worst-case corner is shown faintly on the right, no longer needed.</desc>']
    ox = 0
    chips = [(150, "Chip A"), (250, "Chip B"), (338, "Chip C")]
    p += ['<text x="40" y="34" class="c-title">Measured: a margin per chip</text>',
          f'<line class="c-axis" x1="{ox + 40}" y1="{y0}" x2="{ox + 540}" y2="{y0}"/>',
          f'<line class="c-corner c-faint" x1="{ox + 500}" y1="80" x2="{ox + 500}" y2="{y0}"/>',
          f'<text x="{ox + 492}" y="72" class="c-small" text-anchor="end">Fleet corner, no longer needed</text>']
    for i, (mu, name) in enumerate(chips):
        mu += ox
        lut = _bell(mu, 13, 112 - i * 8, y0, x_from=mu - 44, x_to=mu + 48, step=2)
        car = _bell(mu + 9, 12, 84 - i * 6, y0, x_from=mu - 36, x_to=mu + 52, step=2)
        so = mu + 58
        p.append(f'<rect class="c-band" x="{mu + 40}" y="{y0 - 128}" width="{so - (mu + 40)}" height="128"/>')
        p.append(f'<path class="c-lut" d="{_area(lut, y0)}"/>')
        p.append(f'<path class="c-carry" d="{_area(car, y0)}"/>')
        p.append(f'<line class="c-signoff" x1="{so}" y1="{y0 - 128}" x2="{so}" y2="{y0}"/>')
        p.append(f'<text x="{mu + 4}" y="{y0 + 22}" class="c-small" text-anchor="middle">{name}</text>')
    p.append(f'<path d="M{ox + 199} {y0 - 128} V{y0 - 150} H{ox + 212}" class="c-gold" fill="none"/>')
    p.append(f'<text x="{ox + 216}" y="{y0 - 146}" class="c-small c-gold-text">Per-chip margin: error + drift, under 20 ps</text>')
    p.append(f'<text x="{ox + 540}" y="{y0 + 44}" class="c-small" text-anchor="end">Path delay →</text>')
    p.append('</svg>')
    return "".join(p)
