"""Animation, bill of materials and cost estimate for the best simulated kite carousel. Prices are the model's budget estimates, not supplier quotes. Arms are drawn larger than scale."""
import json, math
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from PIL import Image
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import zoo as Z
D = json.load(open("out/carousel2.json")); B = min((r for r in D["econ"] if r["price"] == 50 and r["life"] == 5000), key=lambda r: r["usd"]); O = D["flight"][f"{B['Ra']}|{B['f']}|{B['m']}"]; VS = [3.5, 4., 5., 6.]
v = Z.WS[(Z.WS >= 3.5) & (Z.WS <= 6.)]; hrs = len(v) / len(Z.WS) * 8766 * .85; g = lambda k: np.array([O[str(x)][k] for x in VS])
ar, m = B["arms"], B["m"]; kites = ar * m * 50; line = ar * 160 * m * 12 / 16; pods = 450 * ar; items = [("Reduction gear, ring and chain", B["gear"]), ("Generator and inverter", B["elec"]), ("Kite lines", line), ("Turntable bearing", B["slew"]), ("Steering pods, one per arm", pods), ("Steel arms", B["arm_cost"]), (f"{ar * m} inflatable kites at $50", kites), ("Sensors, wiring, hardware", 240.)]; cap = sum(x[1] for x in items); assert abs(cap - B["capex"]) < 1
def cost(crash=True, price=50, life=5000):
    av = g("av") if crash else np.ones(4); Pm = g("Pf") * av * ar * .9 * .78; P = float(np.interp(v, VS, np.maximum(Pm, 0)).mean()); A = float(np.interp(v, VS, av).mean()); lam = float(np.interp(v, VS, g("lam")).mean()) * ar * (1 if crash else 0); fly = hrs * A; k = ar * m * price; c = cap - kites + k; yr = k * fly / life + .05 * lam * fly * price + line * fly / 1500 + .03 * (c - k - line); L = c + yr * 19 + .3 * (B["elec"] + pods); return dict(W=P * hrs / 8766, usd=L / (P * hrs / 1e6 * 20), life=L, build=c, per_year=yr, crashes=lam * fly)
