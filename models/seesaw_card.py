import json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
R = json.load(open("out/seesaw_window.json")); pick = lambda p, l, q: min((r for r in R if r["price"] == p and r["life"] == l and r["line_life"] == q), key=lambda r: r["usd"]); a_, b_ = pick(50, 5000, 5000), pick(150, 1500, 1500)
INK, MUTE, ACC, GR, BG = "#1b2a33", "#6b7a83", "#e4572e", "#aab5ba", "#f7f4ee"
f = plt.figure(figsize=(7.2, 9), facecolor=BG); f.text(.06, .95, "Kite Seesaw", fontsize=27, weight="bold", color=INK); f.text(.06, .915, rf"Beats the carousel: \${a_['usd']:.0f}/MWh at best. Dandelion \$76.", fontsize=14, color=MUTE)
a = f.add_axes([.04, .49, .92, .40]); a.set_xlim(0, 100); a.set_ylim(0, 60); a.axis("off"); a.add_patch(Rectangle((0, 0), 100, 7, color="#cfe3e8")); a.add_patch(Rectangle((9, 7), 9, 3, color=INK)); a.add_patch(plt.Circle((13.5, 12), 2.7, color=INK))
for end, col, n in (((88, 27), ACC, "pulling out"), ((47, 53), GR, "resting, hauled in")):
    a.plot([13.5, end[0]], [12, end[1]], color=INK, lw=1.2)
    for s in (.7, .8, .9, 1.):
        x, y = 13.5 + (end[0] - 13.5) * s, 12 + (end[1] - 12) * s; a.add_patch(Polygon([(x - 4, y - 1), (x - 1, y + 3), (x + 4, y + .5), (x + .5, y + .3)], color=col, ec=INK, lw=.4))
    a.text(end[0] - 8, end[1] + 4.5, n, fontsize=12, color=INK)
a.text(22, 3, "one rope, one drum, on your pad", fontsize=12, color=INK)
c = f.add_axes([.42, .14, .48, .27]); N = ["14 m Dandelion", "Seesaw, best case", "Seesaw, realistic", "Carousel"]; V = [76, round(a_["usd"]), round(b_["usd"]), 975]; c.barh(N[::-1], V[::-1], color=[GR, ACC, ACC, INK], height=.56); c.set_facecolor(BG); c.set_xlim(0, 1250); c.set_xticks([])
for s in c.spines.values(): s.set_visible(False)
c.tick_params(left=False, labelsize=12.5, colors=INK)
for i, v in enumerate(V[::-1]): c.text(v + 18, i, rf"\${v}", va="center", fontsize=13, weight="bold", color=INK)
f.text(.06, .43, "Lifetime cost per MWh, 20 years", fontsize=13, weight="bold", color=INK); f.text(.06, .075, rf"Best: {a_['pairs']} pairs, {a_['m']} kites per train, {a_['W']:.0f} W, \${a_['capex']:,.0f}", fontsize=13, weight="bold", color=INK); f.text(.06, .04, f"Flies only {a_['fly_h']:.0f} h/yr. Simulation only, launch not modeled.", fontsize=12, color=MUTE); f.savefig("seesaw_summary.png", dpi=150, facecolor=BG)
