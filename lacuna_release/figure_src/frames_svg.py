"""frames.json -> one SVG per frame (svg/f_###.svg). Layout 1200 x 600."""
import json, base64, io, os, numpy as np
from PIL import Image

D = json.load(open("frames.json")); F = D["frames"]; N = len(F)
img = np.array(D["img"]); HOLE = D["hole"]; YM, YA = D["y_main"], D["y_alias"]; X0, X1 = D["x0"], D["x1"]
S = 550 / 400.0; MY0 = 84; YCUT = (20.0, 160.0); MH = (YCUT[1] - YCUT[0]) * S
FONT = "Inter, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
os.makedirs("svg", exist_ok=True)


def heat_uri(p):
    p = np.array(p)[int(YCUT[0] // 4):int(YCUT[1] // 4)]
    k = np.exp(-0.5 * (np.arange(-4, 5) / 1.4) ** 2); k /= k.sum()             # display-only smoothing so the belief is visible
    p = np.apply_along_axis(lambda v: np.convolve(v, k, "same"), 1, p); p = np.apply_along_axis(lambda v: np.convolve(v, k, "same"), 0, p)
    a = np.zeros_like(p)
    if p.max() > 0: a = np.clip((p / p.max()) ** 0.6, 0, 1); a[a < 0.04] = 0
    rgba = np.zeros(p.shape + (4,), np.uint8); rgba[..., 0], rgba[..., 1], rgba[..., 2] = 79, 70, 229
    rgba[..., 3] = (a * 215).astype(np.uint8)
    im = Image.fromarray(rgba, "RGBA").resize((550, int(MH)), Image.BILINEAR)
    b = io.BytesIO(); im.save(b, "PNG"); return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


def panel(px, name, t, title, sub, ours):
    X = lambda m: px + 10 + m * S; Y = lambda m: MY0 + (m - YCUT[0]) * S
    f = F[t]; r = f[name]; xr, yr = X(f["x"]), Y(f["y"])
    o = [f'<rect x="{px}" y="72" width="570" height="228" rx="12" fill="#fff" stroke="{"#16a34a" if ours else "#e2e8f0"}" stroke-width="{2 if ours else 1.5}"/>',
         f'<text x="{px + 4}" y="40" font-size="19" font-weight="700" fill="#0f172a">{title}</text>',
         f'<text x="{px + 4}" y="61" font-size="13" fill="#64748b">{sub}</text>']
    road = 'stroke="#e2e8f0" stroke-width="10" stroke-linecap="round"'
    o += [f'<line x1="{X(X0 - 4)}" y1="{Y(YM)}" x2="{X(X1 + 4)}" y2="{Y(YM)}" {road}/>',
          f'<line x1="{X(X0 - 4)}" y1="{Y(YA)}" x2="{X(X1 + 4)}" y2="{Y(YA)}" {road}/>']
    for xc in D["x_cross"]: o.append(f'<line x1="{X(xc)}" y1="{Y(YA)}" x2="{X(xc)}" y2="{Y(YM)}" {road}/>')
    o.append(f'<rect x="{X(HOLE[0]) - 5}" y="{Y(YM) - 24}" width="{(HOLE[1] - HOLE[0]) * S + 10}" height="48" rx="8" fill="#fef3c7" '
             f'stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="6 4"/>')
    o.append(f'<text x="{X((HOLE[0] + HOLE[1]) / 2)}" y="{Y(YM) + 19}" font-size="11.5" fill="#b45309" text-anchor="middle">unmapped area</text>')
    o.append(f'<text x="{X(X0)}" y="{Y(YA) - 12}" font-size="11.5" fill="#64748b">look-alike street (mapped)</text>')
    o.append(f'<image href="{heat_uri(r["belief"])}" x="{px + 10}" y="{MY0}" width="550" height="{MH:.0f}"/>')
    o.append('<g fill="#64748b">' + "".join(f'<circle cx="{X(a):.1f}" cy="{Y(b):.1f}" r="1.5"/>' for a, b, _ in img) + "</g>")
    o.append(f'<line x1="{X(X0)}" y1="{yr}" x2="{xr}" y2="{yr}" stroke="#2563eb" stroke-width="3" stroke-opacity="0.55" stroke-linecap="round"/>')
    o.append(f'<circle cx="{xr}" cy="{yr}" r="6.5" fill="#2563eb" stroke="#fff" stroke-width="2"/>'
             f'<path d="M{xr + 13},{yr} L{xr + 7},{yr - 4.5} L{xr + 7},{yr + 4.5} z" fill="#2563eb"/>')
    if r["fix"] is not None:
        fx, fy = X(r["fix"][0]), Y(r["fix"][1])
        if r["ok"]:
            o.append(f'<circle cx="{fx}" cy="{fy}" r="12" fill="none" stroke="#16a34a" stroke-width="2.5"/>')
        else:
            o.append(f'<line x1="{xr}" y1="{yr}" x2="{fx}" y2="{fy}" stroke="#dc2626" stroke-width="1.5" stroke-dasharray="4 3"/>')
            o.append(f'<circle cx="{fx}" cy="{fy}" r="12" fill="#fee2e2" fill-opacity="0.6" stroke="#dc2626" stroke-width="2.5"/>'
                     f'<path d="M{fx - 5},{fy - 5} L{fx + 5},{fy + 5} M{fx + 5},{fy - 5} L{fx - 5},{fy + 5}" stroke="#dc2626" stroke-width="2.5" stroke-linecap="round"/>')
            o.append(f'<text x="{fx + 17}" y="{fy - 10}" font-size="12.5" font-weight="700" fill="#dc2626">false fix</text>')
    # status pill
    if r["fix"] is not None and r["ok"]: txt, bg, fg = "✓  Correct position fix", "#dcfce7", "#15803d"
    elif r["fix"] is not None: txt, bg, fg = f"✗  False fix, {r['err']:.0f} m from the robot", "#fee2e2", "#b91c1c"
    elif f["off"]: txt, bg, fg = "Abstains: robot is off the map", "#fef3c7", "#b45309"
    else: txt, bg, fg = "Abstains", "#f1f5f9", "#475569"
    pause = r["fix"] is None
    o.append(f'<rect x="{px}" y="312" width="330" height="32" rx="16" fill="{bg}"/>')
    if pause:
        o.append(f'<rect x="{px + 16}" y="322" width="4" height="12" rx="1" fill="{fg}"/><rect x="{px + 23}" y="322" width="4" height="12" rx="1" fill="{fg}"/>'
                 f'<text x="{px + 35}" y="333" font-size="14" font-weight="600" fill="{fg}">{txt}</text>')
    else:
        o.append(f'<text x="{px + 16}" y="333" font-size="14" font-weight="600" fill="{fg}">{txt}</text>')
    nbad = sum(1 for g in F[:t + 1] if g[name]["ok"] is False)
    o.append(f'<text x="{px + 568}" y="333" font-size="13" text-anchor="end" fill="{"#b91c1c" if nbad else "#475569"}">'
             f'false fixes so far: <tspan font-weight="700">{nbad}</tspan></text>')
    return o


def timeline(t):
    x0, x1 = 160, 1180; w = (x1 - x0) / N; o = []
    rows = [(384, "Robot on the map?", None), (410, "Closed-world filter", "cw"), (436, "LACUNA (ours)", "ow")]
    for y, lab, name in rows:
        o.append(f'<text x="{x0 - 10}" y="{y + 11}" font-size="12.5" fill="#334155" text-anchor="end" font-weight="{700 if name == "ow" else 400}">{lab}</text>')
        o.append(f'<rect x="{x0}" y="{y}" width="{x1 - x0}" height="15" rx="3" fill="#f8fafc" stroke="#e2e8f0"/>')
        for i in range(N if name is None else t + 1):
            g = F[i]
            if name is None: c = "#fbbf24" if g["off"] else "#cbd5e1"
            else:
                r = g[name]; c = "#e2e8f0" if r["fix"] is None else ("#22c55e" if r["ok"] else "#ef4444")
            o.append(f'<rect x="{x0 + i * w:.2f}" y="{y + 1.5}" width="{w + 0.3:.2f}" height="12" fill="{c}"/>')
    cx = x0 + (t + 0.5) * w
    o.append(f'<line x1="{cx:.1f}" y1="377" x2="{cx:.1f}" y2="458" stroke="#0f172a" stroke-width="1.5"/>')
    lg = [("#cbd5e1", "on map"), ("#fbbf24", "off map (hole)"), ("#22c55e", "correct fix"), ("#ef4444", "false fix"), ("#e2e8f0", "abstain")]
    xx = x0
    for c, lab in lg:
        o.append(f'<rect x="{xx}" y="473" width="12" height="12" rx="2" fill="{c}"/><text x="{xx + 18}" y="484" font-size="12" fill="#475569">{lab}</text>')
        xx += 30 + 7.2 * len(lab)
    o.append(f'<rect x="{xx + 6}" y="472" width="26" height="14" rx="3" fill="#4f46e5" fill-opacity="0.55"/>'
             f'<text x="{xx + 38}" y="484" font-size="12" fill="#475569">belief of the filter</text>')
    return o


for t in range(N):
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="528" viewBox="0 0 1200 528" font-family="{FONT}">',
             '<rect width="1200" height="528" fill="#ffffff"/>']
    parts += panel(20, "cw", t, "Closed-world filter", "belief restricted to mapped places", False)
    parts += panel(610, "ow", t, "LACUNA (ours)", "belief over mapped and unmapped space", True)
    parts += timeline(t)
    parts.append(f'<text x="20" y="516" font-size="11.5" fill="#94a3b8">Illustrative simulation on a synthetic map: the same filter with and without unmapped cells.</text>')
    parts.append("</svg>")
    open(f"svg/f_{t:03d}.svg", "w").write("".join(parts))
print(N, "frames")
