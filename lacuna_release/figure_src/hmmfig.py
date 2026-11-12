"""hmm.svg: the role of the HMM in LACUNA (textbook-level structure; no LACUNA-specific component is shown)."""
import re
from figs import FONT, GREEN, AMBER, BLUE, INK, MUTED, LINE, DEFS, street, minimap, blob, card, text, arrow, pin, pause


def m(x, y, s, size=14, fill=INK, weight=400, anchor="start"):
    """text with _{...} subscripts rendered as lowered, smaller tspans"""
    out, pos = [], 0
    for mt in re.finditer(r"_\{([^}]*)\}", s):
        out.append(s[pos:mt.start()])
        out.append(f'<tspan dy="{size * 0.3:.1f}" font-size="{size * 0.72:.1f}">{mt.group(1)}</tspan><tspan dy="{-size * 0.3:.1f}">​</tspan>')
        pos = mt.end()
    out.append(s[pos:])
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{"".join(out)}</text>'


W, H = 1200, 470
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">', DEFS,
     f'<rect width="{W}" height="{H}" rx="16" fill="#ffffff"/>']
# row labels
rows = [(98, "Observation", "camera image"), (252, "Hidden state", "robot position, on or off the map"), (392, "Output", "position or abstain")]
for y, a, b in rows:
    o.append(text(24, y, a, 15, INK, 700) + text(24, y + 20, b, 12.5, MUTED))
XS = (330, 530, 730); SUB = ("t−1", "t", "t+1")
# observations
for k, cx in enumerate(XS):
    o.append(street(cx - 46, 64, 92, 64, v=k))
    o.append(m(cx + 54, 82, f"z_{{{SUB[k]}}}", 15, INK, 600))
# hidden states (mini maps: on map, in a hole, on map)
for k, cx in enumerate(XS):
    cy = 252
    o.append(f'<circle cx="{cx}" cy="{cy}" r="44" fill="#ffffff" stroke="{GREEN}" stroke-width="2.2"/>')
    mm, (h0, h1, ym, ya) = minimap(cx - 32, cy - 22, 64, 44, hole=True, dots=False); o.append(mm)
    bx = (h0 + h1) / 2 if k == 1 else (h0 - 7 if k == 0 else h1 + 7)
    o.append(blob(bx, ym, 9, 6, 0.95))
    o.append(m(cx + 50, cy - 34, f"x_{{{SUB[k]}}}", 15, INK, 600))
    # emission arrow (state -> observation)
    o.append(f'<line x1="{cx}" y1="{cy - 46}" x2="{cx}" y2="{136}" stroke="#94a3b8" stroke-width="2" marker-end="url(#ah)"/>')
    # output
    o.append(f'<line x1="{cx}" y1="{cy + 46}" x2="{cx}" y2="{356}" stroke="#94a3b8" stroke-width="2" marker-end="url(#ah)"/>')
    if k == 1:
        o.append(f'<rect x="{cx - 52}" y="364" width="104" height="34" rx="17" fill="#fffbeb" stroke="#fde68a"/>'
                 + pause(cx - 30, 381, AMBER, 0.72) + text(cx - 14, 386, "abstain", 13.5, AMBER, 700))
    else:
        o.append(f'<rect x="{cx - 52}" y="364" width="104" height="34" rx="17" fill="#f0fdf4" stroke="#bbf7d0"/>'
                 + pin(cx - 28, 392, GREEN, 0.62) + text(cx - 12, 386, "position", 13.5, GREEN, 700))
o.append(text(XS[1], 424, "robot is off the map", 12, MUTED, 400, "middle"))
# transitions
for a, b in zip(XS, XS[1:]):
    o.append(f'<line x1="{a + 46}" y1="252" x2="{b - 48}" y2="252" stroke="{BLUE}" stroke-width="2.4" marker-end="url(#ah)"/>')
    o.append(m((a + b) / 2, 240, f"u_{{{SUB[XS.index(b)]}}}", 13, BLUE, 600, "middle"))
for x1, x2 in ((XS[0] - 92, XS[0] - 48), (XS[2] + 48, XS[2] + 92)):
    o.append(f'<line x1="{x1}" y1="252" x2="{x2}" y2="252" stroke="#94a3b8" stroke-width="2" stroke-dasharray="4 4" marker-end="url(#ah)"/>')
o.append(text(XS[0] + 14, 175, "observation model", 12.5, MUTED, 600) + text(XS[0] + 14, 191, "similarity to map images", 12, MUTED))
o.append(text(XS[1], 292 + 12, "", 1))
o.append(text((XS[0] + XS[1]) / 2, 280, "motion model", 12.5, BLUE, 600, "middle") + text((XS[0] + XS[1]) / 2, 296, "odometry", 12, BLUE, 400, "middle"))
o.append(text(XS[0] + 14, 330, "decision", 12.5, MUTED, 600) + text(XS[0] + 14, 346, "confident or not", 12, MUTED))
# forward filtering box
bx, by = 840, 40
o.append(card(bx, by, 340, 248, LINE, "#f8fafc"))
o.append(text(bx + 20, by + 32, "At every frame", 15, INK, 700))
o.append(text(bx + 20, by + 64, "1. predict the motion from odometry", 12.5, BLUE, 600))
_l = m(bx + 20, by + 88, "prior(x_{t}) = ΣSUMX p(x_{t} | x_{t−1}, u_{t}) · post(x_{t−1})", 13.5)
o.append(_l.replace("SUMX", '<tspan dy="5" font-size="9.5">x</tspan><tspan dy="2" font-size="7.5">t−1</tspan><tspan dy="-7">\u200b</tspan>'))
o.append(text(bx + 20, by + 124, "2. correct it with the camera image", 12.5, GREEN, 600))
o.append(m(bx + 20, by + 148, "post(x_{t}) ∝ p(z_{t} | x_{t}) · prior(x_{t})", 13.5))
o.append(text(bx + 20, by + 184, "3. decide", 12.5, INK, 600))
o.append(text(bx + 20, by + 206, "report a position only when confident,", 13, "#334155"))
o.append(text(bx + 20, by + 225, "otherwise abstain", 13, "#334155"))
o.append(card(bx, 304, 340, 120, GREEN, "#f0fdf4", 2))
o.append(text(bx + 20, 334, "LACUNA", 15, GREEN, 800))
o.append(text(bx + 20, 358, "Open world: the hidden states also cover", 13, "#334155"))
o.append(text(bx + 20, 377, "places that are not on the map.", 13, "#334155"))
o.append(text(bx + 20, 404, "Further details in the paper.", 13, MUTED, 400, "start", True))
o.append("</svg>")
open("hmm.svg", "w").write("".join(o)); print("ok")
