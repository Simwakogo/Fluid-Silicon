# Builds the Fluid Silicon logo SVGs: the IC-package mark plus an outlined wordmark (Carlito Bold, metric-compatible with the original's face).
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
import json
F = TTFont('/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf')
gs = F.getGlyphSet(); cmap = F.getBestCmap(); upm = F['head'].unitsPerEm
cap = F['OS/2'].sCapHeight
def word(text, tracking=0.0):
    x = 0; parts = []
    for ch in text:
        g = cmap[ord(ch)]; glyph = gs[g]
        pen = SVGPathPen(gs); glyph.draw(pen)
        d = pen.getCommands()
        parts.append((x, d))
        x += glyph.width + tracking*upm
    return parts, x - tracking*upm
def path_group(parts, scale, dx, dy, fill):
    out = []
    for x, d in parts:
        out.append(f'<path transform="translate({dx + x*scale:.2f} {dy:.2f}) scale({scale:.5f} {-scale:.5f})" d="{d}" fill="{fill}"/>')
    return "\n".join(out)
fl, wf = word("FLUID", 0.0); si, ws = word("SILICON", 0.0)
print("upm", upm, "cap", cap, "widths", wf, ws)
MARK = '''<g class="fs-mark">
  <rect x="0" y="0" width="64" height="64" rx="3" fill="{border}"/>
  <rect x="3.5" y="3.5" width="57" height="57" rx="1.5" fill="{lid}"/>
  <path d="M3.5 3.5 H60.5 L58.8 5.2 H5.2 V58.8 L3.5 60.5 Z" fill="#ffffff" opacity=".10"/>
  <g fill="none" stroke="{trace}" stroke-width="3.3" stroke-linecap="round" stroke-linejoin="round">
    <path d="M17.6 27.4 V19.4 Q17.6 15 22 15 H40.6"/>
    <path d="M17.6 42.6 V35.4 Q17.6 31 22 31 H31.2"/>
  </g>
  <g fill="{lid}" stroke="{trace}" stroke-width="3.1">
    <circle cx="44.4" cy="15" r="3.7"/>
    <circle cx="35" cy="31" r="3.7"/>
    <circle cx="17.6" cy="46.6" r="3.9"/>
  </g>
</g>'''
def logo(ink, gold, border="#C64E00", lid="#F06024", trace="#FFFFFF", title="Fluid Silicon"):
    capH = 34.0                      # wordmark cap height in the 64-unit mark space
    s = capH / cap
    gap = 12.0
    x0 = 64 + 11
    y_base = 32 + capH/2             # vertically centre the caps on the mark
    fx = x0; sx = x0 + wf*s + 1.2
    total = sx + ws*s
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total:.1f} 64" role="img" aria-label="{title}"><title>{title}</title>
{MARK.format(border=border, lid=lid, trace=trace)}
<g class="fs-word-fluid">{path_group(fl, s, fx, y_base, ink)}</g>
<g class="fs-word-silicon">{path_group(si, s, sx, y_base, gold)}</g>
</svg>'''
    return svg, total
dark, W = logo("#F4F2ED", "#D2A21E")
light, _ = logo("#121212", "#967200")
mark_only = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="Fluid Silicon"><title>Fluid Silicon</title>{MARK.format(border="#C64E00", lid="#F06024", trace="#FFFFFF")}</svg>'
open('src/assets/img/logo-on-dark.svg','w').write(dark)
open('src/assets/img/logo-on-light.svg','w').write(light)
open('src/assets/img/mark.svg','w').write(mark_only)
json.dump({"width": W}, open('logo-meta.json', 'w'))  # build info only, not shipped
print("logo width units", round(W,1), "aspect", round(W/64,2))
