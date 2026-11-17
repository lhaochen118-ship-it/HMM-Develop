"""Static README figures: io.svg (input / output) and method.svg (pipeline)."""
import math

FONT = "Inter, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
GREEN, GREEN_BG, AMBER, AMBER_BG, BLUE, INDIGO = "#16a34a", "#f0fdf4", "#d97706", "#fffbeb", "#2563eb", "#4f46e5"
INK, MUTED, LINE = "#0f172a", "#64748b", "#e2e8f0"
_id = [0]


def uid(p): _id[0] += 1; return f"{p}{_id[0]}"


def street(x, y, w=86, h=60, v=0, step=2.6):
    """perspective camera frame of a straight street; v = frame index: the camera moves `step` m forward per frame,
    so consecutive frames show the same buildings and tree coming closer"""
    c = uid("c"); f = w * 0.55; cx = x + w / 2; hy = y + h * 0.5; camH = 1.5; dmin = 0.9; sh = v * step

    def P(X, d, Y=0.0): return (cx + f * X / d, hy + f * (camH - Y) / d)

    def poly(pts, col, op=1.0): return f'<polygon points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" fill="{col}" fill-opacity="{op}"/>'
    o = [f'<clipPath id="{c}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6"/></clipPath><g clip-path="url(#{c})">',
         f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#dbeafe"/>', f'<rect x="{x}" y="{hy:.1f}" width="{w}" height="{y + h - hy:.1f}" fill="#e2e8f0"/>']
    o.append(poly([P(-3.2, dmin), P(3.2, dmin), P(3.2, 400), P(-3.2, 400)], "#64748b"))
    for k in range(12):                                            # lane dashes, 2 m long every 5 m
        d0 = 1.0 + k * 5 - (sh % 5)
        if d0 + 2 <= dmin: continue
        d0 = max(d0, dmin); o.append(poly([P(-0.13, d0), P(0.13, d0), P(0.13, d0 + 2), P(-0.13, d0 + 2)], "#ffffff"))
    B = [(-5, 2, 8, 4.5, "#94a3b8", "#cbd5e1"), (-5, 9, 15, 6.5, "#a5b4fc", "#c7d2fe"), (-5, 16, 26, 4.0, "#cbd5e1", "#e2e8f0"),
         (-5, 27, 40, 7.0, "#94a3b8", "#cbd5e1"), (5, 4, 10, 6.0, "#cbd5e1", "#e2e8f0"), (5, 11, 19, 4.5, "#94a3b8", "#cbd5e1"),
         (5, 20, 34, 6.5, "#a5b4fc", "#c7d2fe")]
    for X, d1, d2, Hb, side, cap in sorted(B, key=lambda b: -b[1]):  # far to near
        d1, d2 = d1 - sh, d2 - sh
        if d2 <= dmin: continue
        d1 = max(d1, dmin); sg = 1 if X > 0 else -1
        o.append(poly([P(X, d1), P(X, d2), P(X, d2, Hb), P(X, d1, Hb)], side))
        if d1 > dmin: o.append(poly([P(X, d1), P(X + sg * 6, d1), P(X + sg * 6, d1, Hb), P(X, d1, Hb)], cap))
    for X, d in ((-3.9, 7.0), (3.9, 14.0)):                          # trees
        d -= sh
        if d <= dmin: continue
        bx, by = P(X, d); tx, ty = P(X, d, 2.6)
        o.append(f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" stroke="#a16207" stroke-width="{max(0.8, f * 0.25 / d):.1f}"/>')
        o.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="{f * 1.1 / d:.1f}" fill="#86efac"/>')
    o.append('</g>' + f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="none" stroke="#cbd5e1"/>')
    return "".join(o)


def minimap(x, y, w, h, hole=True, dots=True):
    """top-down map: two streets + cross street, dots = map images, amber dashed hole"""
    o = []; ym, ya = y + h * 0.75, y + h * 0.25
    road = 'stroke="#e2e8f0" stroke-width="7" stroke-linecap="round"'
    o += [f'<line x1="{x + 8}" y1="{ym}" x2="{x + w - 8}" y2="{ym}" {road}/>', f'<line x1="{x + 8}" y1="{ya}" x2="{x + w - 8}" y2="{ya}" {road}/>',
          f'<line x1="{x + 0.12 * w}" y1="{ya}" x2="{x + 0.12 * w}" y2="{ym}" {road}/>', f'<line x1="{x + 0.88 * w}" y1="{ya}" x2="{x + 0.88 * w}" y2="{ym}" {road}/>']
    h0, h1 = x + 0.38 * w, x + 0.64 * w
    if hole:
        o.append(f'<rect x="{h0 - 3}" y="{ym - 13}" width="{h1 - h0 + 6}" height="26" rx="6" fill="#fef3c7" stroke="#f59e0b" stroke-width="1.2" stroke-dasharray="4 3"/>')
    if dots:
        g = []
        n = int((w - 16) / 6)
        for i in range(n + 1):
            xx = x + 8 + i * (w - 16) / n
            g.append(f'<circle cx="{xx:.1f}" cy="{ya}" r="1.4"/>')
            if not (hole and h0 <= xx <= h1): g.append(f'<circle cx="{xx:.1f}" cy="{ym}" r="1.4"/>')
        for fx in (0.12, 0.88):
            for j in range(1, int((ym - ya) / 6)):
                g.append(f'<circle cx="{x + fx * w:.1f}" cy="{ya + j * 6:.1f}" r="1.4"/>')
        o.append('<g fill="#64748b">' + "".join(g) + "</g>")
    return "".join(o), (h0, h1, ym, ya)


def blob(cx, cy, rx, ry, op=0.85):
    g = uid("g")
    return (f'<radialGradient id="{g}"><stop offset="0" stop-color="{INDIGO}" stop-opacity="{op}"/><stop offset="0.6" stop-color="{INDIGO}" stop-opacity="{op * 0.35}"/>'
            f'<stop offset="1" stop-color="{INDIGO}" stop-opacity="0"/></radialGradient><ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#{g})"/>')


def card(x, y, w, h, stroke=LINE, fill="#ffffff", sw=1.5):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def text(x, y, s, size=13, fill=INK, weight=400, anchor="start", italic=False):
    st = ' font-style="italic"' if italic else ""
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}"{st}>{s}</text>'


def arrow(x1, y1, x2, y2, col="#94a3b8", w=2.2, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{w}"{d} marker-end="url(#ah)"/>'


DEFS = ('<defs><marker id="ah" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M0,0 L10,5 L0,10 z" fill="#94a3b8"/></marker>'
        '<marker id="ahg" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{GREEN}"/></marker>'
        '<marker id="ahb" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{BLUE}"/></marker></defs>')


def pin(x, y, col=GREEN, s=1.0):
    return (f'<path d="M{x},{y} c{-7 * s},{-9 * s} {-11 * s},{-14 * s} {-11 * s},{-20 * s} a{11 * s},{11 * s} 0 1 1 {22 * s},0 '
            f'c0,{6 * s} {-4 * s},{11 * s} {-11 * s},{20 * s} z" fill="{col}"/><circle cx="{x}" cy="{y - 20 * s}" r="{4.2 * s}" fill="#fff"/>')


def pause(x, y, col=AMBER, s=1.0):
    return (f'<circle cx="{x}" cy="{y}" r="{13 * s}" fill="{col}"/><rect x="{x - 5 * s}" y="{y - 6 * s}" width="{3.6 * s}" height="{12 * s}" rx="1" fill="#fff"/>'
            f'<rect x="{x + 1.4 * s}" y="{y - 6 * s}" width="{3.6 * s}" height="{12 * s}" rx="1" fill="#fff"/>')


# ------------------------------------------------------------------ io.svg
def io_svg():
    W, H = 1200, 420; o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">', DEFS,
                          f'<rect width="{W}" height="{H}" rx="16" fill="#ffffff"/>']
    o.append(text(24, 36, "INPUT", 13, MUTED, 700) + text(830, 36, "OUTPUT, EVERY FRAME", 13, MUTED, 700))
    # input 1: image sequence
    o.append(card(20, 50, 400, 112))
    for k in range(3): o.append(street(36 + k * 34, 76 - k * 6 + 6, 86, 60, v=k))
    for k, lab in enumerate(("t−2", "t−1", "t")): o.append(text(79 + k * 34, 156, lab, 11, MUTED, 400, "middle"))
    o.append(text(196, 82, "Camera image sequence", 15, INK, 700) + text(196, 104, "one image per frame, compared", 13, MUTED)
             + text(196, 124, "with the map images", 13, MUTED))
    # input 2: odometry
    o.append(card(20, 174, 400, 100))
    pts = [(40, 250), (70, 240), (100, 236), (128, 222), (150, 204), (176, 196)]
    for (a, b), (c, d) in zip(pts, pts[1:]): o.append(f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" stroke="{BLUE}" stroke-width="2.4" marker-end="url(#ahb)"/>')
    o.append(f'<circle cx="40" cy="250" r="4" fill="{BLUE}"/>')
    o.append(text(196, 206, "Odometry", 15, INK, 700) + text(196, 228, "how far the robot moved since", 13, MUTED)
             + text(196, 248, "the previous frame", 13, MUTED))
    # input 3: map
    o.append(card(20, 286, 400, 118))
    mm, (h0, h1, ym, ya) = minimap(30, 296, 156, 98); o.append(mm)
    o.append(text(196, 320, "Geo-referenced image map", 15, INK, 700) + text(196, 342, "images taken at known positions", 13, MUTED)
             + text(196, 362, "has holes:", 13, MUTED) + f'<rect x="262" y="352" width="34" height="13" rx="3" fill="#fef3c7" stroke="#f59e0b" stroke-dasharray="3 2"/>'
             + text(302, 362, "unmapped areas", 13, MUTED))
    # arrows into LACUNA
    for yy in (106, 224, 345): o.append(f'<path d="M424,{yy} C470,{yy} 470,212 500,212" fill="none" stroke="#94a3b8" stroke-width="2.2" marker-end="url(#ah)"/>')
    # centre: LACUNA
    o.append(card(506, 92, 290, 240, GREEN, GREEN_BG, 2.2))
    o.append(text(651, 128, "LACUNA", 24, GREEN, 800, "middle") + text(651, 150, "open-world HMM filter", 13, "#15803d", 600, "middle"))
    gx, gy = 556, 166
    o.append(f'<rect x="{gx}" y="{gy}" width="190" height="96" rx="6" fill="#ffffff" stroke="#bbf7d0"/>')
    mm, (h0, h1, ym, ya) = minimap(gx, gy, 190, 96); o.append(mm)
    o.append(blob((h0 + h1) / 2 + 6, ym, 22, 13))
    o.append(f'<circle cx="{(h0 + h1) / 2 + 6}" cy="{ym}" r="4.5" fill="{BLUE}" stroke="#fff" stroke-width="1.5"/>')
    o.append(text(651, 284, "built on Hidden Markov Model principles", 12.5, "#334155", 400, "middle")
             + text(651, 304, "no labels needed · one setting for all maps", 12.5, "#334155", 400, "middle"))
    o.append(arrow(800, 212, 826, 212))
    # output 1: fix
    o.append(card(832, 50, 348, 112, "#bbf7d0", "#ffffff"))
    mm, (h0, h1, ym, ya) = minimap(842, 64, 120, 84, hole=False); o.append(mm)
    o.append(pin(842 + 120 * 0.78, ym - 1, GREEN, 0.9))
    o.append(text(978, 92, "Position", 15, GREEN, 700) + text(978, 114, "(x, y) on the map, reported", 13, MUTED)
             + text(978, 134, "only when the filter is confident", 13, MUTED))
    # output 2: abstain
    o.append(card(832, 174, 348, 100, "#fde68a", "#ffffff"))
    o.append(pause(870, 224, AMBER, 1.25))
    o.append(text(908, 206, "Abstain", 15, AMBER, 700) + text(908, 228, "robot is off the map or uncertain:", 13, MUTED)
             + text(908, 248, "no position is reported", 13, MUTED))
    # output 3: over a drive
    o.append(card(832, 286, 348, 118))
    o.append(text(848, 312, "Over a drive", 15, INK, 700))
    seq = "ffffffoooooooffffff"; x0, w = 848, 316 / len(seq)
    for i, c in enumerate(seq):
        o.append(f'<rect x="{x0 + i * w:.1f}" y="324" width="{w - 1.5:.1f}" height="10" rx="2" fill="{"#fbbf24" if c == "o" else "#cbd5e1"}"/>')
        o.append(f'<rect x="{x0 + i * w:.1f}" y="340" width="{w - 1.5:.1f}" height="14" rx="2" fill="{"#e2e8f0" if c == "o" else "#22c55e"}"/>')
    lg = [("#cbd5e1", "on map"), ("#fbbf24", "in a hole"), ("#22c55e", "position"), ("#e2e8f0", "abstain")]; xx = 848
    for c, lab in lg:
        o.append(f'<rect x="{xx}" y="370" width="11" height="11" rx="2" fill="{c}"/>' + text(xx + 16, 380, lab, 12, MUTED)); xx += 34 + 6.8 * len(lab)
    o.append(text(848, 398, "top: where the robot is · bottom: LACUNA's output", 11, "#94a3b8"))
    o.append("</svg>"); return "".join(o)


# ------------------------------------------------------------------ method.svg
def method_svg():
    W, H = 1200, 456; o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">', DEFS,
                          f'<rect width="{W}" height="{H}" rx="16" fill="#ffffff"/>']
    cols = [(20, "1", "Place retrieval", False), (316, "2", "Predict with odometry", True), (612, "3", "Update with evidence", True), (908, "4", "Decide", False)]
    for x, n, title, ours in cols:
        o.append(card(x, 20, 272, 356, GREEN if ours else LINE, GREEN_BG if ours else "#ffffff", 2 if ours else 1.5))
        o.append(f'<circle cx="{x + 26}" cy="{48}" r="13" fill="{GREEN if ours else "#334155"}"/>' + text(x + 26, 53, n, 14, "#fff", 700, "middle"))
        o.append(text(x + 48, 54, title, 16, INK, 700))
    for x in (296, 592, 888): o.append(arrow(x, 198, x + 16, 198))
    # 1: retrieval
    x = 20; o.append(street(x + 22, 78, 92, 64, v=1)); o.append(text(x + 68, 158, "current frame", 11.5, MUTED, 400, "middle"))
    o.append(arrow(x + 120, 110, x + 146, 110))
    bx, by = x + 152, 140; vals = [0.12, 0.10, 0.14, 0.11, 0.13, 0.95, 0.30, 0.12, 0.10, 0.42, 0.13, 0.11]
    for i, v in enumerate(vals):
        col = GREEN if v > 0.9 else ("#f59e0b" if v > 0.35 else "#cbd5e1")
        o.append(f'<rect x="{bx + i * 9}" y="{by - v * 60:.1f}" width="6.5" height="{v * 60:.1f}" rx="1.5" fill="{col}"/>')
    o.append(f'<line x1="{bx - 3}" y1="{by}" x2="{bx + 108}" y2="{by}" stroke="#94a3b8"/>')
    o.append(text(bx + 52, by + 16, "similarity to map images", 11, MUTED, 400, "middle"))
    o.append(f'<rect x="{x + 96}" y="175" width="9" height="9" rx="2" fill="{GREEN}"/>' + text(x + 110, 184, "true place", 11.5, GREEN, 600)
             + f'<rect x="{x + 180}" y="175" width="9" height="9" rx="2" fill="#f59e0b"/>' + text(x + 194, 184, "look-alike", 11.5, "#b45309", 600))
    for i, s in enumerate(["A global descriptor (e.g. NetVLAD,", "SALAD, MegaLoc) scores the current", "frame against every map image.",
                           "Look-alike places can score high too."]):
        o.append(text(x + 18, 228 + i * 20, s, 12.5, "#334155"))
    # 2: predict
    x = 316; gx, gy = x + 22, 76
    for k in (2, 1):
        o.append(f'<rect x="{gx + k * 8}" y="{gy - k * 8}" width="214" height="104" rx="6" fill="#ffffff" stroke="#bbf7d0" opacity="0.8"/>')
    o.append(f'<rect x="{gx}" y="{gy}" width="214" height="104" rx="6" fill="#ffffff" stroke="#86efac"/>')
    o.append("".join(f'<line x1="{gx + i * 10.7:.1f}" y1="{gy}" x2="{gx + i * 10.7:.1f}" y2="{gy + 104}" stroke="#f0fdf4"/>' for i in range(1, 20)))
    o.append("".join(f'<line x1="{gx}" y1="{gy + j * 10.4:.1f}" x2="{gx + 214}" y2="{gy + j * 10.4:.1f}" stroke="#f0fdf4"/>' for j in range(1, 10)))
    mm, (h0, h1, ym, ya) = minimap(gx, gy, 214, 104); o.append(mm)
    o.append(blob(h0 - 4, ym, 14, 9, 0.35))
    o.append(blob(h0 + 30, ym, 22, 13, 0.85))
    o.append(f'<path d="M{h0 - 4},{ym - 16} C{h0 + 6},{ym - 30} {h0 + 22},{ym - 30} {h0 + 30},{ym - 18}" fill="none" stroke="{BLUE}" stroke-width="2" marker-end="url(#ah)"/>')
    o.append(text(h0 + 13, ym - 32, "odometry", 11, BLUE, 600, "middle"))
    o.append(f'<circle cx="{gx + 200}" cy="{gy + 14}" r="9" fill="#fff" stroke="#64748b"/>' + text(gx + 200, gy + 18.5, "Ω", 11.5, "#334155", 400, "middle"))
    for i, s in enumerate(["The belief lives on a metric grid that", "covers mapped cells, unmapped cells and", "a far state Ω. Odometry shifts it into and",
                           "out of holes; it is never forced back onto", "the map. A filter bank self-calibrates", "odometry noise and scale online."]):
        o.append(text(x + 18, 228 + i * 20, s, 12.5, "#334155"))
    # 3: update
    x = 612
    o.append(text(x + 18, 92, "mapped cells", 12.5, INK, 700) + text(x + 112, 92, "× likelihood ratio", 12.5, "#334155"))
    o.append(text(x + 18, 116, "unmapped cells", 12.5, INK, 700) + text(x + 126, 116, "× calibrated evidence", 12.5, "#334155"))
    px, py, pw, ph = x + 30, 130, 212, 82
    o.append(f'<rect x="{px - 12}" y="{py - 6}" width="{pw + 24}" height="{ph + 36}" rx="8" fill="#ffffff" stroke="#bbf7d0"/>')

    def curve(m, s, col):
        pts = []
        for i in range(61):
            u = i / 60; v = math.exp(-0.5 * ((u - m) / s) ** 2)
            pts.append(f"{px + u * pw:.1f},{py + ph - 6 - v * (ph - 16):.1f}")
        return f'<polyline points="{" ".join(pts)}" fill="none" stroke="{col}" stroke-width="2.4"/>'
    o.append(f'<line x1="{px}" y1="{py + ph - 6}" x2="{px + pw}" y2="{py + ph - 6}" stroke="#94a3b8"/>')
    o.append(curve(0.30, 0.10, "#f59e0b") + curve(0.72, 0.10, GREEN))
    o.append(text(px + 0.30 * pw, py + 8, "f_off", 12, "#b45309", 700, "middle") + text(px + 0.72 * pw, py + 8, "f_on", 12, GREEN, 700, "middle"))
    o.append(text(px + pw / 2, py + ph + 12, "x = best similarity − median", 11, MUTED, 400, "middle"))
    o.append(text(x + 136, 262, "log f_off(x) − log f_on(x)", 13.5, INK, 700, "middle"))
    for i, s in enumerate(["f_on: best match when on the map.", "f_off: best look-alike when the true place", "is absent. Both are learned without labels",
                           "from the filter's own confident fixes."]):
        o.append(text(x + 18, 290 + i * 20, s, 12.5, "#334155"))
    # 4: decide
    x = 908
    o.append(f'<rect x="{x + 18}" y="78" width="236" height="122" rx="8" fill="#f0fdf4" stroke="#bbf7d0"/>')
    mm, (h0, h1, ym, ya) = minimap(x + 24, 84, 116, 74, hole=True); o.append(mm)
    o.append(blob(x + 24 + 116 * 0.8, ym, 8, 6, 0.95))
    o.append(text(x + 150, 112, "mass near a", 12, "#334155") + text(x + 150, 128, "mapped place", 12, "#334155") + text(x + 150, 144, "≥ 1 − ε", 12, "#334155", 700))
    o.append(pin(x + 160, 190, GREEN, 0.7) + text(x + 176, 184, "Position fix", 13.5, GREEN, 700))
    o.append(f'<rect x="{x + 18}" y="212" width="236" height="104" rx="8" fill="{AMBER_BG}" stroke="#fde68a"/>')
    mm, (h0, h1, ym, ya) = minimap(x + 24, 218, 116, 74, hole=True); o.append(mm)
    o.append(blob((h0 + h1) / 2, ym, 18, 11, 0.8))
    o.append(text(x + 150, 246, "belief is in", 12, "#334155") + text(x + 150, 262, "a hole or diffuse", 12, "#334155"))
    o.append(pause(x + 162, 290, AMBER, 0.85) + text(x + 180, 295, "Abstain", 13.5, AMBER, 700))
    o.append(text(x + 18, 346, "Confidence tiers and a self-supervised", 12.5, "#334155") + text(x + 18, 366, "conformal branch decide each frame.", 12.5, "#334155"))
    # loops at the bottom
    o.append(f'<path d="M1000,378 C1000,412 760,412 748,383" fill="none" stroke="{GREEN}" stroke-width="2" stroke-dasharray="6 4" marker-end="url(#ahg)"/>')
    o.append(text(874, 424, "confident fixes calibrate f_on, f_off", 12.5, "#15803d", 600, "middle"))
    o.append(text(874, 440, "(label-free, causal within a session)", 11.5, "#15803d", 400, "middle"))
    o.append("</svg>"); return "".join(o)


open("io.svg", "w").write(io_svg()); open("method.svg", "w").write(method_svg()); print("ok")
