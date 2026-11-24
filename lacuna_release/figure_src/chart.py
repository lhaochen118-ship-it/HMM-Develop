"""results.svg: per-environment recall, LACUNA vs the best external baseline at its per-run oracle threshold.
Numbers: HMM-Develop analysis/results/owf/s1111/e29a_board_s67_72.md (288 runs, seeds 67-72)."""
FONT = "Inter, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
OURS, BASE, INK, INK2, MUTED, GRID = "#16a34a", "#6b7fd7", "#0f172a", "#475569", "#94a3b8", "#eef2f6"
# env, LACUNA, Claxton@orc, Xu@orc, TAO@orc
ROWS = [("Oxford RobotCar", 0.943, 0.765, 0.745, 0.670), ("Nordland", 0.971, 0.448, 0.774, 0.549),
        ("Extended CMU Seasons", 0.828, 0.764, 0.581, 0.784), ("St Lucia", 0.983, 0.782, 0.839, 0.703),
        ("Boreas", 0.969, 0.689, 0.720, 0.685), ("4Seasons office loop", 0.964, 0.741, 0.649, 0.736),
        ("4Seasons old town", 0.945, 0.689, 0.673, 0.703), ("4Seasons countryside", 0.813, 0.484, 0.224, 0.374)]
NAMES = ("Claxton'24", "Xu'21", "TAO'26")
POOLED = ("All 8 environments", 0.927, 0.670, 0.651, 0.651)
W, H = 1000, 520; X0, X1, V0, V1 = 300, 830, 0.4, 1.0
X = lambda v: X0 + (v - V0) / (V1 - V0) * (X1 - X0)


def t(x, y, s, size=13, fill=INK, w=400, a="start"): return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" font-weight="{w}" text-anchor="{a}">{s}</text>'


o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
     f'<rect width="{W}" height="{H}" rx="16" fill="#ffffff"/>',
     t(24, 40, "Recall per environment", 20, INK, 700),
     t(24, 64, "In each environment, LACUNA (no labels) against the strongest of TAO'26, Claxton'24 and Xu'21,", 14, INK2),
     t(24, 84, "whose threshold is tuned on the test labels. 288 runs, the same runs for every method.", 14, INK2)]
# legend
o.append(f'<circle cx="{W - 300}" cy="35" r="6.5" fill="none" stroke="{BASE}" stroke-width="2.5"/>' + t(W - 288, 40, "best baseline", 14, INK2))
o.append(f'<circle cx="{W - 170}" cy="35" r="7" fill="{OURS}" stroke="#fff" stroke-width="2"/>' + t(W - 157, 40, "LACUNA", 14, INK2))
top, rh = 124, 38; ybot = top + rh * (len(ROWS) + 1) + 14
for v in (0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
    o.append(f'<line x1="{X(v):.1f}" y1="{top - 14}" x2="{X(v):.1f}" y2="{ybot - 8}" stroke="{GRID}" stroke-width="1"/>')
    o.append(t(X(v), ybot + 12, f"{v:.1f}", 13, MUTED, 400, "middle"))
o.append(t((X0 + X1) / 2, ybot + 34, "recall (fraction of on-map frames with a correct fix)", 13, MUTED, 400, "middle"))
o.append(t(945, top - 22, "gain", 13, MUTED, 600, "middle"))


def row(y, name, ours, b3, bold=False):
    k = max(range(3), key=lambda i: b3[i]); b = b3[k]
    o.append(t(24, y + 5, name, 15, INK, 700 if bold else 400))
    o.append(f'<line x1="{X(b):.1f}" y1="{y}" x2="{X(ours):.1f}" y2="{y}" stroke="#cbd5e1" stroke-width="2"/>')
    o.append(f'<circle cx="{X(b):.1f}" cy="{y}" r="6.5" fill="#ffffff" stroke="{BASE}" stroke-width="2.5"/>')
    o.append(f'<circle cx="{X(ours):.1f}" cy="{y}" r="7" fill="{OURS}" stroke="#ffffff" stroke-width="2"/>')
    o.append(t(X(b) - 13, y + 5, f'{b:.3f} <tspan fill="{MUTED}">{NAMES[k]}</tspan>', 14, INK2, 400, "end"))
    o.append(t(X(ours) + 13, y + 5, f"{ours:.3f}", 14, INK, 700))
    o.append(t(945, y + 5, f"+{(ours - b) * 100:.1f} pp", 15, INK, 700, "middle"))


for i, r in enumerate(ROWS): row(top + i * rh, r[0], r[1], r[2:])
yp = top + len(ROWS) * rh + 14
o.append(f'<line x1="24" y1="{yp - 19}" x2="{W - 24}" y2="{yp - 19}" stroke="#e2e8f0" stroke-width="1"/>')
row(yp, POOLED[0], POOLED[1], POOLED[2:], bold=True)
o.append("</svg>")
open("results.svg", "w").write("".join(o)); print("ok")