S = dict(simulated=cost(), no_crashes=cost(False), no_crashes_150=cost(False, 150, 1500)); json.dump(dict(design=B, items=items, scenarios=S), open("out/carousel_bom.json", "w"), indent=1, default=float); print({k: {a: round(b) for a, b in x.items()} for k, x in S.items()}); print([(a, round(b)) for a, b in items], round(cap))
INK, MUTE, ACC, GR, BG, SEA = "#1b2a33", "#6b7a83", "#e4572e", "#aab5ba", "#f7f4ee", "#cfe3e8"
def pj(x, y, z): return x + .42 * y, z + .22 * y
def blend(a, b, t): return tuple((1 - t) * int(a[i:i + 2], 16) / 255 + t * int(b[i:i + 2], 16) / 255 for i in (1, 3, 5))
N = 64; fr = []; fig = plt.figure(figsize=(5.4, 5.7), dpi=100, facecolor=BG); AZ = [-.62, -.21, .21, .62]
for k in range(N):
    t = 2 * math.pi * k / N; fig.clf(); a = fig.add_axes([0, 0, 1, 1]); a.set_xlim(-24, 92); a.set_ylim(-17, 106); a.axis("off"); a.add_patch(Rectangle((-24, -17), 116, 20, color=SEA))
    for yy, o in ((-3, 0), (-9, 1.4)): a.plot(np.linspace(-24, 92, 80), yy + .5 * np.sin(np.linspace(0, 15, 80) + t + o), color="white", lw=1.3)
    for i in range(5):
        x = -20 + ((i * 24 + 24 * k / N * 3) % 110); a.annotate("", xy=(x + 8, 82 - i * 3), xytext=(x, 82 - i * 3), arrowprops=dict(arrowstyle="-|>", shrinkA=0, shrinkB=0, color=MUTE, lw=1, alpha=.45))
    a.add_patch(Polygon([pj(-7, -7, 2), pj(7, -7, 2), pj(7, 7, 2), pj(-7, 7, 2)], color="#8d979c", ec=INK)); hub = pj(0, 0, 5); tips = []
    for j in range(4):
        ph = t + j * math.pi / 2; tx, ty = 10 * math.cos(ph), 10 * math.sin(ph); tip = pj(tx, ty, 5); tips.append((tip, ph, j)); a.plot([hub[0], tip[0]], [hub[1], tip[1]], color=INK, lw=3.4, solid_capstyle="round")
    a.plot(*hub, "o", color=INK, ms=9)
    for tip, ph, j in tips:
        p = .5 + .5 * math.tanh(4 * math.cos(ph)); r = 76 + 7 * math.cos(ph); az = AZ[j] * (.45 + .55 * p) + .09 * p * math.sin(2 * t + j); el = 1.08 - .46 * p + .05 * p * math.sin(4 * t + j); e = np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)]); base = np.array([10 * math.cos(ph), 10 * math.sin(ph), 5.]); pts = [base + e * r * s for s in (.70, .80, .90, 1.)]; end = pj(*pts[-1]); a.plot([tip[0], end[0]], [tip[1], end[1]], color=MUTE, lw=.8); col = blend(GR, ACC, p)
        for q in pts:
            u, w = pj(*q); h = 3.1 + 1.5 * p; a.add_patch(Polygon([(u - h, w - .3 * h), (u - .25 * h, w + .75 * h), (u + h, w + .1 * h), (u + .15 * h, w + .05 * h)], color=col, ec=blend("#777777", "#a93518", p), lw=.7, zorder=5))
    a.text(-21, 98, "Kite Carousel", fontsize=20, weight="bold", color=INK); a.text(-21, 91.5, "orange pulls, gray rests", fontsize=11.5, color=MUTE); a.text(34, -13, "arms turn the generator on your pad", ha="center", fontsize=11, color=INK); fig.canvas.draw(); im = Image.frombuffer("RGBA", fig.canvas.get_width_height(), fig.canvas.buffer_rgba()).convert("RGB"); fr.append(im.convert("P", palette=Image.ADAPTIVE, colors=64))
    if k == 6: im.save("out/carousel_frame.png")
fr[0].save("carousel.gif", save_all=True, append_images=fr[1:], duration=85, loop=0, optimize=True)
f = plt.figure(figsize=(7.2, 9), facecolor=BG); f.text(.06, .94, "Kite Carousel BOM", fontsize=25, weight="bold", color=INK); f.text(.06, .905, rf"{ar} arms, {m} kites per arm, {S['simulated']['W']:.0f} W average", fontsize=14, color=MUTE); y = .85
for n, c in sorted(items, key=lambda x: -x[1]): f.text(.06, y, n.replace("$", r"\$"), fontsize=14, color=INK); f.text(.94, y, rf"\${c:,.0f}", ha="right", fontsize=14, weight="bold", color=INK); y -= .049
f.add_artist(plt.Line2D([.06, .94], [y + .025, y + .025], color=INK, lw=1.3)); f.text(.06, y - .012, "Build cost", fontsize=16, weight="bold", color=INK); f.text(.94, y - .012, rf"\${cap:,.0f}", ha="right", fontsize=16, weight="bold", color=INK); y -= .085; f.text(.06, y, "Lifetime cost per MWh, 20 years", fontsize=14, weight="bold", color=INK); y -= .05
for n, u in (("As simulated, with crashes", S["simulated"]["usd"]), ("If AI eliminates all crashes", S["no_crashes"]["usd"]), ("No crashes, $150 kites, 1,500 h", S["no_crashes_150"]["usd"]), ("14 m Dandelion", 76.)): f.text(.06, y, n.replace("$", r"\$"), fontsize=13.5, color=INK); f.text(.94, y, rf"\${u:,.0f}", ha="right", fontsize=14, weight="bold", color=ACC if "Dandelion" not in n else INK); y -= .043
f.text(.06, .035, "Budget estimates, simulation only. Launch and tangling not modeled.", fontsize=11, color=MUTE); f.savefig("carousel_bom.png", dpi=150, facecolor=BG)
