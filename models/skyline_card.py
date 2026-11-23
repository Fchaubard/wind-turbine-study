import json
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Ellipse
d = json.load(open("out/skyline.json")); b, o, fr = d["base_kite only"], d["optimistic_kite only"], d["free_lift"]
INK, MUTE, ACC, GR, BG = "#1b2a33", "#6b7a83", "#e4572e", "#b9c4ca", "#f7f4ee"
f = plt.figure(figsize=(7.2, 9), facecolor=BG)
f.text(.06, .95, "Kite-Lifted Line", fontsize=27, weight="bold", color=INK)
f.text(.06, .915, f"Failed: \${b['usd']:,.0f}/MWh realistic, \${o['usd']:.0f} best case.", fontsize=14, color=MUTE)
a = f.add_axes([.04, .49, .92, .40]); a.set_xlim(-10, 110); a.set_ylim(-4, 50); a.axis("off")
a.fill_between([-10, 110], -4, 0, color="#cfe3e8")
for x in (8, 92):
    a.add_patch(Ellipse((x, 42), 25, 7, color=GR)); a.plot([x, x], [38.5, 25], color=MUTE, lw=1); a.plot([x, x + (-14 if x < 50 else 14)], [25, 0], color=MUTE, lw=1)
a.plot([8, 50, 92], [25, 21.5, 25], color=INK, lw=1.5); a.plot([8, 50, 92], [8, 5, 8], color=INK, lw=1.5)
for x in (35, 44, 53, 62):
    a.add_patch(Polygon([[x, 22], [x + 5, 22], [x + 6, 6.5], [x + 1, 6.5]], color=ACC))
a.text(50, 46, f"kites must be {2 * o['kite_m2_each'] / (o['n'] * o['h'] * o['c']):.1f}× the sail area", ha="center", fontsize=14, weight="bold", color=INK)
a.text(50, 31, "holding the line tight takes most of the lift", ha="center", fontsize=12, color=MUTE)
c = f.add_axes([.42, .12, .48, .30]); N = ["High line, free supports", "Dandelion", "Zipline Sail", "Kite line, best case", "Kite line, realistic"]; V = [round(fr["usd"]), 100, 164, round(o["usd"]), round(b["usd"])]
c.barh(N[::-1], V[::-1], color=[ACC, ACC, GR, INK, GR], height=.58); c.set_facecolor(BG); c.set_xlim(0, 1300); c.set_xticks([])
for s in c.spines.values(): s.set_visible(False)
c.tick_params(left=False, labelsize=12, colors=INK)
for i, v in enumerate(V[::-1]): c.text(v + 18, i, f"\${v:,}", va="center", fontsize=12.5, weight="bold", color=INK)
f.text(.06, .435, "Lifetime cost per MWh, 20 years", fontsize=13, weight="bold", color=INK)
f.text(.06, .07, "Height is valuable. Lifting with kites is not.", fontsize=14, weight="bold", color=INK)
f.text(.06, .037, "Simulation only. Launch, landing and storms not charged.", fontsize=12, color=MUTE)
f.savefig("skyline_summary.png", dpi=150, facecolor=BG)
